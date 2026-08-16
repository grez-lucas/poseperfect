"""PROTOTYPE - throwaway. Wayfinder ticket #9: does the instrument work?

Ticket #9 replaces annotated ground truth with coloured tape, because the real
subject's photographs have no annotation. That swap is the whole methodological
bet of this ticket, and it is not self-evidently sound: if the colour
calibration, the blob finder, the wrist-versus-ankle assignment or the
nearest-keypoint rule is wrong, every chirality number produced downstream is an
artefact, and NOTHING in the real capture set could reveal it - there is no
second opinion to check against, and map constraint 2 forbids the eye.

So the instrument is validated where a second opinion DOES exist. This paints
synthetic tape onto ticket #18's COCO cohort at the annotated wrist and ankle
positions, runs the marker-based chirality test over it, and compares the answer
against #18's ground-truth-based test on the identical frames and the identical
predictions.

The test that matters is DISAGREEMENT, and it needs positives to have any power.
RTMPose-m swaps on roughly 1% of rear COCO instances, so waiting for it to fail
would put a handful of positives against thousands of negatives and an
instrument that answered CORRECT unconditionally would score about 99%.

So the positives are MANUFACTURED. Every instance is scored twice: once on the
real prediction, and once on the same prediction with its left and right labels
deliberately transposed - which is precisely the failure the instrument exists
to catch, injected at a known 100% rate. Three numbers come out, and they are
reported separately because they fail in different directions:

  false alarm rate  on real predictions, how often the tape cries swap when the
                    annotation says there was none. This is the number that
                    would drown a true 1% rear rate.
  injected recall   on label-transposed predictions, how often the tape catches
                    a swap it is guaranteed to be looking at.
  coverage          how often the tape yields any verdict at all. An instrument
                    with perfect recall over 20% of frames is not an instrument.

    python synthetic_check.py --limit 120

Run:  ./run.sh
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import sys
from collections import Counter

import cv2
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
EXPS = os.path.dirname(HERE)
REARVIEW = os.path.join(EXPS, "rear-view")
sys.path.insert(0, REARVIEW)

from cohort import build_cohort, BODY_PAIRS, IDX                   # noqa: E402
from run_experiment import (make_crop, gt_arrays, chirality,       # noqa: E402
                            MIRROR)

import markers as mk                                               # noqa: E402

DEFAULT_ONNX = os.path.expanduser(
    "~/.cache/poseperfect-checkpoint-swap/onnx/coco/end2end.onnx")

# BGR. Chosen far apart in hue and both far from skin, floor and denim, which is
# exactly the constraint the real tape has to satisfy. `_check_separable` in
# markers.py enforces it rather than trusting it.
TAPE_BGR = {"L": (60, 220, 40), "R": (200, 40, 220)}    # green, magenta


def paint(img, inst, gxy, gv, radius_frac=0.030):
    """Synthetic tape at the annotated wrist and ankle, where visible.

    Radius scales with the instance so a distant person gets small tape, as
    real tape would. Only v == 2 keypoints are painted: an occluded joint has no
    tape on it in the real capture set either.
    """
    r = max(3, int(round(radius_frac * np.sqrt(inst.area))))
    out = img.copy()
    painted = []
    for side, (w, a) in (("L", (IDX["left_wrist"], IDX["left_ankle"])),
                         ("R", (IDX["right_wrist"], IDX["right_ankle"]))):
        for joint, i in (("wrist", w), ("ankle", a)):
            if gv[i] != 2:
                continue
            c = tuple(int(v) for v in np.round(gxy[i]))
            cv2.circle(out, c, r, TAPE_BGR[side], -1)
            painted.append((side, joint, i))
    return out, painted, r


def calib_frames(tmp):
    """Two solid-colour frames, so calibration runs the real code path."""
    paths = {}
    for side, bgr in TAPE_BGR.items():
        p = os.path.join(tmp, f"cal_{side}.png")
        cv2.imwrite(p, np.full((256, 256, 3), bgr, np.uint8))
        paths[side] = p
    return paths


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", default=os.path.expanduser(
        "~/.cache/poseperfect-rearview/data"))
    ap.add_argument("--onnx", default=DEFAULT_ONNX)
    ap.add_argument("--out", default=os.path.join(HERE, "results"))
    ap.add_argument("--limit", type=int, default=120,
                    help="per orientation bucket")
    ap.add_argument("--decisive", type=float, default=None,
                    help="override markers.DECISIVE_TORSO_FRAC, for calibrating "
                         "it ON COCO. Never set this from the real captures.")
    ap.add_argument("--tag", default="")
    args = ap.parse_args()
    if args.decisive is not None:
        mk.DECISIVE_TORSO_FRAC = args.decisive
    os.makedirs(args.out, exist_ok=True)
    tmp = os.path.join(args.out, "_synthetic")
    os.makedirs(tmp, exist_ok=True)

    calib = mk.calibrate(calib_frames(tmp))
    print("calibrated:", json.dumps({k: round(v["hue"], 1)
                                     for k, v in calib.items()}))

    ann = os.path.join(args.data, "annotations", "person_keypoints_val2017.json")
    imdir = os.path.join(args.data, "val2017")
    cohort = build_cohort(ann)
    per, keep = Counter(), []
    for i in cohort:
        if per[i.orientation] < args.limit:
            per[i.orientation] += 1
            keep.append(i)
    cohort = keep
    print(f"cohort: {len(cohort)} instances {dict(per)}", flush=True)

    from rtmlib import RTMPose
    pose = RTMPose(onnx_model=args.onnx, model_input_size=(192, 256),
                   backend="onnxruntime", device="cpu")

    rows = []
    for inst in cohort:
        img = cv2.imread(os.path.join(imdir, inst.file_name))
        if img is None:
            continue
        gxy, gv = gt_arrays(inst)
        painted_img, painted, r = paint(img, inst, gxy, gv)
        if not painted:
            continue
        crop, ox, oy, box = make_crop(
            cv2.cvtColor(painted_img, cv2.COLOR_BGR2RGB), inst.bbox)
        crop_bgr = cv2.cvtColor(crop, cv2.COLOR_RGB2BGR)

        gt_box = [box[0], box[1], box[0] + box[2], box[1] + box[3]]
        kps_l, _ = pose(crop, bboxes=[[float(v) for v in gt_box]])
        kps = np.asarray(kps_l[0], np.float64) + np.array([ox, oy])

        # #18's verdict, from the annotation.
        d_id, d_sw, n_ch = chirality(kps, gxy, gv, inst.area, BODY_PAIRS)
        if not np.isfinite(d_sw) or n_ch < 2:
            continue
        gt_swapped = bool(d_sw < d_id)

        # #9's verdict, from the tape. Markers are found in crop coordinates,
        # so the prediction is put back into crop space to match. The GT box is
        # passed as the person box for the same reason the real sweep passes the
        # detector's: it resolves a lone marker to wrist or ankle.
        found = mk.find(crop_bgr, calib, person_box=gt_box)
        kps_crop = kps - np.array([ox, oy])
        sh = (kps_crop[IDX["left_shoulder"]] + kps_crop[IDX["right_shoulder"]]) / 2
        hp = (kps_crop[IDX["left_hip"]] + kps_crop[IDX["right_hip"]]) / 2
        torso = float(np.linalg.norm(sh - hp))
        if torso <= 0:
            continue
        scored = mk.score_chirality(found, kps_crop, torso)
        verdict = mk.frame_verdict(scored)

        # The injected positive: the identical prediction with left and right
        # transposed. The instrument MUST call this swapped.
        inj = mk.score_chirality(found, kps_crop[MIRROR], torso)
        inj_verdict = mk.frame_verdict(inj)

        rows.append({
            "ann_id": inst.ann_id, "orientation": inst.orientation,
            "n_painted": len(painted), "n_found": len(found),
            "tape_verdict": verdict, "injected_verdict": inj_verdict,
            "gt_swapped": int(gt_swapped),
            "n_marker_scored": sum(1 for s in scored
                                   if s["verdict"] in ("CORRECT", "SWAPPED")),
            "n_unassigned": sum(1 for s in scored
                                if s["verdict"] == "UNASSIGNED"),
            "n_ambiguous": sum(1 for s in scored if s["verdict"] == "AMBIGUOUS"),
            "n_gross_miss": sum(1 for s in scored
                                if s["verdict"] == "GROSS_MISS"),
        })

    path = os.path.join(args.out, f"synthetic_check{args.tag}.csv")
    with open(path, "w", newline="") as f:
        wr = csv.DictWriter(f, fieldnames=list(rows[0]))
        wr.writeheader()
        wr.writerows(rows)

    def stats(sel, label):
        usable = [r for r in sel if r["tape_verdict"] in
                  ("CORRECT", "SWAPPED", "INCONSISTENT")]
        # False alarms are counted only where the annotation says there was no
        # swap, so a genuine RTMPose failure is not scored against the tape.
        clean = [r for r in usable if not r["gt_swapped"]]
        fa = [r for r in clean if r["tape_verdict"] != "CORRECT"]
        inj_usable = [r for r in sel if r["injected_verdict"] != "NO_SIGNAL"]
        caught = [r for r in inj_usable if r["injected_verdict"] != "CORRECT"]
        return {
            "label": label, "instances": len(sel),
            "coverage": (len(usable) / len(sel)) if sel else None,
            "no_marker_signal": len(sel) - len(usable),
            "false_alarms": len(fa),
            "false_alarm_rate": (len(fa) / len(clean)) if clean else None,
            "injected_n": len(inj_usable),
            "injected_recall": ((len(caught) / len(inj_usable))
                                if inj_usable else None),
            "gt_swapped_present": sum(r["gt_swapped"] for r in sel),
        }

    summary = {
        "decisive_torso_frac": mk.DECISIVE_TORSO_FRAC,
        "wrist_ankle_split": mk.WRIST_ANKLE_SPLIT,
        "overall": stats(rows, "ALL"),
        "by_orientation": [stats([r for r in rows if r["orientation"] == o], o)
                           for o in ("FRONT", "OBLIQUE", "PROFILE", "REAR")],
        "marker_buckets": {
            "unassigned": sum(r["n_unassigned"] for r in rows),
            "ambiguous": sum(r["n_ambiguous"] for r in rows),
            "gross_miss": sum(r["n_gross_miss"] for r in rows),
            "scored": sum(r["n_marker_scored"] for r in rows),
        },
    }
    with open(os.path.join(args.out, f"synthetic_check{args.tag}.json"), "w") as f:
        json.dump(summary, f, indent=2)
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
