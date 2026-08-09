"""PROTOTYPE - throwaway. Analysis for wayfinder ticket #19.

Reads results/per_instance.csv and writes results/summary.json and
results/summary.md. Follows ticket #18's conventions: Wilson intervals on every
rate, two-proportion z-tests where a difference carries a decision, and
positional error kept separate from chirality error throughout.

Run:  ./run.sh  (or .venv310/bin/python analyse.py)
"""

from __future__ import annotations

import json
import math
import os

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
RES = os.path.join(HERE, "results")
BUCKET_ORDER = ["FRONT", "OBLIQUE", "PROFILE", "REAR"]
IOU_HIT = 0.5
SCORE_SWEEP = [0.0, 0.05, 0.1, 0.3, 0.5, 0.7]


def wilson(k, n, z=1.96):
    if n == 0:
        return (float("nan"), float("nan"))
    p = k / n
    d = 1 + z * z / n
    c = p + z * z / (2 * n)
    s = z * np.sqrt(p * (1 - p) / n + z * z / (4 * n * n))
    return ((c - s) / d, (c + s) / d)


def two_prop_z(k1, n1, k2, n2):
    """Two-sided two-proportion z-test. Returns (z, p)."""
    if n1 == 0 or n2 == 0:
        return float("nan"), float("nan")
    p1, p2 = k1 / n1, k2 / n2
    p = (k1 + k2) / (n1 + n2)
    se = math.sqrt(p * (1 - p) * (1 / n1 + 1 / n2))
    if se == 0:
        return float("nan"), float("nan")
    z = (p1 - p2) / se
    p_val = math.erfc(abs(z) / math.sqrt(2))
    return z, p_val


def md(df, floatfmt="{:.3f}"):
    df = df.copy()
    for c in df.columns:
        if df[c].dtype.kind == "f":
            df[c] = df[c].map(lambda v: "" if pd.isna(v) else floatfmt.format(v))
    head = "| " + " | ".join([df.index.name or ""] + list(map(str, df.columns))) + " |"
    sep = "|" + "|".join(["---"] * (len(df.columns) + 1)) + "|"
    rows = ["| " + " | ".join([str(i)] + [str(v) for v in r]) + " |"
            for i, r in zip(df.index, df.values)]
    return "\n".join([head, sep] + rows)


def rate_table(d, value_col, detectors, buckets=BUCKET_ORDER, ci=True):
    """rate of a 0/1 column per detector per orientation bucket, with CI."""
    rows = {}
    for b in buckets:
        row = {}
        for det in detectors:
            sel = d[(d.detector == det) & (d.orientation == b)][value_col].dropna()
            n, k = len(sel), int(sel.sum())
            if n == 0:
                row[det] = ""
                continue
            lo, hi = wilson(k, n)
            row[det] = (f"{k/n:.3f} [{lo:.3f}, {hi:.3f}] n={n}" if ci
                        else f"{k/n:.3f}")
        rows[b] = row
    t = pd.DataFrame(rows).T
    t.index.name = "orientation"
    return t


def mean_table(d, value_col, detectors, buckets=BUCKET_ORDER):
    rows = {}
    for b in buckets:
        row = {}
        for det in detectors:
            sel = d[(d.detector == det) & (d.orientation == b)][value_col].dropna()
            row[det] = float(sel.mean()) if len(sel) else float("nan")
        rows[b] = row
    t = pd.DataFrame(rows).T
    t.index.name = "orientation"
    return t


