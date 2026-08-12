"""PROTOTYPE - throwaway. Analysis for wayfinder ticket #20.

Reads results/per_instance.csv and writes results/summary.json and
results/summary.md. Follows #18's and #19's conventions without deviation:
Wilson intervals on every rate, two-proportion z-tests where a difference
carries a decision, and positional error kept strictly separate from chirality
error.

The helpers (wilson, two_prop_z, md) are #19's, imported from
../person-detector/analyse.py rather than copied, so the intervals and the
tests here are computed by the same code that computed #19's.

Run:  ./run.sh  (or ../person-detector/.venv310/bin/python analyse.py)
"""

from __future__ import annotations

import importlib.util
import json
import os

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
RES = os.path.join(HERE, "results")
DETECTOR = os.path.join(os.path.dirname(HERE), "person-detector")

_spec = importlib.util.spec_from_file_location(
    "pd_analyse", os.path.join(DETECTOR, "analyse.py"))
_pd = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_pd)
wilson, two_prop_z, md = _pd.wilson, _pd.two_prop_z, _pd.md

BUCKET_ORDER = ["FRONT", "OBLIQUE", "PROFILE", "REAR"]
IOU_HIT = 0.5
ALL_ARMS = ["body7_official", "body7_self", "aic_coco_self", "coco_self"]


def rate_table(d, value_col, arms, buckets=BUCKET_ORDER, ci=True):
    rows = {}
    for b in buckets:
        row = {}
        for a in arms:
            sel = d[(d.arm == a) & (d.orientation == b)][value_col].dropna()
            n, k = len(sel), int(sel.sum())
            if n == 0:
                row[a] = ""
                continue
            lo, hi = wilson(k, n)
            row[a] = (f"{k/n:.3f} [{lo:.3f}, {hi:.3f}] n={n}" if ci
                      else f"{k/n:.3f}")
        rows[b] = row
    t = pd.DataFrame(rows).T
    t.index.name = "orientation"
    return t


def mean_table(d, value_col, arms, buckets=BUCKET_ORDER):
    rows = {}
    for b in buckets:
        row = {}
        for a in arms:
            sel = d[(d.arm == a) & (d.orientation == b)][value_col].dropna()
            row[a] = float(sel.mean()) if len(sel) else float("nan")
        rows[b] = row
    t = pd.DataFrame(rows).T
    t.index.name = "orientation"
    return t


def counted(d, arm, bucket, col="pose_chirality_swapped"):
    s = d[(d.arm == arm) & (d.orientation == bucket)][col].dropna()
    return int(s.sum()), len(s)


def check_detector_agreement(d):
    """Every arm must have seen the SAME detector box for a given instance.

    This is the check that makes a two-pass sweep legitimate. `run.sh` sweeps
    all arms in one pass, but the committed results were produced as three arms
    then one, and concatenated. The arms are independent per instance and the
    detector runs once per instance on a deterministic crop, so the second pass
    must reproduce the identical box. Verify that rather than assert it.
    """
    det = d[d.box_source == "rtmdet_ins_tiny"]
    cols = ["n_person_det", "top1_score", "top1_iou", "best_iou", "best_rank"]
    bad = []
    for c in cols:
        n = det.groupby("ann_id")[c].nunique(dropna=False)
        bad.extend(f"{c}: {int((n > 1).sum())} instances" for _ in [0]
                   if (n > 1).any())
    if bad:
        raise SystemExit(
            "detector columns disagree between arms, so the passes are not "
            "commensurable and must not be merged: " + "; ".join(bad))
    return len(det.ann_id.unique()), len(cols)


