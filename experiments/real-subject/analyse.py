"""PROTOTYPE - throwaway. Wayfinder ticket #9: tables and the verdict.

THE THRESHOLDS BELOW WERE FIXED BEFORE ANY PHOTOGRAPH WAS TAKEN. They are the
grilled answer to a gap this ticket exposed in the map: #9 says "if a genuine
posing correction produces a smaller change than that jitter, the metric
measures noise", and nowhere on the map, in any of the twenty tickets, was the
size of a genuine posing correction ever written down. A threshold chosen once
the jitter is known is not a test, it is a rationalisation.

Reported, and never merged into one number:

  chirality   fatal, because it is bimodal. A coin flip between two
              interpretations destroys self-referential comparison in a way a
              consistent offset never does.
  detection   its own outcome. #18 found this dominated BlazePose's rear
              failures at 30%, and unlike chirality it is trivially detectable
              at runtime.
  noise floor two of them. The sensor floor is what the pipeline could ever
              achieve; the human floor is what it will actually see, and it is
              the one #11 and #12 inherit.

Run:  ./run.sh
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import os
from collections import defaultdict

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))

# ---------------------------------------------------------------------------
# PRE-REGISTERED. Do not edit these after looking at a result.
# ---------------------------------------------------------------------------
CORRECTION_CM = 5.0        # smallest limb displacement the app must report
CORRECTION_DEG = 3.0       # smallest segment angle change the app must report

# MDC95 - the change a single new capture must show before it can be called a
# real change rather than the same pose measured twice. 1.96 * sqrt(2) * SEM,
# the standard test-retest form: sqrt(2) because both the reference and the new
# capture carry the noise, 1.96 for two-sided 95%. Comparing a raw standard
# deviation against 5 cm would silently claim a sensitivity the pipeline does
# not have.
MDC_K = 1.96 * math.sqrt(2.0)

SWAP_CONFIRM = 0.05        # under this on REAR: RTMPose confirmed, #14 proceeds
SWAP_MITIGATE = 0.20       # 5-20%: confirmed, orientation prior becomes mandatory
                           # over 20%: rear mandatories cannot be scored on drift

SEGMENTS = [
    ("shoulder_line", "left_shoulder", "right_shoulder"),
    ("hip_line", "left_hip", "right_hip"),
    ("left_upper_arm", "left_shoulder", "left_elbow"),
    ("right_upper_arm", "right_shoulder", "right_elbow"),
    ("left_forearm", "left_elbow", "left_wrist"),
    ("right_forearm", "right_elbow", "right_wrist"),
    ("left_thigh", "left_hip", "left_knee"),
    ("right_thigh", "right_hip", "right_knee"),
    ("left_shank", "left_knee", "left_ankle"),
    ("right_shank", "right_knee", "right_ankle"),
]
MARKED = {"left_wrist", "right_wrist", "left_ankle", "right_ankle"}


def wilson(k, n, z=1.96):
    if n == 0:
        return (float("nan"), float("nan"))
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return (max(0.0, c - h), min(1.0, c + h))


def load(out):
    with open(os.path.join(out, "per_frame.csv"), newline="") as f:
        frames = list(csv.DictReader(f))
    kps = defaultdict(dict)
    with open(os.path.join(out, "keypoints.csv"), newline="") as f:
        for r in csv.DictReader(f):
            kps[(r["n"], r["box_source"])][r["name"]] = (
                float(r["x"]), float(r["y"]))
    with open(os.path.join(out, "run_meta.json")) as f:
        meta = json.load(f)
    return frames, kps, meta


def best_rows(frames):
    """One row per frame: the box that actually contains the athlete.

    Where the top-scoring detection is NOT him - the mirror case - `top1` would
    measure the reflection, so the subject box is used and the discrepancy is
    reported separately as the subject-selection rate. Scoring the reflection
    and calling it a chirality failure would blame the pose model for the
    detector's mistake.
    """
    by_n = defaultdict(dict)
    for r in frames:
        by_n[r["n"]][r["box_source"]] = r
    out = []
    for n, d in by_n.items():
        out.append(d.get("subject_box") or d.get("top1") or d.get("none"))
    return sorted(out, key=lambda r: int(r["n"]))


def chirality_table(rows):
    buckets = defaultdict(lambda: defaultdict(int))
    for r in rows:
        buckets[r["orientation"] or "?"][r["frame_verdict"]] += 1
        buckets["ALL"][r["frame_verdict"]] += 1
    lines = ["| orientation | n | correct | swapped | inconsistent | "
             "no signal | no detection | failure rate (95% CI) |",
             "|---|---|---|---|---|---|---|---|"]
    rates = {}
    for o in ("FRONT", "PROFILE", "REAR", "ALL"):
        b = buckets.get(o)
        if not b:
            continue
        c, s, i = b["CORRECT"], b["SWAPPED"], b["INCONSISTENT"]
        scored = c + s + i
        fail = s + i
        lo, hi = wilson(fail, scored)
        rates[o] = {"scored": scored, "correct": c, "swapped": s,
                    "inconsistent": i, "no_signal": b["NO_SIGNAL"],
                    "no_detection": b["NO_DETECTION"],
                    "failure_rate": (fail / scored) if scored else float("nan"),
                    "ci": [lo, hi]}
        lines.append(
            f"| {o} | {sum(b.values())} | {c} | {s} | {i} | {b['NO_SIGNAL']} | "
            f"{b['NO_DETECTION']} | "
            + (f"{fail / scored:.1%} ({lo:.1%}-{hi:.1%}) |" if scored else "n/a |"))
    return "\n".join(lines), rates


def dispersion(group, kps, px_per_cm):
    """Noise floor for one group of repeated captures of the same pose.

    Two forms, because they answer different questions and #11 may want either:

      raw       the athlete's own drift within the group is INCLUDED. This is
                what a metric that compares absolute landmark positions between
                two captures would actually face.
      aligned   centroid and scale removed before measuring, so only shape
                disagreement remains. Rotation is NOT removed, because a torso
                rotation is signal here rather than nuisance, and reflection is
                never removed under any circumstance - allowing it would let a
                chirality failure be absorbed into the alignment and vanish.
    """
    names = [n for n in kps[next(iter(group))].keys()]
    P = np.array([[kps[k][n] for n in names] for k in group], np.float64)
    if len(P) < 3:
        return None

    def spread(A):
        c = A.mean(axis=0)
        return np.sqrt(((A - c) ** 2).sum(axis=2).mean(axis=0))   # RMS per kp

    raw = spread(P)

    Q = P - P.mean(axis=1, keepdims=True)
    scale = np.sqrt((Q ** 2).sum(axis=(1, 2)) / Q.shape[1])
    Q = Q / scale[:, None, None] * scale.mean()
    aligned = spread(Q)

    def pack(v):
        cm = v / px_per_cm if px_per_cm else None
        return {
            "median_px": float(np.median(v)), "p90_px": float(np.percentile(v, 90)),
            "median_cm": (float(np.median(cm)) if cm is not None else None),
            "p90_cm": (float(np.percentile(cm, 90)) if cm is not None else None),
            "mdc95_p90_cm": (float(np.percentile(cm, 90) * MDC_K)
                             if cm is not None else None),
            "per_kp_px": {n: float(x) for n, x in zip(names, v)},
        }

    ang = {}
    for seg, a, b in SEGMENTS:
        ia, ib = names.index(a), names.index(b)
        th = np.arctan2(P[:, ib, 1] - P[:, ia, 1], P[:, ib, 0] - P[:, ia, 0])
        # circular standard deviation, so a segment sitting near +/-180 does not
        # report a huge spread purely from the wrap
        R = np.hypot(np.cos(th).mean(), np.sin(th).mean())
        ang[seg] = float(np.degrees(np.sqrt(max(0.0, -2.0 * np.log(max(R, 1e-12))))))
    ang_vals = np.array(list(ang.values()))

    return {"n": len(P), "raw": pack(raw), "aligned": pack(aligned),
            "angles_deg": ang,
            "angle_p90_deg": float(np.percentile(ang_vals, 90)),
            "angle_mdc95_p90_deg": float(np.percentile(ang_vals, 90) * MDC_K)}


def floors(rows, kps, px_per_cm):
    """Group the repeated captures and measure dispersion within each.

    What is excluded, and what deliberately is not. NO_DETECTION goes, because
    there are no landmarks to disperse. SWAPPED and INCONSISTENT go, because a
    transposed frame would add the distance between the two wrists to the
    jitter and report it as noise - merging the two failure modes the map keeps
    separate, and inflating the floor with the very thing it is supposed to be
    measured independently of.

    NO_SIGNAL stays. It means no marker was readable, not that the pose was bad,
    and its seventeen landmarks are exactly as good as any other frame's.
    Dropping it was a bug that cost more than half of every group.
    """
    keep = ("CORRECT", "NO_SIGNAL")
    groups = defaultdict(list)
    for r in rows:
        if r["block"] in ("C", "D") and r["frame_verdict"] in keep:
            groups[(r["block"], r["pose"], r["camera"])].append(
                (r["n"], r["box_source"]))
    out = {}
    for k, members in sorted(groups.items()):
        d = dispersion(members, kps, px_per_cm)
        if d:
            out["/".join(k)] = d
    return out


def marker_effect(rows, kps, px_per_cm):
    """Does the tape move the landmark it is meant to label?

    The comparison is WITHIN a frame pair, not against the human floor: if the
    tape mattered, the marked joints would move more between the marked and
    unmarked shots than the unmarked joints do. Both sets carry the athlete's
    own re-hit noise equally, so that difference is the tape's effect and
    nothing else. Comparing the raw displacement against the human floor would
    have confounded the two, since he necessarily broke the pose to remove the
    tape.
    """
    marked = defaultdict(list)
    unmarked = {}
    for r in rows:
        # Only NO_DETECTION is disqualifying. Block E frames have the tape
        # removed, so NO_SIGNAL is their NORMAL state - excluding it emptied
        # this table completely, which is how the bug was found.
        if r["frame_verdict"] == "NO_DETECTION":
            continue
        key = (r["pose"], r["camera"])
        if r["condition"] == "unmarked":
            unmarked[key] = (r["n"], r["box_source"])
        elif r["block"] == "B":
            marked[key].append((r["n"], r["box_source"]))

    rowsout = []
    for key, u in sorted(unmarked.items()):
        if key not in marked:
            continue
        names = list(kps[u].keys())
        ref = np.array([[kps[k][n] for n in names] for k in marked[key]]).mean(axis=0)
        cur = np.array([kps[u][n] for n in names])
        d = np.linalg.norm(cur - ref, axis=1)
        m = np.array([n in MARKED for n in names])
        if not m.any() or m.all():
            continue
        rowsout.append({
            "pose": key[0], "camera": key[1],
            "marked_joint_median_px": float(np.median(d[m])),
            "unmarked_joint_median_px": float(np.median(d[~m])),
            "ratio": float(np.median(d[m]) / max(np.median(d[~m]), 1e-9)),
        })
    return rowsout


def subject_selection(rows):
    out = defaultdict(lambda: [0, 0])
    for r in rows:
        if r["top1_is_subject"] == "":
            continue
        key = f"{r['block']}/{r['orientation']}"
        out[key][1] += 1
        out[key][0] += int(r["top1_is_subject"] == "1")
    return {k: {"hit": v[0], "n": v[1], "rate": v[0] / v[1]}
            for k, v in sorted(out.items()) if v[1]}


def verdict(rates, fl):
    """The pre-registered decision rule, computed rather than narrated."""
    v = {}
    rear = rates.get("REAR", {})
    fr = rear.get("failure_rate")
    if fr is None or (isinstance(fr, float) and math.isnan(fr)):
        v["chirality"] = "NO DATA - no rear frame carried a marker signal"
    elif fr < SWAP_CONFIRM:
        v["chirality"] = (f"CONFIRMED ({fr:.1%} < {SWAP_CONFIRM:.0%}) - "
                          f"#14 proceeds on RTMPose-m")
    elif fr < SWAP_MITIGATE:
        v["chirality"] = (f"CONFIRMED WITH MITIGATION ({fr:.1%}) - the session "
                          f"script's orientation prior becomes mandatory, and "
                          f"that is a new ticket")
    else:
        v["chirality"] = (f"FAILED ({fr:.1%} >= {SWAP_MITIGATE:.0%}) - the rear "
                          f"mandatories cannot be scored on drift and #16's "
                          f"scope decision reopens")

    worst_cm, worst_deg, where = 0.0, 0.0, None
    for k, d in fl.items():
        if not k.startswith("D/"):      # the human floor is the binding one
            continue
        cm = d["raw"]["mdc95_p90_cm"]
        if cm and cm > worst_cm:
            worst_cm, where = cm, k
        worst_deg = max(worst_deg, d["angle_mdc95_p90_deg"])
    if where is None:
        v["noise_floor"] = "NO DATA - block D produced no usable group"
    else:
        ok = worst_cm < CORRECTION_CM and worst_deg < CORRECTION_DEG
        v["noise_floor"] = (
            f"{'PASS' if ok else 'FAIL'} - worst human-floor MDC95 is "
            f"{worst_cm:.2f} cm and {worst_deg:.2f} deg ({where}), against a "
            f"pre-registered {CORRECTION_CM:.0f} cm and {CORRECTION_DEG:.0f} deg. "
            + ("" if ok else "#11's metric would be reporting noise at that "
                             "resolution and must say so."))
    return v


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=os.path.join(HERE, "results"))
    args = ap.parse_args()

    frames, kps, meta = load(args.out)
    px_per_cm = meta.get("px_per_cm")
    rows = best_rows(frames)

    table, rates = chirality_table(rows)
    fl = floors(rows, kps, px_per_cm)
    me = marker_effect(rows, kps, px_per_cm)
    ss = subject_selection(rows)
    vd = verdict(rates, fl)

    L = ["# Ticket #9 - RTMPose-m on the real subject", "",
         f"Frames measured: {len(rows)}. Chirality ground truth: physical tape, "
         f"four limbs, two colours. Scale: "
         + (f"{px_per_cm:.3f} px/cm." if px_per_cm else "UNAVAILABLE - "
            "centimetre figures are absent and the pre-registered threshold "
            "cannot be applied."), "",
         "## Verdict (pre-registered, see analyse.py)", ""]
    for k, s in vd.items():
        L += [f"- **{k}**: {s}"]
    L += ["", "## Chirality, by orientation", "", table, "",
          "## Noise floors", "",
          "`C/*` is the sensor floor - a burst with no movement between frames. "
          "`D/*` is the human floor - the pose broken and re-hit. MDC95 is the "
          "change a single new capture must show before it can be called real.",
          "",
          "| group | n | raw p90 (cm) | MDC95 p90 (cm) | angle p90 (deg) | "
          "angle MDC95 (deg) |", "|---|---|---|---|---|---|"]
    for k, d in fl.items():
        r = d["raw"]
        L.append(f"| {k} | {d['n']} | "
                 + (f"{r['p90_cm']:.2f} | {r['mdc95_p90_cm']:.2f} | "
                    if r["p90_cm"] is not None else "n/a | n/a | ")
                 + f"{d['angle_p90_deg']:.2f} | {d['angle_mdc95_p90_deg']:.2f} |")

    L += ["", "## Subject selection (block F is the mirror arm)", "",
          "| block/orientation | top-1 is the athlete | n | rate |",
          "|---|---|---|---|"]
    for k, v in ss.items():
        L.append(f"| {k} | {v['hit']} | {v['n']} | {v['rate']:.1%} |")

    L += ["", "## Does the tape move the landmark it labels?", "",
          "Ratio above 1 means the marked joints moved more than the unmarked "
          "ones between the marked and unmarked shots, which is what a real "
          "tape effect would look like.", "",
          "| pose | camera | marked (px) | unmarked (px) | ratio |",
          "|---|---|---|---|---|"]
    for r in me:
        L.append(f"| {r['pose']} | {r['camera']} | "
                 f"{r['marked_joint_median_px']:.2f} | "
                 f"{r['unmarked_joint_median_px']:.2f} | {r['ratio']:.2f} |")

    md = "\n".join(L) + "\n"
    with open(os.path.join(args.out, "summary.md"), "w") as f:
        f.write(md)
    with open(os.path.join(args.out, "summary.json"), "w") as f:
        json.dump({"verdict": vd, "chirality": rates, "floors": fl,
                   "subject_selection": ss, "marker_effect": me,
                   "pre_registered": {
                       "correction_cm": CORRECTION_CM,
                       "correction_deg": CORRECTION_DEG,
                       "swap_confirm": SWAP_CONFIRM,
                       "swap_mitigate": SWAP_MITIGATE}}, f, indent=2)
    print(md)


if __name__ == "__main__":
    main()