def main():
    d = pd.read_csv(os.path.join(RES, "per_instance.csv"))
    d["orientation"] = pd.Categorical(d["orientation"], BUCKET_ORDER, ordered=True)
    detectors = [x for x in d.detector.unique() if x != "gt_box"]
    seg_detectors = [x for x in detectors if d[d.detector == x]
                     ["top1_mask_iou"].notna().any()]

    # Sign-confirmed subsets, exactly as ticket #18 defined them: the
    # visibility proxy AND the annotated shoulder order agree.
    d["confirmed"] = (
        ((d.orientation == "REAR") & (d.gt_shoulder_sign > 0)) |
        ((d.orientation == "FRONT") & (d.gt_shoulder_sign < 0))
    )
    d["hit"] = (d.top1_iou >= IOU_HIT).astype(float)
    d["any_hit"] = (d.best_iou >= IOU_HIT).astype(float)
    d["no_det"] = (d.n_person_det.fillna(0) == 0).astype(float)

    out, lines = {}, []

    def say(s=""):
        print(s)
        lines.append(s)

    say("# Ticket #19 - person detector sweep\n")
    say("Cohort, crop and chirality test reused verbatim from "
        "`experiments/rear-view/` (ticket #18). CPU, IMAGE mode, no score "
        "threshold applied at record time.\n")

    inst = d.drop_duplicates("ann_id")
    t = inst.groupby("orientation", observed=True).agg(
        n=("ann_id", "size"),
        facing_away_by_gt_shoulders=("gt_shoulder_sign", lambda s: (s > 0).mean()),
        median_bbox_h=("bbox_h", "median"))
    t.index.name = "orientation"
    say("## 0. Cohort\n")
    say(md(t))
    out["cohort"] = json.loads(t.to_json(orient="index"))

    # ---- 1. detector rear-view competence -----------------------------
    say("\n## 1. Does the detector find a person who is facing away?\n")
    say("Top-1 person detection matching the ground-truth box at IoU >= 0.5. "
        "Rate [95% Wilson CI] n.\n")
    t1 = rate_table(d, "hit", detectors)
    say(md(t1))
    out["top1_hit_iou50"] = json.loads(t1.to_json(orient="index"))

    say("\nAny returned person detection matching at IoU >= 0.5 (upper bound "
        "on what a smarter selection rule could reach):\n")
    t1b = rate_table(d, "any_hit", detectors)
    say(md(t1b))
    out["any_hit_iou50"] = json.loads(t1b.to_json(orient="index"))

    say("\nInstances where the detector returned NO person detection at all - "
        "the failure mode that took BlazePose to 30.0% on rear views:\n")
    t1c = rate_table(d, "no_det", detectors)
    say(md(t1c))
    out["no_detection_at_all"] = json.loads(t1c.to_json(orient="index"))

    # score-threshold sweep, because the map forbids gating on confidence and
    # the honest treatment is to show how much the answer moves.
    say("\n### 1b. Sensitivity to the detector score threshold\n")
    say("Top-1 hit rate at IoU >= 0.5 when the top-1 detection is additionally "
        "required to score at least `s`. Map constraint 3 forbids gating on "
        "engine confidence; this is here to show what a threshold would cost, "
        "not to pick one.\n")
    sweep = {}
    for det in detectors:
        for b in BUCKET_ORDER:
            sel = d[(d.detector == det) & (d.orientation == b)]
            for s in SCORE_SWEEP:
                ok = ((sel.top1_iou >= IOU_HIT) & (sel.top1_score.fillna(0) >= s))
                sweep.setdefault(f"s>={s}", {})[f"{det} {b}"] = float(ok.mean())
    ts = pd.DataFrame(sweep).T
    ts.index.name = "score"
    say(md(ts))
    out["score_threshold_sweep"] = json.loads(ts.to_json(orient="index"))

    say("\n### 1c. Box quality where the detector did hit\n")
    say("Mean IoU of the top-1 box against the ground-truth box, hits only:\n")
    hits = d[d.hit == 1]
    t1d = mean_table(hits, "top1_iou", detectors)
    say(md(t1d))
    out["mean_top1_iou_on_hits"] = json.loads(t1d.to_json(orient="index"))

    # ---- 2. RTMPose with a real detector ------------------------------
    say("\n## 2. RTMPose-m with a real detector instead of ground-truth boxes\n")
    say("Chirality swap rate - the fatal error, because it is bimodal rather "
        "than systematic. `gt_box` is ticket #18's condition, recomputed here "
        "on the identical instances.\n")
    allsrc = ["gt_box"] + detectors
    t2 = rate_table(d, "pose_chirality_swapped", allsrc)
    say(md(t2))
    out["chirality_swap_by_source"] = json.loads(t2.to_json(orient="index"))

    say("\nSame, restricted to **sign-confirmed** instances (proxy label and "
        "annotated shoulder order agree) - the subset ticket #18 quoted in its "
        "verdict:\n")
    t2b = rate_table(d[d.confirmed], "pose_chirality_swapped", allsrc,
                     buckets=["FRONT", "REAR"])
    say(md(t2b))
    out["chirality_swap_confirmed"] = json.loads(t2b.to_json(orient="index"))

    say("\nTwo-proportion z-tests, ground-truth box vs each detector, on "
        "sign-confirmed REAR:\n")
    tests = {}
    base = d[d.confirmed & (d.orientation == "REAR") & (d.detector == "gt_box")]
    k1, n1 = int(base.pose_chirality_swapped.sum()), len(base)
    for det in detectors:
        s = d[d.confirmed & (d.orientation == "REAR") & (d.detector == det)]
        k2, n2 = int(s.pose_chirality_swapped.sum()), len(s)
        z, p = two_prop_z(k2, n2, k1, n1)
        tests[det] = {"gt_box": f"{k1}/{n1}", "detector": f"{k2}/{n2}",
                      "z": round(z, 3) if z == z else None,
                      "p": round(p, 4) if p == p else None}
    say("```json\n" + json.dumps(tests, indent=2) + "\n```")
    out["chirality_ztests_rear_confirmed"] = tests

    say("\nPositional error, kept separate as the map requires. Mean OKS after "
        "correcting chirality:\n")
    t2c = mean_table(d, "pose_oks_corrected", allsrc)
    say(md(t2c))
    out["oks_corrected"] = json.loads(t2c.to_json(orient="index"))

    say("\nComposite usable-capture rate, using ticket #18's definition - the "
        "detector found the subject (IoU >= 0.5) AND the resulting pose is not "
        "chirally transposed:\n")
    d["usable"] = ((d.top1_iou >= IOU_HIT) &
                   (d.pose_chirality_swapped == 0)).astype(float)
    t2d = rate_table(d, "usable", detectors)
    say(md(t2d))
    out["usable_capture_rate"] = json.loads(t2d.to_json(orient="index"))

    # ---- 3. segmentation quality --------------------------------------
    if seg_detectors:
        say("\n## 3. Segmentation quality, and specifically on rear views\n")
        say("Mask IoU of the top-1 detection's mask against the COCO "
            "ground-truth instance segmentation, hits only:\n")
        t3 = mean_table(hits, "top1_mask_iou", seg_detectors)
        say(md(t3))
        out["mask_iou"] = json.loads(t3.to_json(orient="index"))

        say("\nMask precision and recall, kept separate. For a lat spread the "
            "damaging failure is the mask CLIPPING the flared silhouette, "
            "which is a recall failure; bleeding into the background is a "
            "precision failure and costs a width measurement far less.\n")
        t3b = mean_table(hits, "top1_mask_recall", seg_detectors)
        say("Mask recall (fraction of the true silhouette captured):\n")
        say(md(t3b))
        t3c = mean_table(hits, "top1_mask_precision", seg_detectors)
        say("\nMask precision:\n")
        say(md(t3c))
        out["mask_recall"] = json.loads(t3b.to_json(orient="index"))
        out["mask_precision"] = json.loads(t3c.to_json(orient="index"))

        say("\nFraction of hits whose mask IoU clears 0.7, a rough "
            "'silhouette is usable' bar:\n")
        h = hits.copy()
        h["mask_ok"] = (h.top1_mask_iou >= 0.7).astype(float)
        t3d = rate_table(h, "mask_ok", seg_detectors)
        say(md(t3d))
        out["mask_iou_ge_070"] = json.loads(t3d.to_json(orient="index"))

    # ---- 4. cost ------------------------------------------------------
    say("\n## 4. Detector cost on this box (CPU, PyTorch, not the shipped runtime)\n")
    t4 = d[d.detector != "gt_box"].groupby("detector", observed=True).agg(
        median_ms=("det_latency_ms", "median"),
        p90_ms=("det_latency_ms", lambda s: float(np.nanpercentile(s, 90))))
    t4.index.name = "detector"
    say(md(t4, "{:.1f}"))
    out["detector_latency_ms"] = json.loads(t4.to_json(orient="index"))
    say("\nThese are PyTorch-on-x86 numbers and are NOT an iOS estimate. The "
        "ONNX Runtime figures are in the writeup.\n")

    with open(os.path.join(RES, "summary.json"), "w") as f:
        json.dump(out, f, indent=2)
    with open(os.path.join(RES, "summary.md"), "w") as f:
        f.write("\n".join(lines) + "\n")


if __name__ == "__main__":
    main()
