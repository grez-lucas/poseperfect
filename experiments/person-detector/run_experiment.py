"""PROTOTYPE - throwaway. Wayfinder ticket #19: source the person detector.

Reuses ticket #18's cohort, crop construction and chirality scoring verbatim
(`experiments/rear-view/`) rather than rebuilding them, so the numbers here sit
on the same 1,675-instance COCO val2017 cohort and the same orientation proxy.

Three questions, one sweep:

  1. REAR-VIEW COMPETENCE OF THE DETECTOR ITSELF. Does a candidate person
     detector find a person who is facing away? Measured as recall against the
     ground-truth box, bucketed by the #18 orientation proxy. BlazePose's own
     face-anchored detector returned nothing on 30.0% of rear instances under
     these exact conditions; that is the bar.

  2. RTMPOSE-M WITH A REAL DETECTOR IN FRONT OF IT. #18 ran RTMPose on
     ground-truth boxes, so its 1.0% rear chirality swap rate is a pose-head
     upper bound. Here the same pose model is re-run on the box the detector
     actually produced, and the two are compared on identical instances.

  3. SEGMENTATION QUALITY, AND SPECIFICALLY ON REAR VIEWS. Mask IoU against
     the COCO ground-truth instance segmentation, bucketed by orientation. A
     mask good enough for a front lat spread need not survive a back one.

Discipline carried over from #18 and from the map's standing constraints:

  - IMAGE mode / static single-image inference only.
  - Nothing is validated by eye. No overlay is rendered anywhere.
  - NO SCORE THRESHOLD is applied when recording. Every person detection the
    model returns is written out with its score, and thresholds are swept in
    analyse.py. The map forbids gating on engine confidence; the honest
    treatment of a detector score is to measure how much the answer depends on
    it, not to pick one.

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
REARVIEW = os.path.join(os.path.dirname(HERE), "rear-view")
sys.path.insert(0, REARVIEW)

# Reused verbatim from ticket #18. Same cohort, same proxy, same crop, same
# chirality test - that is what makes the two sets of numbers comparable.
from cohort import build_cohort, BODY_PAIRS, IDX                  # noqa: E402
from run_experiment import (make_crop, gt_arrays, oks, pck,       # noqa: E402
                            chirality, MIRROR, CROP_PAD)

sys.path.insert(0, HERE)
import detectors                                                   # noqa: E402

RTMPOSE_M_BODY7 = (
    "https://download.openmmlab.com/mmpose/v1/projects/rtmposev1/onnx_sdk/"
    "rtmpose-m_simcc-body7_pt-body7_420e-256x192-e48f03d0_20230504.zip"
)


def iou_xyxy(a, b):
    ix = max(0.0, min(a[2], b[2]) - max(a[0], b[0]))
    iy = max(0.0, min(a[3], b[3]) - max(a[1], b[1]))
    inter = ix * iy
    ua = (a[2] - a[0]) * (a[3] - a[1]) + (b[2] - b[0]) * (b[3] - b[1]) - inter
    return inter / ua if ua > 0 else 0.0


def mask_metrics(pred_mask, gt_mask):
    """IoU, plus precision/recall of the predicted mask against ground truth.

    Precision and recall are kept separate on purpose. For a lat spread the
    failure that matters is the mask CLIPPING the flared silhouette, which is a
    recall failure; a mask that bleeds into the background is a precision
    failure and is far less damaging to a width measurement.
    """
    if pred_mask is None or gt_mask is None:
        return (float("nan"),) * 3
    p = pred_mask.astype(bool)
    g = gt_mask.astype(bool)
    inter = np.logical_and(p, g).sum()
    union = np.logical_or(p, g).sum()
    if union == 0:
        return (float("nan"),) * 3
    prec = inter / p.sum() if p.sum() else float("nan")
    rec = inter / g.sum() if g.sum() else float("nan")
    return float(inter / union), float(prec), float(rec)


def gt_masks_by_ann(ann_path, wanted_ids):
    """Decode COCO instance segmentations for the cohort, keyed by ann_id."""
    from pycocotools import mask as maskutils

    with open(ann_path) as f:
        coco = json.load(f)
    sizes = {im["id"]: (im["height"], im["width"]) for im in coco["images"]}
    out = {}
    for ann in coco["annotations"]:
        if ann["id"] not in wanted_ids:
            continue
        h, w = sizes[ann["image_id"]]
        seg = ann["segmentation"]
        if isinstance(seg, list):
            rles = maskutils.frPyObjects(seg, h, w)
            rle = maskutils.merge(rles)
        elif isinstance(seg["counts"], list):
            rle = maskutils.frPyObjects(seg, h, w)
        else:
            rle = seg
        out[ann["id"]] = maskutils.decode(rle).astype(bool)
    return out


def crop_mask(full_mask, xi, yi, side):
    """Crop a full-image mask with make_crop's geometry, zero-padded."""
    out = np.zeros((side, side), bool)
    sx0, sy0 = max(0, xi), max(0, yi)
    sx1 = min(full_mask.shape[1], xi + side)
    sy1 = min(full_mask.shape[0], yi + side)
    if sx1 > sx0 and sy1 > sy0:
        out[sy0 - yi:sy1 - yi, sx0 - xi:sx1 - xi] = full_mask[sy0:sy1, sx0:sx1]
    return out


