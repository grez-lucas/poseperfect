"""PROTOTYPE - throwaway. Analysis for wayfinder ticket #18.

Reads results/per_instance.csv and writes results/summary.json plus a set of
Markdown tables on stdout. Positional error and chirality error are reported
separately and never combined.

Run:  ./run.sh  (or .venv/bin/python analyse.py)
"""

from __future__ import annotations

import json
import os
import sys

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
RES = os.path.join(HERE, "results")
BUCKET_ORDER = ["FRONT", "OBLIQUE", "PROFILE", "REAR"]
DECISIVE_MARGIN = 0.05


def wilson(k, n, z=1.96):
    """Wilson score interval - honest on small buckets and near 0/1."""
    if n == 0:
        return (float("nan"), float("nan"))
    p = k / n
    d = 1 + z * z / n
    c = p + z * z / (2 * n)
    s = z * np.sqrt(p * (1 - p) / n + z * z / (4 * n * n))
    return ((c - s) / d, (c + s) / d)


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


def main():
    d = pd.read_csv(os.path.join(RES, "per_instance.csv"))
    d["orientation"] = pd.Categorical(d["orientation"], BUCKET_ORDER, ordered=True)
    out = {}
    lines = []

    def say(s=""):
        print(s)
        lines.append(s)

    # ---- 0. cohort and proxy validation -------------------------------
    inst = d.drop_duplicates("ann_id")
    say("## 0. Cohort and proxy validation\n")
    t = inst.groupby("orientation", observed=True).agg(
        n=("ann_id", "size"),
        facing_away_by_gt_shoulders=("gt_shoulder_sign", lambda s: (s > 0).mean()),
        ears_visible_mean=("ears_visible", "mean"),
        median_bbox_h=("bbox_h", "median"),
    )
    t.index.name = "orientation"
    say(md(t))
    out["cohort"] = json.loads(t.to_json(orient="index"))
    say("\n`facing_away_by_gt_shoulders` is the fraction of instances whose "
        "ANNOTATED right shoulder lies to the viewer's right - a second, "
        "independent read on orientation from the same ground truth. It is "
        "what bounds contamination of the visibility-derived proxy.\n")

    # Sign-confirmed subsets: proxy label AND annotated shoulder order agree.
    d["confirmed"] = (
        ((d.orientation == "REAR") & (d.gt_shoulder_sign > 0)) |
        ((d.orientation == "FRONT") & (d.gt_shoulder_sign < 0))
    )

    # ---- 1. detection ---------------------------------------------------
    say("\n## 1. Detection failure rate (the face-anchored-detector hypothesis)\n")
    t = d.pivot_table(index="orientation", columns="engine", values="detected",
                      aggfunc=lambda s: 1 - s.mean(), observed=True)
    t.index.name = "orientation"
    say(md(t))
    out["detection_failure_rate"] = json.loads(t.to_json(orient="index"))

    det = d[d.detected == 1].copy()

    # ---- 2. chirality ---------------------------------------------------
    say("\n## 2. Chirality error - swap rate (THE FATAL ONE)\n")
    say("An instance is `swapped` when the engine's output matches the "
        "ground truth better after transposing every left/right landmark "
        "label than it does as emitted. Scored on torso and limb pairs at "
        "GT v==2 only, normalised by sqrt(COCO area).\n")
    ch = det[det.n_chir >= 4]
    t = ch.pivot_table(index="orientation", columns="engine",
                       values="chirality_swapped", aggfunc="mean", observed=True)
    t.index.name = "orientation"
    say(md(t))
    out["swap_rate"] = json.loads(t.to_json(orient="index"))

    say("\n### 2b. Swap rate with 95% Wilson intervals, sign-confirmed buckets\n")
    say("| engine | bucket | n | swap rate | 95% CI |")
    say("|---|---|---|---|---|")
    conf_rows = {}
    for eng in sorted(ch.engine.unique()):
        for b in ("FRONT", "REAR"):
            s = ch[(ch.engine == eng) & (ch.orientation == b) & ch.confirmed]
            n, k = len(s), int(s.chirality_swapped.sum())
            lo, hi = wilson(k, n)
            say(f"| {eng} | {b} (sign-confirmed) | {n} | {k/n:.3f} | {lo:.3f} - {hi:.3f} |")
            conf_rows[f"{eng}|{b}"] = {"n": n, "k": k, "rate": k / n,
                                       "ci": [lo, hi]}
    out["swap_rate_confirmed"] = conf_rows

    say("\n### 2c. Decisive swaps only (|margin| > "
        f"{DECISIVE_MARGIN} sqrt-area units)\n")
    say("Guards against near-symmetric standing poses where the two "
        "hypotheses are all but tied and the label is noise.\n")
    dec = ch[ch.chirality_margin.abs() > DECISIVE_MARGIN]
    t = dec.pivot_table(index="orientation", columns="engine",
                        values="chirality_swapped", aggfunc="mean", observed=True)
    t.index.name = "orientation"
    say(md(t))
    t2 = ch.pivot_table(index="orientation", columns="engine",
                        values="chirality_margin",
                        aggfunc=lambda s: (s.abs() > DECISIVE_MARGIN).mean(),
                        observed=True)
    t2.index.name = "orientation"
    say("\nFraction of instances that are decisive at all:\n")
    say(md(t2))
    out["swap_rate_decisive"] = json.loads(t.to_json(orient="index"))
    out["decisive_fraction"] = json.loads(t2.to_json(orient="index"))

    # ---- 3. positional error --------------------------------------------
    say("\n## 3. Positional error, chirality-corrected (the tolerable one)\n")
    say("OKS over GT keypoints at v==2, computed AFTER applying the "
        "left/right correction, so this number is positional error with the "
        "chirality failure removed. This is the quantity that cancels when "
        "an athlete is scored against their own reference.\n")
    t = det.pivot_table(index="orientation", columns="engine",
                        values="oks_corrected", aggfunc="mean", observed=True)
    t.index.name = "orientation"
    say(md(t))
    out["oks_corrected"] = json.loads(t.to_json(orient="index"))

    say("\n### 3b. OKS as emitted (chirality error left in)\n")
    t = det.pivot_table(index="orientation", columns="engine",
                        values="oks_raw", aggfunc="mean", observed=True)
    t.index.name = "orientation"
    say(md(t))
    out["oks_raw"] = json.loads(t.to_json(orient="index"))

    say("\n### 3c. PCK@0.2 sqrt(area), chirality-corrected\n")
    t = det.pivot_table(index="orientation", columns="engine",
                        values="pck02_corrected", aggfunc="mean", observed=True)
    t.index.name = "orientation"
    say(md(t))
    out["pck02_corrected"] = json.loads(t.to_json(orient="index"))

    say("\n### 3d. Degradation with facing-away, sign-confirmed FRONT vs REAR\n")
    say("| engine | OKS corr FRONT | OKS corr REAR | delta | OKS raw FRONT | "
        "OKS raw REAR | delta |")
    say("|---|---|---|---|---|---|---|")
    deg = {}
    for eng in sorted(det.engine.unique()):
        f = det[(det.engine == eng) & (det.orientation == "FRONT") & det.confirmed]
        r = det[(det.engine == eng) & (det.orientation == "REAR") & det.confirmed]
        row = dict(oks_corr_front=f.oks_corrected.mean(),
                   oks_corr_rear=r.oks_corrected.mean(),
                   oks_raw_front=f.oks_raw.mean(), oks_raw_rear=r.oks_raw.mean())
        say(f"| {eng} | {row['oks_corr_front']:.3f} | {row['oks_corr_rear']:.3f} | "
            f"{row['oks_corr_rear']-row['oks_corr_front']:+.3f} | "
            f"{row['oks_raw_front']:.3f} | {row['oks_raw_rear']:.3f} | "
            f"{row['oks_raw_rear']-row['oks_raw_front']:+.3f} |")
        deg[eng] = row
    out["front_vs_rear"] = deg

    # ---- 4. shoulder-sign heuristic -------------------------------------
    say("\n## 4. The shoulder-sign heuristic\n")
    say("`sign(RIGHT_SHOULDER.x - LEFT_SHOULDER.x)` on the PREDICTED "
        "landmarks, scored against the same sign computed on the ANNOTATED "
        "shoulders. Unconditioned - full proxy buckets, no sign filtering, "
        "so this is not circular.\n")
    t = det.pivot_table(index="orientation", columns="engine",
                        values="shoulder_sign_correct", aggfunc="mean",
                        observed=True)
    t.index.name = "orientation"
    say(md(t))
    out["shoulder_sign_accuracy"] = json.loads(t.to_json(orient="index"))

    say("\n### 4b. Overall accuracy and rear recall\n")
    say("| engine | overall acc | REAR acc | n REAR | FRONT acc | n FRONT |")
    say("|---|---|---|---|---|---|")
    ss = {}
    for eng in sorted(det.engine.unique()):
        e = det[det.engine == eng]
        r = e[e.orientation == "REAR"]
        f = e[e.orientation == "FRONT"]
        ss[eng] = {"overall": e.shoulder_sign_correct.mean(),
                   "rear": r.shoulder_sign_correct.mean(), "n_rear": len(r),
                   "front": f.shoulder_sign_correct.mean(), "n_front": len(f)}
        say(f"| {eng} | {ss[eng]['overall']:.3f} | {ss[eng]['rear']:.3f} | "
            f"{len(r)} | {ss[eng]['front']:.3f} | {len(f)} |")
    out["shoulder_sign_summary"] = ss

    # ---- 5. confidence --------------------------------------------------
    say("\n## 5. Is confidence usable as a self-check?\n")
    say("Mean per-landmark confidence. BlazePose reports `visibility`; "
        "MoveNet and RTMPose report a keypoint score. The question is "
        "whether any of them falls on the inputs where the engine is wrong.\n")
    for col, label in (("conf_nose", "nose"), ("conf_eyes", "eyes"),
                       ("conf_shoulders", "shoulders"), ("conf_mean", "all 17")):
        t = det.pivot_table(index="orientation", columns="engine", values=col,
                            aggfunc="mean", observed=True)
        t.index.name = "orientation"
        say(f"\n**{label}**\n")
        say(md(t))
        out.setdefault("confidence", {})[col] = json.loads(t.to_json(orient="index"))

    say("\n### 5b. Confidence on the instances the engine got CHIRALLY WRONG\n")
    say("| engine | n swapped | mean conf (all 17) on swapped | "
        "mean conf on correct | conf_nose on swapped |")
    say("|---|---|---|---|---|")
    cu = {}
    for eng in sorted(ch.engine.unique()):
        e = ch[ch.engine == eng]
        sw, ok = e[e.chirality_swapped == 1], e[e.chirality_swapped == 0]
        cu[eng] = {"n_swapped": len(sw), "conf_swapped": sw.conf_mean.mean(),
                   "conf_correct": ok.conf_mean.mean(),
                   "conf_nose_swapped": sw.conf_nose.mean()}
        say(f"| {eng} | {len(sw)} | {sw.conf_mean.mean():.3f} | "
            f"{ok.conf_mean.mean():.3f} | {sw.conf_nose.mean():.3f} |")
    out["confidence_on_swapped"] = cu

    # ---- 6. where degradation begins ------------------------------------
    say("\n## 6. Where degradation begins\n")
    say("The proxy is ordinal, not angular: `face_visible` counts how many "
        "of {nose, left_eye, right_eye} the annotator marked v==2. It is a "
        "monotone stand-in for turning away from the camera. There is no "
        "degree axis without MEBOW.\n")
    t = det.pivot_table(index="face_visible", columns="engine",
                        values=["oks_corrected"], aggfunc="mean")
    t.columns = [c[1] for c in t.columns]
    t.index.name = "face_visible"
    say("**OKS, chirality-corrected, by face_visible (3 = fully frontal face, "
        "0 = no face keypoint visible)**\n")
    say(md(t.sort_index(ascending=False)))
    t2 = ch.pivot_table(index="face_visible", columns="engine",
                        values="chirality_swapped", aggfunc="mean")
    t2.index.name = "face_visible"
    say("\n**Chirality swap rate by face_visible**\n")
    say(md(t2.sort_index(ascending=False)))
    out["by_face_visible_oks"] = json.loads(t.to_json(orient="index"))
    out["by_face_visible_swap"] = json.loads(t2.to_json(orient="index"))

    with open(os.path.join(RES, "summary.json"), "w") as f:
        json.dump(out, f, indent=2, default=float)
    with open(os.path.join(RES, "summary.md"), "w") as f:
        f.write("\n".join(lines) + "\n")




