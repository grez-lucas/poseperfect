"""PROTOTYPE - throwaway. Wayfinder ticket #9: RTMPose on the real subject.

TWO questions #18, #19 and #20 could not answer, both requiring this subject and
this room:

  1. Does RTMPose-m survive a heavily muscled, minimally clothed athlete? COCO
     is clothed people in everyday scenes. Nobody has measured this population,
     and the direction of the effect is unknown.
  2. What is the noise floor? Tickets #11 and #12 both depend on it, and if a
     genuine posing correction moves the landmarks less than the jitter does,
     the metric measures noise and must be reported as such.

Deliberately NOT re-run here, because #18, #19 and #20 already settled them and
re-deriving them would spend captures for nothing: positional error against
ground truth (tolerable, architecture-independent, corrected OKS drop 0.087 vs
0.078), the deployable rear swap rate behind a real detector (1.2% vs 1.0% on
ground-truth boxes, p = 0.85), and engine confidence as a gate (AUC 0.53-0.56).

WHAT DIFFERS FROM THE THREE EARLIER SWEEPS, and it is not incidental:

  - There is no ground truth. Chirality comes from coloured tape on four limbs
    (`markers.py`); everything COCO-annotation-shaped is simply absent.
  - The detector runs on the WHOLE PHONE FRAME. #18 and #19 fed it a 1.25x
    padded crop around an annotated box, which stands in for a frame-fit gated
    capture. Here the frame is the real input, so a detection failure is a real
    detection failure.
  - Nothing is scored against an absolute reference. The noise floor is a
    dispersion within a group of the athlete's own frames, which is exactly the
    self-referential shape decision 6 commits the product to.

Discipline carried forward unchanged: IMAGE mode only, no score threshold at
record time, and no overlay is rendered anywhere by anything in this directory.

Run:  ./run.sh
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import sys
import time

import cv2
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
EXPS = os.path.dirname(HERE)
DETECTOR = os.path.join(EXPS, "person-detector")
REARVIEW = os.path.join(EXPS, "rear-view")

sys.path.insert(0, DETECTOR)
sys.path.insert(0, REARVIEW)
import detectors                                                   # noqa: E402
from cohort import COCO_KP_NAMES, IDX                              # noqa: E402

import markers as mk                                               # noqa: E402
import shotplan                                                    # noqa: E402

# The checkpoint ticket #20 chose. COCO-supervised; AI Challenger appears only
# in backbone pretraining. #20's mitigation for the residual licensing risk is
# that the checkpoint stays a one-line configuration and never an assumption
# baked into the pipeline, so it is a flag here and not a constant inline.
DEFAULT_ONNX = os.path.expanduser(
    "~/.cache/poseperfect-checkpoint-swap/onnx/coco/end2end.onnx")

FLOOR_SCALE_CM = 100.0    # the two floor marks in the CAL-S frame, 1.00 m apart


def torso_length(kps):
    """Shoulder-midpoint to hip-midpoint, in pixels.

    The scale-free denominator. COCO's sqrt(segmentation area), which #18 and
    #19 normalised by, does not exist without an annotation - and a bounding-box
    height would change between a quarter turn and a double biceps purely
    because the arms went up, which would make the noise floor look like it
    varied by pose when only the denominator moved.
    """
    sh = (kps[IDX["left_shoulder"]] + kps[IDX["right_shoulder"]]) / 2.0
    hp = (kps[IDX["left_hip"]] + kps[IDX["right_hip"]]) / 2.0
    return float(np.linalg.norm(sh - hp))


def scale_from_cal(path, calib):
    """Pixels per centimetre, from two floor marks a known 1.00 m apart.

    Lets the noise floor be quoted in centimetres, which is the only unit in
    which the pre-registered threshold ("a 5 cm limb displacement") means
    anything. The marks sit on the athlete's standing line and run left-to-right
    across the frame, so they are at his depth and the conversion holds for him
    rather than for the floor in general.
    """
    img = cv2.imread(path)
    if img is None:
        return None
    found = mk._blobs(img, calib["L"],
                      mk.MIN_BLOB_FRAC * img.shape[0] * img.shape[1])
    found = sorted(found, key=lambda d: -d["area"])[:2]
    if len(found) != 2:
        print(f"!! scale frame {os.path.basename(path)}: found {len(found)} "
              f"floor marks, expected 2. Distances stay in pixels.")
        return None
    px = float(np.linalg.norm(found[0]["xy"] - found[1]["xy"]))
    return px / FLOOR_SCALE_CM


def contains(box, xy, pad=0.0):
    x0, y0, x1, y1 = box
    w, h = x1 - x0, y1 - y0
    return (x0 - pad * w <= xy[0] <= x1 + pad * w and
            y0 - pad * h <= xy[1] <= y1 + pad * h)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--photos", required=True)
    ap.add_argument("--shotlog", default=os.path.join(HERE, "results", "shotlog.csv"))
    ap.add_argument("--onnx", default=DEFAULT_ONNX)
    ap.add_argument("--ckpts", default=os.path.expanduser(
        "~/.cache/poseperfect-detector/checkpoints"))
    ap.add_argument("--cfgs", default=os.path.expanduser(
        "~/.cache/poseperfect-detector/configs"))
    ap.add_argument("--out", default=os.path.join(HERE, "results"))
    ap.add_argument("--require-confirmed", action="store_true", default=True)
    args = ap.parse_args()
    os.makedirs(args.out, exist_ok=True)

    with open(args.shotlog, newline="") as f:
        log = list(csv.DictReader(f))

    cal = {r["pose"]: os.path.join(args.photos, r["file"])
           for r in log if r["condition"] == "calibration"}
    for need in ("CAL-L", "CAL-R"):
        if need not in cal:
            raise SystemExit(f"shotlog has no {need} frame - run ingest.py first")
    calib = mk.calibrate({"L": cal["CAL-L"], "R": cal["CAL-R"]})
    mk.save(calib, os.path.join(args.out, "marker_calibration.json"))
    print("tape calibrated:", json.dumps(
        {k: round(v["hue"], 1) for k, v in calib.items()}))

    px_per_cm = scale_from_cal(cal["CAL-S"], calib) if "CAL-S" in cal else None
    print(f"scale: {px_per_cm:.3f} px/cm" if px_per_cm else "scale: unavailable")

    work = [r for r in log if r["condition"] != "calibration"
            and (not args.require_confirmed or r["confirmed"].strip().lower() == "y")]
    if not work:
        raise SystemExit("no confirmed rows in the shot log - see ingest.py's "
                         "closing instructions")
    print(f"{len(work)} confirmed frames", flush=True)

    from rtmlib import RTMPose
    pose = RTMPose(onnx_model=args.onnx, model_input_size=(192, 256),
                   backend="onnxruntime", device="cpu")
    det = detectors.build("rtmdet_ins_tiny", args.ckpts, args.cfgs)
    print("detector:", det.name, "| pose:", os.path.basename(args.onnx), flush=True)

    frame_fields = [
        "n", "file", "block", "pose", "orientation", "camera", "condition",
        "rep", "facing", "box_source", "n_person_det", "top1_score",
        "top1_is_subject", "subject_box_rank", "n_markers", "n_markers_scored",
        "torso_px", "frame_verdict",
        "wristL", "wristR", "ankleL", "ankleR", "pose_conf_mean",
    ]
    kp_fields = ["n", "file", "box_source", "kp", "name", "x", "y", "score"]

    fpath = os.path.join(args.out, "per_frame.csv")
    kpath = os.path.join(args.out, "keypoints.csv")
    t0 = time.time()

    with open(fpath, "w", newline="") as ff, open(kpath, "w", newline="") as kf:
        fw = csv.DictWriter(ff, fieldnames=frame_fields)
        fw.writeheader()
        kw = csv.DictWriter(kf, fieldnames=kp_fields)
        kw.writeheader()

        for i, r in enumerate(work):
            path = os.path.join(args.photos, r["file"])
            img = cv2.imread(path)
            if img is None:
                print("unreadable:", r["file"])
                continue

            orientation = shotplan.POSE_BY_CODE.get(r["pose"], ("", "", False))[1]

            try:
                dets = det.detect(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
            except Exception as exc:
                print("detect error", r["file"], exc, flush=True)
                dets = []

            # Which detection is the athlete.
            #
            # For every block but F there is only one person in the room, so the
            # box containing the markers is his and the tape settles it with no
            # human input. Block F cannot work that way: A REFLECTION WEARS THE
            # SAME TAPE ON THE SAME LIMBS, so marker containment cannot separate
            # a man from his mirror image, and no geometric rule reliably can
            # either. That one fact is supplied by Lucas in the shot log's
            # `subject_hint` column - the horizontal position of himself, as a
            # fraction of frame width, on four frames.
            #
            # Recognising yourself rather than your reflection in your own
            # photograph is a fact about the photograph, which is the same
            # licence the tape operates under. It is not a judgement about the
            # model's output, so map constraint 2 is untouched.
            hint = (r.get("subject_hint") or "").strip()
            subject_rank = -1
            if hint and dets:
                want = float(hint) * img.shape[1]
                subject_rank = int(np.argmin(
                    [abs((d["box"][0] + d["box"][2]) / 2.0 - want) for d in dets]))

            # Detection first, because a lone visible marker is resolved to
            # wrist or ankle against the person's own box. The box carries no
            # left/right information, so this decides WHICH JOINT the tape is
            # on and never which side - the side is the tape's colour, and that
            # is what keeps the ground truth independent of the model under test.
            sub_box = dets[subject_rank]["box"] if subject_rank >= 0 else None
            found = mk.find(img, calib,
                            person_box=(sub_box if sub_box is not None
                                        else (dets[0]["box"] if dets else None)),
                            restrict_box=sub_box)

            # Where no hint was given, the tape settles it: the subject box is
            # the detection containing the most markers. This is what turns
            # #19's 83.7% top-1 caveat into a measurement rather than an
            # inherited unknown.
            if subject_rank < 0 and dets and found:
                counts = [sum(1 for m in found if contains(d["box"], m["xy"]))
                          for d in dets]
                if max(counts) > 0:
                    subject_rank = int(np.argmax(counts))

            arms = []
            if dets:
                arms.append(("top1", dets[0]["box"]))
                if subject_rank > 0:
                    arms.append(("subject_box", dets[subject_rank]["box"]))

            base = {
                "n": r["n"], "file": r["file"], "block": r["block"],
                "pose": r["pose"], "orientation": orientation,
                "camera": r["camera"], "condition": r["condition"],
                "rep": r["rep"], "facing": r.get("facing", ""),
                "n_person_det": len(dets),
                "top1_score": (f"{dets[0]['score']:.4f}" if dets else ""),
                "top1_is_subject": (1 if subject_rank == 0 else
                                    (0 if subject_rank > 0 else "")),
                "subject_box_rank": subject_rank,
                "n_markers": len(found),
            }

            if not arms:
                # No detection at all. Recorded as its own outcome, never as a
                # chirality result - #18 found this failure mode dominated for
                # BlazePose at 30% of rear captures, and it is the one failure
                # that is trivially detectable at runtime.
                fw.writerow(dict(base, box_source="none", n_markers_scored=0,
                                 torso_px="", frame_verdict="NO_DETECTION",
                                 wristL="", wristR="", ankleL="", ankleR="",
                                 pose_conf_mean=""))
                continue

            for tag, box in arms:
                kps_l, sc_l = pose(cv2.cvtColor(img, cv2.COLOR_BGR2RGB),
                                   bboxes=[[float(box[0]), float(box[1]),
                                            float(box[2]), float(box[3])]])
                kps = np.asarray(kps_l[0], np.float64)
                conf = np.asarray(sc_l[0], np.float64)
                tp = torso_length(kps)
                rows = mk.score_chirality(found, kps, tp) if tp > 0 else []
                by = {f"{m['joint']}{m['side']}": m["verdict"] for m in rows
                      if m["joint"] != "unassigned"}

                fw.writerow(dict(
                    base, box_source=tag,
                    n_markers_scored=sum(1 for m in rows
                                         if m["verdict"] in ("CORRECT", "SWAPPED")),
                    torso_px=f"{tp:.2f}",
                    frame_verdict=mk.frame_verdict(rows),
                    wristL=by.get("wristL", ""), wristR=by.get("wristR", ""),
                    ankleL=by.get("ankleL", ""), ankleR=by.get("ankleR", ""),
                    pose_conf_mean=f"{float(np.mean(conf)):.4f}"))

                for j in range(17):
                    kw.writerow({"n": r["n"], "file": r["file"],
                                 "box_source": tag, "kp": j,
                                 "name": COCO_KP_NAMES[j],
                                 "x": f"{kps[j, 0]:.3f}", "y": f"{kps[j, 1]:.3f}",
                                 "score": f"{conf[j]:.4f}"})

            if (i + 1) % 20 == 0:
                print(f"{i + 1}/{len(work)}  {time.time() - t0:.0f}s", flush=True)

    meta = {
        "ticket": 9,
        "subject": "single real athlete, private room - NOT a public dataset",
        "photographs_committed": False,
        "photograph_manifest": "results/shotlog.csv (sha256 per file)",
        "mode": "IMAGE / static single-image inference only",
        "score_threshold_applied_at_record_time": None,
        "chirality_ground_truth": "physical tape markers, four limbs, two colours",
        "detector": {"name": det.name,
                     "checkpoint": os.path.basename(det.checkpoint),
                     "checkpoint_bytes": det.checkpoint_bytes,
                     "input": "whole phone frame, NOT a padded crop"},
        "pose_onnx": args.onnx,
        "pose_onnx_bytes": os.path.getsize(args.onnx),
        "px_per_cm": px_per_cm,
        "frames": len(work),
        "seconds": round(time.time() - t0, 1),
    }
    with open(os.path.join(args.out, "run_meta.json"), "w") as f:
        json.dump(meta, f, indent=2)
    print(json.dumps(meta, indent=2))


if __name__ == "__main__":
    main()