def pose_row(pose_engine, crop_rgb, box_in_crop, ox, oy, gxy, gv, area):
    """Run RTMPose-m on one box and score it exactly as ticket #18 did."""
    x0, y0, x1, y1 = box_in_crop
    kps, scores = pose_engine(crop_rgb, bboxes=[[float(x0), float(y0),
                                                 float(x1), float(y1)]])
    pxy = np.asarray(kps[0], np.float64) + np.array([ox, oy])
    conf = np.asarray(scores[0], np.float64)

    d_id, d_sw, n_ch = chirality(pxy, gxy, gv, area, BODY_PAIRS)
    swapped = int(np.isfinite(d_sw) and d_sw < d_id)
    cxy = pxy[MIRROR] if swapped else pxy
    o_raw, n_s = oks(pxy, gxy, gv, area)
    o_cor, _ = oks(cxy, gxy, gv, area)
    p_cor, _ = pck(cxy, gxy, gv, area)
    dx = pxy[IDX["right_shoulder"], 0] - pxy[IDX["left_shoulder"], 0]
    psign = 1 if dx > 0 else (-1 if dx < 0 else 0)
    return {
        "pose_oks_raw": o_raw, "pose_oks_corrected": o_cor,
        "pose_pck02_corrected": p_cor, "pose_n_scored": n_s,
        "pose_chirality_swapped": swapped,
        "pose_chirality_margin": (d_id - d_sw) if np.isfinite(d_sw) else float("nan"),
        "pose_n_chir": n_ch,
        "pose_pred_shoulder_sign": psign,
        "pose_conf_mean": float(np.mean(conf)),
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", default=os.path.expanduser(
        "~/.cache/poseperfect-rearview/data"))
    ap.add_argument("--ckpts", default=os.path.expanduser(
        "~/.cache/poseperfect-detector/checkpoints"))
    ap.add_argument("--cfgs", default=os.path.expanduser(
        "~/.cache/poseperfect-detector/configs"))
    ap.add_argument("--out", default=os.path.join(HERE, "results"))
    ap.add_argument("--limit", type=int, default=0, help="0 = whole cohort")
    ap.add_argument("--detectors",
                    default="rtmdet_ins_tiny,rtmdet_ins_s,rtmdet_nano_person")
    # The sweep is CPU-bound and embarrassingly parallel over instances, so it
    # is shardable. run.sh runs the shards concurrently and concatenates them.
    # Consequence, stated because it matters: det_latency_ms from a sharded run
    # is contended wall clock, not a clean timing. Cost claims come from
    # bench_onnx.py, which runs alone.
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

    print("decoding ground-truth instance masks", flush=True)
    gt_masks = gt_masks_by_ann(ann, {i.ann_id for i in cohort})

    from rtmlib import RTMPose
    pose = RTMPose(onnx_model=RTMPOSE_M_BODY7, model_input_size=(192, 256),
                   backend="onnxruntime", device="cpu")

    dets = [detectors.build(n, args.ckpts, args.cfgs)
            for n in args.detectors.split(",")]
    print("detectors:", [d.name for d in dets], flush=True)

    fields = [
        "ann_id", "image_id", "file_name", "orientation", "face_visible",
        "num_keypoints", "area", "bbox_h", "gt_shoulder_sign", "detector",
        "n_person_det", "top1_score", "top1_iou", "best_iou", "best_rank",
        "top1_mask_iou", "top1_mask_precision", "top1_mask_recall",
        "det_latency_ms",
        "pose_oks_raw", "pose_oks_corrected", "pose_pck02_corrected",
        "pose_n_scored", "pose_chirality_swapped", "pose_chirality_margin",
        "pose_n_chir", "pose_pred_shoulder_sign", "pose_conf_mean",
    ]

    suffix = "" if args.nshards == 1 else f".shard{args.shard}"
    path = os.path.join(args.out, f"per_instance{suffix}.csv")

    # Resume. An instance counts as done only if it has the full complement of
    # rows (one gt_box baseline plus one per detector); a half-written trailing
    # instance is dropped and recomputed. The file is rewritten with only the
    # complete instances, then appended to.
    done = set()
    if os.path.exists(path):
        expected = 1 + len(dets)
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
    det_ms = {d.name: [] for d in dets}
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
            side = crop.shape[0]
            gxy, gv = gt_arrays(inst)
            gt_box = [box_xywh[0], box_xywh[1],
                      box_xywh[0] + box_xywh[2], box_xywh[1] + box_xywh[3]]
            gt_m = crop_mask(gt_masks[inst.ann_id], int(round(ox)),
                             int(round(oy)), side) if inst.ann_id in gt_masks else None

            base = {
                "ann_id": inst.ann_id, "image_id": inst.image_id,
                "file_name": inst.file_name, "orientation": inst.orientation,
                "face_visible": inst.face_visible,
                "num_keypoints": inst.num_keypoints,
                "area": f"{inst.area:.1f}", "bbox_h": f"{inst.bbox[3]:.1f}",
                "gt_shoulder_sign": inst.gt_shoulder_sign,
            }

            # Baseline: RTMPose-m on the ground-truth box, i.e. ticket #18's
            # condition, recomputed in-process so the comparison below is
            # against the identical instances rather than a joined table.
            row = dict(base, detector="gt_box", n_person_det="", top1_score="",
                       top1_iou=1.0, best_iou=1.0, best_rank=0,
                       top1_mask_iou="", top1_mask_precision="",
                       top1_mask_recall="", det_latency_ms="")
            row.update(pose_row(pose, crop, gt_box, ox, oy, gxy, gv, inst.area))
            wr.writerow(row)

            for d in dets:
                t = time.time()
                try:
                    found = d.detect(crop)
                except Exception as exc:                  # keep the sweep alive
                    print("detect error", inst.ann_id, d.name, exc, flush=True)
                    found = []
                ms = (time.time() - t) * 1000.0
                det_ms[d.name].append(ms)

                row = dict(base, detector=d.name, n_person_det=len(found),
                           det_latency_ms=f"{ms:.1f}")
                if not found:
                    row.update({"top1_iou": 0.0, "best_iou": 0.0, "best_rank": -1})
                    wr.writerow(row)
                    continue

                ious = [iou_xyxy(f["box"], gt_box) for f in found]
                bi = int(np.argmax(ious))
                mi, mp, mr = mask_metrics(found[0]["mask"], gt_m)
                row.update({
                    "top1_score": f"{found[0]['score']:.4f}",
                    "top1_iou": f"{ious[0]:.4f}",
                    "best_iou": f"{ious[bi]:.4f}", "best_rank": bi,
                    "top1_mask_iou": "" if np.isnan(mi) else f"{mi:.4f}",
                    "top1_mask_precision": "" if np.isnan(mp) else f"{mp:.4f}",
                    "top1_mask_recall": "" if np.isnan(mr) else f"{mr:.4f}",
                })
                row.update(pose_row(pose, crop, found[0]["box"], ox, oy,
                                    gxy, gv, inst.area))
                wr.writerow(row)
            n += 1
            if n % 50 == 0:
                print(f"{n}/{len(cohort)}  {time.time()-t0:.0f}s", flush=True)

    meta = {
        "ticket": 19,
        "dataset": "COCO val2017 person keypoints",
        "cohort": "reused verbatim from experiments/rear-view (ticket #18)",
        "cohort_size": len(cohort),
        "crop_pad": CROP_PAD,
        "mode": "IMAGE / static single-image inference only",
        "score_threshold_applied_at_record_time": None,
        "pose_model": RTMPOSE_M_BODY7,
        "detectors": {d.name: {"checkpoint": os.path.basename(d.checkpoint),
                               "checkpoint_bytes": d.checkpoint_bytes}
                      for d in dets},
        "detector_latency_ms_median": {k: round(float(np.median(v)), 1)
                                       for k, v in det_ms.items() if v},
        "hardware": "CPU only, Linux, Python 3.10",
        "seconds": round(time.time() - t0, 1),
    }
    with open(os.path.join(args.out, f"run_meta{suffix}.json"), "w") as f:
        json.dump(meta, f, indent=2)
    print(json.dumps(meta, indent=2))


if __name__ == "__main__":
    main()