def extra():
    """Section 7: robustness checks and the product-level composite."""
    import json as _json
    d = pd.read_csv(os.path.join(RES, "per_instance.csv"))
    d["orientation"] = pd.Categorical(d["orientation"], BUCKET_ORDER, ordered=True)
    d["confirmed"] = (
        ((d.orientation == "REAR") & (d.gt_shoulder_sign > 0)) |
        ((d.orientation == "FRONT") & (d.gt_shoulder_sign < 0)))
    out, lines = {}, []

    def say(s=""):
        print(s)
        lines.append(s)

    say("\n## 7. Robustness checks and the product-level composite\n")

    # --- 7a. size confound -------------------------------------------------
    say("### 7a. Size confound control\n")
    say("REAR instances are smaller than FRONT in COCO, so the raw comparison "
        "confounds viewpoint with scale. Repeated inside size bands.\n")
    d["size_band"] = pd.cut(d.bbox_h, [100, 200, 300, 1e9],
                            labels=["100-200px", "200-300px", ">300px"], right=False)
    for metric, agg, label in (
            ("detected", lambda s: 1 - s.mean(), "detection failure rate"),
            ("chirality_swapped", "mean", "chirality swap rate"),
            ("oks_corrected", "mean", "OKS (chirality-corrected)")):
        say(f"\n**{label}, FRONT vs REAR within size band**\n")
        say("| size band | engine | FRONT | REAR | n FRONT | n REAR |")
        say("|---|---|---|---|---|---|")
        for band in ["100-200px", "200-300px", ">300px"]:
            for eng in sorted(d.engine.unique()):
                s = d[(d.size_band == band) & (d.engine == eng)]
                if metric != "detected":
                    s = s[(s.detected == 1) & (s.n_chir >= 4)]
                f = s[(s.orientation == "FRONT") & s.confirmed]
                r = s[(s.orientation == "REAR") & s.confirmed]
                if len(f) < 15 or len(r) < 15:
                    continue
                fv = (1 - f[metric].mean()) if metric == "detected" else f[metric].mean()
                rv = (1 - r[metric].mean()) if metric == "detected" else r[metric].mean()
                say(f"| {band} | {eng} | {fv:.3f} | {rv:.3f} | {len(f)} | {len(r)} |")
                out.setdefault(label, {})[f"{band}|{eng}"] = {
                    "front": fv, "rear": rv, "n_front": len(f), "n_rear": len(r)}

    # --- 7b. product composite --------------------------------------------
    say("\n### 7b. Product-level composite: fraction of captures that are USABLE\n")
    say("A capture is usable only if the engine returns a pose AND that pose "
        "is not chirally transposed. Non-detections count as failures - the "
        "app cannot score what it did not get. This is the number that "
        "matters to a rear-facing mandatory pose.\n")
    say("| engine | FRONT usable | REAR usable | n FRONT | n REAR |")
    say("|---|---|---|---|---|")
    for eng in sorted(d.engine.unique()):
        e = d[(d.engine == eng) & d.confirmed]
        row = {}
        for b in ("FRONT", "REAR"):
            s = e[e.orientation == b]
            usable = ((s.detected == 1) & (s.chirality_swapped.fillna(1) == 0)).mean()
            row[b] = (usable, len(s))
        say(f"| {eng} | {row['FRONT'][0]:.3f} | {row['REAR'][0]:.3f} | "
            f"{row['FRONT'][1]} | {row['REAR'][1]} |")
        out.setdefault("usable_capture_rate", {})[eng] = {
            "front": row["FRONT"][0], "rear": row["REAR"][0],
            "n_front": row["FRONT"][1], "n_rear": row["REAR"][1]}

    # --- 7c. can the shoulder-sign heuristic catch the swap? ---------------
    say("\n### 7c. Can the shoulder-sign heuristic DETECT the chirality swap?\n")
    say("The heuristic reads facing direction off the same predicted "
        "landmarks that are swapped. If the two agree almost perfectly, the "
        "heuristic is not an independent check - it is the failure, restated.\n")
    say("| engine | agreement(sign wrong == swapped) | swaps caught (recall) | "
        "false alarms | n |")
    say("|---|---|---|---|---|")
    ch = d[(d.detected == 1) & (d.n_chir >= 4)]
    for eng in sorted(ch.engine.unique()):
        e = ch[ch.engine == eng]
        signwrong = (e.shoulder_sign_correct == 0)
        swapped = (e.chirality_swapped == 1)
        agree = (signwrong == swapped).mean()
        recall = signwrong[swapped].mean() if swapped.any() else float("nan")
        fa = swapped[signwrong].eq(False).mean() if signwrong.any() else float("nan")
        say(f"| {eng} | {agree:.3f} | {recall:.3f} | {fa:.3f} | {len(e)} |")
        out.setdefault("heuristic_vs_swap", {})[eng] = {
            "agreement": agree, "recall": recall, "false_alarm": fa, "n": len(e)}

    # --- 7d. is confidence separable at all? -------------------------------
    say("\n### 7d. AUC of confidence as a detector of the chirality swap\n")
    say("0.50 = the confidence signal carries no information about whether "
        "the engine got chirality right. Computed on REAR instances only.\n")
    say("| engine | AUC conf_mean | AUC conf_nose | n swapped | n correct |")
    say("|---|---|---|---|---|")

    def auc(pos, neg):
        if len(pos) == 0 or len(neg) == 0:
            return float("nan")
        allv = np.concatenate([pos, neg])
        r = pd.Series(allv).rank().values
        return (r[:len(pos)].sum() - len(pos) * (len(pos) + 1) / 2) / (len(pos) * len(neg))

    for eng in sorted(ch.engine.unique()):
        e = ch[(ch.engine == eng) & (ch.orientation == "REAR")]
        sw, ok = e[e.chirality_swapped == 1], e[e.chirality_swapped == 0]
        a1 = auc(ok.conf_mean.values, sw.conf_mean.values)
        a2 = auc(ok.conf_nose.values, sw.conf_nose.values)
        say(f"| {eng} | {a1:.3f} | {a2:.3f} | {len(sw)} | {len(ok)} |")
        out.setdefault("conf_auc_rear", {})[eng] = {
            "auc_conf_mean": a1, "auc_conf_nose": a2,
            "n_swapped": len(sw), "n_correct": len(ok)}

    # --- 7e. is the flip coherent or piecewise? ----------------------------
    say("\n### 7e. Is the chirality failure a COHERENT global mirror, or piecewise?\n")
    say("Chirality is decided independently for four limb groups "
        "(shoulders, hips, arms, legs). If a rear-view failure were a clean "
        "global front/back flip, every group would agree, and a downstream "
        "fix could recover it by transposing all labels. If groups disagree, "
        "the output is internally inconsistent and no relabelling recovers "
        "it.\n")
    say("| engine | bucket | n with 4 groups decided | all-4 agree | "
        "all-4 swapped | mixed (incoherent) |")
    say("|---|---|---|---|---|---|")
    g = d[(d.detected == 1) & (d.n_groups_decided == 4)]
    for eng in sorted(g.engine.unique()):
        for b in ("FRONT", "REAR"):
            s_ = g[(g.engine == eng) & (g.orientation == b) & g.confirmed]
            if len(s_) < 10:
                continue
            allsw = (s_.n_groups_swapped == 4).mean()
            allok = (s_.n_groups_swapped == 0).mean()
            mixed = 1 - allsw - allok
            say(f"| {eng} | {b} | {len(s_)} | {allok+allsw:.3f} | "
                f"{allsw:.3f} | {mixed:.3f} |")
            out.setdefault("chirality_coherence", {})[f"{eng}|{b}"] = {
                "n": len(s_), "all_agree": allok + allsw,
                "all_swapped": allsw, "mixed": mixed}

    say("\n**Per-group swap rate, sign-confirmed REAR**\n")
    say("| engine | shoulders | hips | arms | legs |")
    say("|---|---|---|---|---|")
    gr = d[(d.detected == 1) & (d.orientation == "REAR") & d.confirmed]
    for eng in sorted(gr.engine.unique()):
        e = gr[gr.engine == eng]
        vals = [e[f"swap_{k}"].mean() for k in ("shoulders", "hips", "arms", "legs")]
        say("| " + eng + " | " + " | ".join(f"{v:.3f}" for v in vals) + " |")
        out.setdefault("per_group_swap_rear", {})[eng] = dict(
            zip(("shoulders", "hips", "arms", "legs"), vals))

    # --- 7f. are the engine differences on REAR real? ----------------------
    say("\n### 7f. Two-proportion z-tests on the REAR swap rate\n")
    say("Wilson intervals for two proportions can overlap while the "
        "difference is still significant, so the comparison is tested "
        "directly. Sign-confirmed REAR only.\n")
    say("| comparison | p1 | p2 | z | two-sided p |")
    say("|---|---|---|---|---|")
    rr = d[(d.detected == 1) & (d.n_chir >= 4) &
           (d.orientation == "REAR") & d.confirmed]

    def _phi(x):
        import math
        return 0.5 * (1 + math.erf(x / math.sqrt(2)))

    def zt(k1, n1, k2, n2):
        import math
        p1, p2 = k1 / n1, k2 / n2
        p = (k1 + k2) / (n1 + n2)
        se = math.sqrt(p * (1 - p) * (1 / n1 + 1 / n2))
        z = (p1 - p2) / se if se > 0 else float("nan")
        return p1, p2, z, 2 * (1 - _phi(abs(z)))

    counts = {}
    for eng in sorted(rr.engine.unique()):
        e = rr[rr.engine == eng]
        counts[eng] = (int(e.chirality_swapped.sum()), len(e))
    for a, b in (("blazepose_heavy", "movenet_thunder"),
                 ("blazepose_full", "movenet_thunder"),
                 ("movenet_thunder", "rtmpose_m"),
                 ("blazepose_heavy", "rtmpose_m")):
        if a not in counts or b not in counts:
            continue
        p1, p2, z, pv = zt(*counts[a], *counts[b])
        say(f"| {a} vs {b} | {p1:.3f} (n={counts[a][1]}) | "
            f"{p2:.3f} (n={counts[b][1]}) | {z:.2f} | {pv:.4f} |")
        out.setdefault("rear_swap_ztests", {})[f"{a}_vs_{b}"] = {
            "p1": p1, "p2": p2, "z": z, "p_value": pv,
            "k1": counts[a][0], "n1": counts[a][1],
            "k2": counts[b][0], "n2": counts[b][1]}

    with open(os.path.join(RES, "summary_extra.json"), "w") as f:
        _json.dump(out, f, indent=2, default=float)
    with open(os.path.join(RES, "summary.md"), "a") as f:
        f.write("\n".join(lines) + "\n")


if __name__ == "__main__":
    main()
    extra()