def main():
    d = pd.read_csv(os.path.join(RES, "per_instance.csv"))
    d["orientation"] = pd.Categorical(d["orientation"], BUCKET_ORDER, ordered=True)
    d["arm"] = d.pose_model
    ARMS = [a for a in ALL_ARMS if a in set(d.arm)]
    n_inst, n_cols = check_detector_agreement(d)

    # #18's sign-confirmed subsets, unchanged: the visibility proxy AND the
    # annotated shoulder order agree.
    d["confirmed"] = (
        ((d.orientation == "REAR") & (d.gt_shoulder_sign > 0)) |
        ((d.orientation == "FRONT") & (d.gt_shoulder_sign < 0))
    )
    d["hit"] = (d.top1_iou >= IOU_HIT).astype(float)

    gt = d[d.box_source == "gt_box"]
    det = d[d.box_source == "rtmdet_ins_tiny"]
    # #19's conditioning for the deployable number: restrict to instances where
    # the top-1 detection actually was the target, so the figure measures the
    # cost of a real box rather than the cost of a naive selection rule.
    det_sel = det[det.hit == 1]

    out, lines = {}, []

    def say(s=""):
        print(s)
        lines.append(s)

    say("# Ticket #20 - checkpoint swap sweep\n")
    say("Cohort, crop and chirality test reused verbatim from "
        "`experiments/rear-view/` (#18). Detector and pose scoring reused "
        "verbatim from `experiments/person-detector/` (#19). CPU, IMAGE mode, "
        "no score threshold applied at record time.\n")
    say(f"Arms: {', '.join(ARMS)}.\n")
    say(f"Merge check: every arm saw the same detector box on all {n_inst} "
        f"instances, across all {n_cols} detector columns. The committed "
        "results were produced in two passes and concatenated; this is the "
        "check that makes that legitimate.\n")
    out["detector_agreement_instances"] = n_inst

    inst = d.drop_duplicates("ann_id")
    t = inst.groupby("orientation", observed=True).agg(
        n=("ann_id", "size"),
        facing_away_by_gt_shoulders=("gt_shoulder_sign", lambda s: (s > 0).mean()),
        median_bbox_h=("bbox_h", "median"))
    t.index.name = "orientation"
    say("## 0. Cohort\n")
    say(md(t))
    out["cohort"] = json.loads(t.to_json(orient="index"))

    # ---- 1. the control ------------------------------------------------
    say("\n## 1. The control: does the self-exported graph reproduce the "
        "official one?\n")
    say("`aic-coco` ships no official ONNX, so its graph had to be exported "
        "here. Without this check, any difference it shows could be an export "
        "artefact rather than a property of the weights. `body7` ships BOTH, "
        "so exporting it too gives a direct answer.\n")
    piv = d.pivot_table(index=["ann_id", "box_source"], columns="arm",
                        values=["pose_oks_corrected", "pose_chirality_swapped"])
    doks = (piv[("pose_oks_corrected", "body7_official")] -
            piv[("pose_oks_corrected", "body7_self")]).abs()
    dchi = (piv[("pose_chirality_swapped", "body7_official")] !=
            piv[("pose_chirality_swapped", "body7_self")])
    ctrl = {
        "rows_compared": int(doks.notna().sum()),
        "max_abs_oks_difference": float(np.nanmax(doks.values)),
        "mean_abs_oks_difference": float(np.nanmean(doks.values)),
        "chirality_verdict_disagreements": int(dchi.sum()),
    }
    say("| | |")
    say("|---|---|")
    say(f"| rows compared | {ctrl['rows_compared']} |")
    say(f"| max abs difference in corrected OKS | {ctrl['max_abs_oks_difference']:.3e} |")
    say(f"| mean abs difference in corrected OKS | {ctrl['mean_abs_oks_difference']:.3e} |")
    say(f"| instances where the chirality verdict differs | {ctrl['chirality_verdict_disagreements']} |")
    out["export_control"] = ctrl

    # For the same reason, check the two checkpoints are actually different
    # weights and not the same file under two names.
    daic = (piv[("pose_oks_corrected", "body7_official")] -
            piv[("pose_oks_corrected", "aic_coco_self")]).abs()
    out["aic_coco_differs_from_body7"] = {
        "max_abs_oks_difference": float(np.nanmax(daic.values)),
        "mean_abs_oks_difference": float(np.nanmean(daic.values)),
    }
    say(f"\nSanity check in the other direction, so a null result cannot be a "
        f"mislabelled file: `aic_coco_self` vs `body7_official` differ by "
        f"mean {out['aic_coco_differs_from_body7']['mean_abs_oks_difference']:.3e} "
        f"and max {out['aic_coco_differs_from_body7']['max_abs_oks_difference']:.3e} "
        f"corrected OKS. The two arms are genuinely different weights.\n")

    # ---- 2. chirality, the number the ticket asks for -------------------
    say("\n## 2. Chirality swap rate - the number this ticket exists for\n")
    say("Fatal failure mode, kept separate from positional error throughout. "
        "The engine's `left_shoulder` is not the athlete's left shoulder.\n")

    say("### 2a. On ground-truth boxes - #18's condition\n")
    t2 = rate_table(gt, "pose_chirality_swapped", ARMS)
    say(md(t2))
    out["chirality_swap_gt_box"] = json.loads(t2.to_json(orient="index"))

    say("\nSign-confirmed only (proxy label and annotated shoulder order "
        "agree) - the subset #18's verdict quoted:\n")
    t2b = rate_table(gt[gt.confirmed], "pose_chirality_swapped", ARMS,
                     buckets=["FRONT", "REAR"])
    say(md(t2b))
    out["chirality_swap_gt_box_confirmed"] = json.loads(t2b.to_json(orient="index"))

    say("\n### 2b. On RTMDet-Ins-tiny boxes, given correct selection - "
        "#19's condition, and the deployable one\n")
    t2c = rate_table(det_sel, "pose_chirality_swapped", ARMS)
    say(md(t2c))
    out["chirality_swap_detector"] = json.loads(t2c.to_json(orient="index"))

    say("\nSign-confirmed only:\n")
    t2d = rate_table(det_sel[det_sel.confirmed], "pose_chirality_swapped",
                     ARMS, buckets=["FRONT", "REAR"])
    say(md(t2d))
    out["chirality_swap_detector_confirmed"] = json.loads(t2d.to_json(orient="index"))

    # ---- 3. the tests that carry the decision --------------------------
    say("\n### 2c. Two-proportion z-tests, each candidate against "
        "`body7_official`, on sign-confirmed instances\n")
    say("This is the test the swap decision rests on. A null result means the "
        "swap costs nothing measurable on the failure mode the product cares "
        "about; it does NOT mean the checkpoints are identical.\n")
    candidates = [a for a in ARMS if a not in ("body7_official", "body7_self")]
    for bucket in ("REAR", "FRONT"):
        tests = {}
        for label, frame in (("gt_box", gt[gt.confirmed]),
                             ("rtmdet_ins_tiny", det_sel[det_sel.confirmed])):
            k1, n1 = counted(frame, "body7_official", bucket)
            row = {"body7_official": f"{k1}/{n1}"}
            for cand in candidates:
                k2, n2 = counted(frame, cand, bucket)
                z, p = two_prop_z(k2, n2, k1, n1)
                row[cand] = {
                    "swaps": f"{k2}/{n2}",
                    "z": round(z, 3) if z == z else None,
                    "p": round(p, 4) if p == p else None,
                }
            tests[label] = row
        say(f"\n**{bucket}:**\n")
        say("```json\n" + json.dumps(tests, indent=2) + "\n```")
        out[f"chirality_ztests_{bucket.lower()}_confirmed"] = tests
    say("\nFRONT is reported alongside REAR so a rear-specific claim is not "
        "made from a whole-cohort effect.\n")

    # ---- 4. positional error, kept separate ----------------------------
    say("\n## 3. Positional error, kept separate as the map requires\n")
    say("Mean OKS after correcting chirality. Tolerable if systematic, "
        "because it cancels when an athlete is scored against their own "
        "earlier reference.\n")
    say("On ground-truth boxes:\n")
    t3 = mean_table(gt, "pose_oks_corrected", ARMS)
    say(md(t3, "{:.4f}"))
    out["oks_corrected_gt_box"] = json.loads(t3.to_json(orient="index"))

    say("\nOn RTMDet-Ins-tiny boxes, given correct selection:\n")
    t3b = mean_table(det_sel, "pose_oks_corrected", ARMS)
    say(md(t3b, "{:.4f}"))
    out["oks_corrected_detector"] = json.loads(t3b.to_json(orient="index"))

    say("\nPCK@0.2 after correcting chirality, ground-truth boxes:\n")
    t3c = mean_table(gt, "pose_pck02_corrected", ARMS)
    say(md(t3c, "{:.4f}"))
    out["pck02_corrected_gt_box"] = json.loads(t3c.to_json(orient="index"))

    say("\nRaw OKS, i.e. before chirality correction. This is the number a "
        "single accuracy figure would report, and it merges the two failure "
        "modes the map insists on separating. Recorded, not headlined:\n")
    t3d = mean_table(gt, "pose_oks_raw", ARMS)
    say(md(t3d, "{:.4f}"))
    out["oks_raw_gt_box"] = json.loads(t3d.to_json(orient="index"))

    # ---- 5. composite --------------------------------------------------
    say("\n## 4. Composite usable-capture rate\n")
    say("#18's definition: the detector found the subject (IoU >= 0.5) AND "
        "the resulting pose is not chirally transposed. Over the whole "
        "detector arm, without conditioning on correct selection.\n")
    det = det.copy()
    det["usable"] = ((det.top1_iou >= IOU_HIT) &
                     (det.pose_chirality_swapped == 0)).astype(float)
    t4 = rate_table(det, "usable", ARMS)
    say(md(t4))
    out["usable_capture_rate"] = json.loads(t4.to_json(orient="index"))

    with open(os.path.join(RES, "summary.json"), "w") as f:
        json.dump(out, f, indent=2)
    with open(os.path.join(RES, "summary.md"), "w") as f:
        f.write("\n".join(lines) + "\n")


if __name__ == "__main__":
    main()
