"""PROTOTYPE - throwaway. Wayfinder ticket #20: price the checkpoint swap.

Reuses ticket #18's cohort, crop construction and chirality scoring verbatim
(`experiments/rear-view/`), and ticket #19's detector adapter and pose scoring
verbatim (`experiments/person-detector/`), rather than rebuilding any of them.
That is what makes these numbers directly comparable to the 1.0% (#18,
ground-truth boxes) and 1.2% (#19, RTMDet-Ins-tiny boxes) rear chirality swap
rates the two earlier tickets published.

ONE question: what does the rear chirality swap rate become if RTMPose-m's
`body7` weights are replaced by `aic-coco`?

`aic-coco` drops MPII, whose download page forbids commercial use, and it
publishes a HIGHER COCO AP (75.8 vs 74.9). But COCO AP is a whole-dataset
average over mostly front-facing people, and #18 exists precisely because that
average hides the rear view. Nobody has measured the swap candidate on rear
views. This does.

THREE POSE ARMS, because `aic-coco` ships no official ONNX and a self-exported
graph is not automatically the same thing as the published one:

  body7_official  the official ONNX bundle from download.openmmlab.com, i.e.
                  the exact graph #18 and #19 ran. Anchors this sweep to theirs.
  body7_self      the same weights, exported here by MMDeploy. THE CONTROL.
  aic_coco_self   the swap candidate, exported here by MMDeploy.

If body7_self does not reproduce body7_official, then any difference in
aic_coco_self is an export artefact and this experiment reports nothing about
the checkpoint. That check is run first and stated in the summary.

TWO BOX SOURCES, so both earlier tickets' conditions are reproduced:

  gt_box           COCO's annotated box. #18's condition.
  rtmdet_ins_tiny  the detector #19 chose. #19's condition, and the deployable
                   one. The detector runs ONCE per instance; all three pose
                   arms are then run on the identical box, so the arms differ
                   only in their weights.

Discipline carried over from #18 and #19, and from the map's constraints:

  - IMAGE mode / static single-image inference only.
  - Nothing is validated by eye. No overlay is rendered anywhere.
  - NO SCORE THRESHOLD is applied when recording.

Run:  ./run.sh
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import sys
import time

import cv2
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
EXPS = os.path.dirname(HERE)
REARVIEW = os.path.join(EXPS, "rear-view")
DETECTOR = os.path.join(EXPS, "person-detector")

# Ticket #18's cohort, orientation proxy, crop and chirality test.
sys.path.insert(0, REARVIEW)
from cohort import build_cohort                                  # noqa: E402
from run_experiment import make_crop, gt_arrays, CROP_PAD        # noqa: E402

# Ticket #19's detector adapter and its pose scoring, reused rather than
# reimplemented. pose_row is the exact function that produced #19's swap rates.
#
# #19's sweep file is ALSO called run_experiment.py, so a plain import would
# hand back the already-cached rear-view module instead. Load it by path under
# its own name. It in turn imports rear-view's, which is by then cached, so
# both tickets' helpers come from the files those tickets actually ran.
sys.path.insert(0, DETECTOR)
import detectors                                                  # noqa: E402
import importlib.util                                             # noqa: E402
_spec = importlib.util.spec_from_file_location(
    "pd_run_experiment", os.path.join(DETECTOR, "run_experiment.py"))
_pd = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_pd)
pose_row, iou_xyxy = _pd.pose_row, _pd.iou_xyxy

CACHE = os.path.expanduser("~/.cache/poseperfect-checkpoint-swap")

RTMPOSE_M_BODY7_OFFICIAL_ONNX = (
    "https://download.openmmlab.com/mmpose/v1/projects/rtmposev1/onnx_sdk/"
    "rtmpose-m_simcc-body7_pt-body7_420e-256x192-e48f03d0_20230504.zip"
)
BODY7_PTH = "rtmpose-m_simcc-body7_pt-body7_420e-256x192-e48f03d0_20230504.pth"
AIC_COCO_PTH = "rtmpose-m_simcc-aic-coco_pt-aic-coco_420e-256x192-63eb25f7_20230126.pth"


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def build_pose_arms(onnx_dir):
    """The three pose arms, each an rtmlib RTMPose over a different graph.

    rtmlib is #18's and #19's decode path. Using it for all three arms means
    the SimCC split ratio, the top-down affine and the ImageNet normalisation
    are identical across arms and identical to the two earlier tickets - the
    only thing that varies is the weights.
    """
    from rtmlib import RTMPose

    arms = {}
    arms["body7_official"] = RTMPose(
        onnx_model=RTMPOSE_M_BODY7_OFFICIAL_ONNX, model_input_size=(192, 256),
        backend="onnxruntime", device="cpu")
    for tag, sub in (("body7_self", "body7"), ("aic_coco_self", "aic-coco")):
        path = os.path.join(onnx_dir, sub, "end2end.onnx")
        if not os.path.exists(path):
            raise SystemExit(f"missing {path} - run ./export_onnx.sh first")
        arms[tag] = RTMPose(onnx_model=path, model_input_size=(192, 256),
                            backend="onnxruntime", device="cpu")
    return arms


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", default=os.path.expanduser(
        "~/.cache/poseperfect-rearview/data"))
    ap.add_argument("--ckpts", default=os.path.expanduser(
        "~/.cache/poseperfect-detector/checkpoints"))
    ap.add_argument("--cfgs", default=os.path.expanduser(
        "~/.cache/poseperfect-detector/configs"))
    ap.add_argument("--onnx", default=os.path.join(CACHE, "onnx"))
    ap.add_argument("--out", default=os.path.join(HERE, "results"))
    ap.add_argument("--limit", type=int, default=0, help="0 = whole cohort")
    # Same sharding scheme as #19. Consequence, stated because it matters:
    # latency from a sharded run is contended wall clock, not a clean timing.
    # Cost claims come from bench_onnx.py, which runs alone.
    ap.add_argument("--shard", type=int, default=0)
    ap.add_argument("--nshards", type=int, default=1)
    args = ap.parse_args()

    os.makedirs(args.out, exist_ok=True)
    ann = os.path.join(args.data, "annotations", "person_keypoints_val2017.json")
    imdir = os.path.join(args.data, "val2017")

    cohort = build_cohort(ann)
    if args.limit:
        per, keep = {}, []
        for i in cohort:
            per.setdefault(i.orientation, 0)
            if per[i.orientation] < args.limit:
                per[i.orientation] += 1
                keep.append(i)
        cohort = keep
    if args.nshards > 1:
        cohort = [c for i, c in enumerate(cohort) if i % args.nshards == args.shard]
    print(f"cohort: {len(cohort)} instances "
          f"(shard {args.shard}/{args.nshards})", flush=True)

    arms = build_pose_arms(args.onnx)
    print("pose arms:", list(arms), flush=True)

    det = detectors.build("rtmdet_ins_tiny", args.ckpts, args.cfgs)
    print("detector:", det.name, flush=True)

    fields = [
        "ann_id", "image_id", "file_name", "orientation", "face_visible",
        "num_keypoints", "area", "bbox_h", "gt_shoulder_sign",
        "pose_model", "box_source", "detector",
        "n_person_det", "top1_score", "top1_iou", "best_iou", "best_rank",
        "pose_oks_raw", "pose_oks_corrected", "pose_pck02_corrected",
        "pose_n_scored", "pose_chirality_swapped", "pose_chirality_margin",
        "pose_n_chir", "pose_pred_shoulder_sign", "pose_conf_mean",
    ]

    suffix = "" if args.nshards == 1 else f".shard{args.shard}"
    path = os.path.join(args.out, f"per_instance{suffix}.csv")

    # Resume, same rule as #19: an instance counts as done only if it carries
    # the full complement of rows. A half-written trailing instance is dropped
    # and recomputed.
    expected = len(arms) * 2
    done = set()
    if os.path.exists(path):
        with open(path, newline="") as f:
            old = list(csv.DictReader(f))
        counts = {}
        for r in old:
            counts[r["ann_id"]] = counts.get(r["ann_id"], 0) + 1
        done = {int(a) for a, c in counts.items() if c == expected}
        with open(path, "w", newline="") as f:
            wr = csv.DictWriter(f, fieldnames=fields)
            wr.writeheader()
            wr.writerows([r for r in old if int(r["ann_id"]) in done])
        print(f"resuming: {len(done)} instances already complete", flush=True)

    t0 = time.time()
    n = 0
    with open(path, "a" if done else "w", newline="") as f:
        wr = csv.DictWriter(f, fieldnames=fields)
        if not done:
            wr.writeheader()
        for inst in cohort:
            if inst.ann_id in done:
                continue
            img = cv2.imread(os.path.join(imdir, inst.file_name))
            if img is None:
                continue
            img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            crop, ox, oy, box_xywh = make_crop(img, inst.bbox)
            gxy, gv = gt_arrays(inst)
            gt_box = [box_xywh[0], box_xywh[1],
                      box_xywh[0] + box_xywh[2], box_xywh[1] + box_xywh[3]]

            base = {
                "ann_id": inst.ann_id, "image_id": inst.image_id,
                "file_name": inst.file_name, "orientation": inst.orientation,
                "face_visible": inst.face_visible,
                "num_keypoints": inst.num_keypoints,
                "area": f"{inst.area:.1f}", "bbox_h": f"{inst.bbox[3]:.1f}",
                "gt_shoulder_sign": inst.gt_shoulder_sign,
            }

            # The detector runs ONCE. Every pose arm then sees the identical
            # box, so an arm-to-arm difference cannot be a detector difference.
            try:
                found = det.detect(crop)
            except Exception as exc:                   # keep the sweep alive
                print("detect error", inst.ann_id, exc, flush=True)
                found = []
            if found:
                ious = [iou_xyxy(d["box"], gt_box) for d in found]
                bi = int(np.argmax(ious))
                det_meta = {
                    "n_person_det": len(found),
                    "top1_score": f"{found[0]['score']:.4f}",
                    "top1_iou": f"{ious[0]:.4f}",
                    "best_iou": f"{ious[bi]:.4f}", "best_rank": bi,
                }
                det_box = found[0]["box"]
            else:
                det_meta = {"n_person_det": 0, "top1_score": "",
                            "top1_iou": 0.0, "best_iou": 0.0, "best_rank": -1}
                det_box = None

            for tag, engine in arms.items():
                # #18's condition: the ground-truth box.
                row = dict(base, pose_model=tag, box_source="gt_box",
                           detector="gt_box", n_person_det="", top1_score="",
                           top1_iou=1.0, best_iou=1.0, best_rank=0)
                row.update(pose_row(engine, crop, gt_box, ox, oy,
                                    gxy, gv, inst.area))
                wr.writerow(row)

                # #19's condition: the box RTMDet-Ins-tiny actually produced.
                row = dict(base, pose_model=tag, box_source="rtmdet_ins_tiny",
                           detector=det.name, **det_meta)
                if det_box is not None:
                    row.update(pose_row(engine, crop, det_box, ox, oy,
                                        gxy, gv, inst.area))
                wr.writerow(row)
            n += 1
            if n % 50 == 0:
                print(f"{n}/{len(cohort)}  {time.time()-t0:.0f}s", flush=True)

    ckpt_dir = os.path.join(CACHE, "checkpoints")
    meta = {
        "ticket": 20,
        "dataset": "COCO val2017 person keypoints",
        "cohort": "reused verbatim from experiments/rear-view (ticket #18)",
        "cohort_size": len(cohort),
        "crop_pad": CROP_PAD,
        "mode": "IMAGE / static single-image inference only",
        "score_threshold_applied_at_record_time": None,
        "decode": "rtmlib RTMPose, the same reference implementation as #18/#19",
        "pose_arms": {
            "body7_official": {"source": RTMPOSE_M_BODY7_OFFICIAL_ONNX},
            "body7_self": {
                "checkpoint": BODY7_PTH,
                "checkpoint_sha256": sha256(os.path.join(ckpt_dir, BODY7_PTH)),
                "onnx": os.path.join(args.onnx, "body7", "end2end.onnx"),
                "onnx_bytes": os.path.getsize(
                    os.path.join(args.onnx, "body7", "end2end.onnx")),
            },
            "aic_coco_self": {
                "checkpoint": AIC_COCO_PTH,
                "checkpoint_sha256": sha256(os.path.join(ckpt_dir, AIC_COCO_PTH)),
                "onnx": os.path.join(args.onnx, "aic-coco", "end2end.onnx"),
                "onnx_bytes": os.path.getsize(
                    os.path.join(args.onnx, "aic-coco", "end2end.onnx")),
            },
        },
        "box_sources": ["gt_box", "rtmdet_ins_tiny"],
        "detector": {"name": det.name,
                     "checkpoint": os.path.basename(det.checkpoint),
                     "checkpoint_bytes": det.checkpoint_bytes},
        "hardware": "CPU only, Linux, Python 3.10",
        "seconds": round(time.time() - t0, 1),
    }
    with open(os.path.join(args.out, f"run_meta{suffix}.json"), "w") as f:
        json.dump(meta, f, indent=2)
    print(json.dumps(meta, indent=2))


if __name__ == "__main__":
    main()
