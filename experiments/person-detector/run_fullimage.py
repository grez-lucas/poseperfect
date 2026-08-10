"""PROTOTYPE - throwaway. Unconstrained-input control for wayfinder ticket #19.

The main sweep feeds the detector a 1.25x crop centred on the subject, because
that is what map decisions 8 and 14 promise the product will capture. That is
the friendliest realistic input, and it risks flattering the detector: finding
a person in a picture that is almost entirely one person is easy.

This script runs the same detector over the WHOLE source image instead, and
asks the same question - was the cohort instance found at IoU >= 0.5, bucketed
by orientation. It is the harder condition, and it is the one that says whether
rear-view competence is a property of the detector or of the crop.

Writes results/full_image.csv, one row per (instance, detector).
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
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "rear-view"))
sys.path.insert(0, HERE)

from cohort import build_cohort          # noqa: E402
import detectors                          # noqa: E402
from run_experiment import iou_xyxy       # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", default=os.path.expanduser(
        "~/.cache/poseperfect-rearview/data"))
    ap.add_argument("--ckpts", default=os.path.expanduser(
        "~/.cache/poseperfect-detector/checkpoints"))
    ap.add_argument("--cfgs", default=os.path.expanduser(
        "~/.cache/poseperfect-detector/configs"))
    ap.add_argument("--out", default=os.path.join(HERE, "results"))
    ap.add_argument("--detectors", default="rtmdet_ins_tiny")
    args = ap.parse_args()

    ann = os.path.join(args.data, "annotations", "person_keypoints_val2017.json")
    imdir = os.path.join(args.data, "val2017")
    cohort = build_cohort(ann)

    by_image = {}
    for i in cohort:
        by_image.setdefault(i.file_name, []).append(i)
    print(f"{len(cohort)} instances across {len(by_image)} images", flush=True)

    dets = [detectors.build(n, args.ckpts, args.cfgs)
            for n in args.detectors.split(",")]

    path = os.path.join(args.out, "full_image.csv")
    fields = ["ann_id", "orientation", "gt_shoulder_sign", "bbox_h", "detector",
              "n_person_det", "best_iou", "best_rank", "best_score",
              "best_mask_iou"]
    t0 = time.time()
    with open(path, "w", newline="") as f:
        wr = csv.DictWriter(f, fieldnames=fields)
        wr.writeheader()
        for n, (fn, insts) in enumerate(by_image.items(), 1):
            img = cv2.imread(os.path.join(imdir, fn))
            if img is None:
                continue
            rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            for d in dets:
                try:
                    found = d.detect(rgb)
                except Exception as exc:
                    print("detect error", fn, d.name, exc, flush=True)
                    found = []
                for inst in insts:
                    x, y, w, h = inst.bbox
                    gt = [x, y, x + w, y + h]
                    row = {"ann_id": inst.ann_id, "orientation": inst.orientation,
                           "gt_shoulder_sign": inst.gt_shoulder_sign,
                           "bbox_h": f"{inst.bbox[3]:.1f}", "detector": d.name,
                           "n_person_det": len(found)}
                    if not found:
                        row.update({"best_iou": 0.0, "best_rank": -1})
                        wr.writerow(row)
                        continue
                    ious = [iou_xyxy(fd["box"], gt) for fd in found]
                    bi = int(np.argmax(ious))
                    row.update({"best_iou": f"{ious[bi]:.4f}", "best_rank": bi,
                                "best_score": f"{found[bi]['score']:.4f}"})
                    wr.writerow(row)
            if n % 100 == 0:
                print(f"{n}/{len(by_image)}  {time.time()-t0:.0f}s", flush=True)
    print(json.dumps({"images": len(by_image), "seconds": round(time.time()-t0, 1)}))


if __name__ == "__main__":
    main()
