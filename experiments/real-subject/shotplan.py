"""PROTOTYPE - throwaway. Wayfinder ticket #9: the canonical shot plan.

Single source of truth for what gets photographed, so `CAPTURE.md`, `ingest.py`
and `analyse.py` cannot drift apart. Print the numbered sequence with:

    python shotplan.py

The pose list and order are the IFBB Pro League eight plus the four quarter-turn
positions, per ticket #4 (`docs/research/mandatory-poses.md` section 1.5). The
names here ARE the domain's names - do not invent synonyms.
"""

from __future__ import annotations

# orientation buckets deliberately match ticket #18's cohort labels (FRONT /
# OBLIQUE / PROFILE / REAR) so that a rate measured here can be read next to
# `rear-view-experiment.md` without translation. Standing mandatories are
# square-on or in profile; nothing here is OBLIQUE.
POSES = [
    # code, domain name,                 orientation, has a facing direction
    ("FDB", "Front Double Biceps",       "FRONT",   False),
    ("FLS", "Front Lat Spread",          "FRONT",   False),
    ("SCH", "Side Chest",                "PROFILE", True),
    ("BDB", "Back Double Biceps",        "REAR",    False),
    ("BLS", "Back Lat Spread",           "REAR",    False),
    ("STR", "Side Triceps",              "PROFILE", True),
    ("ABT", "Abdominals and Thighs",     "FRONT",   False),
    ("MM",  "Most Muscular",             "FRONT",   False),
    ("QTF", "Quarter Turn Front",        "FRONT",   False),
    ("QTR", "Quarter Turn Right",        "PROFILE", True),
    ("QTB", "Quarter Turn Back",         "REAR",    False),
    ("QTL", "Quarter Turn Left",         "PROFILE", True),
]
POSE_BY_CODE = {c: (n, o, f) for c, n, o, f in POSES}

# The two poses the noise floor is measured on. One FRONT and one REAR on
# purpose: #18 measured a 30-point usable-rate gap between those buckets for
# BlazePose, so a floor quoted only on a front pose would be the flattering
# half of the answer.
FLOOR_POSES = ["FDB", "BDB"]

# Block E shoots these WITHOUT markers, to price what the tape itself does to
# the landmarks it is meant to label.
CONTROL_POSES = ["FDB", "BDB", "SCH", "QTB"]

# Block F puts the mirror in frame. Rear-facing poses first: #19's 83.7%
# top-1 hit rate was measured on rear crops.
MIRROR_POSES = ["BDB", "QTB", "FDB", "SCH"]

CAL_FRAMES = [
    ("CAL-L", "close-up of the LEFT-side tape, filling the centre of frame"),
    ("CAL-R", "close-up of the RIGHT-side tape, filling the centre of frame"),
    ("CAL-S", "the two floor marks 1.00 m apart, shot from the tripod position"),
]

SENSOR_FLOOR_N = 10   # burst, no movement between frames. Free, so take more.
HUMAN_FLOOR_N = 8     # break the pose and re-hit. Costs a physical rep each.


def blocks():
    """(block, note, [(pose_code, camera, condition, rep), ...])."""
    out = []

    out.append(("C", f"sensor floor - burst of {SENSOR_FLOOR_N}, DO NOT MOVE between frames", [
        (p, cam, "marked", r)
        for cam in ("front", "rear")
        for p in FLOOR_POSES
        for r in range(1, SENSOR_FLOOR_N + 1)
    ]))

    # Human floor is FRONT CAMERA ONLY. Reasoning recorded in CAPTURE.md: the
    # camera comparison belongs to the sensor floor, and 32 rear double biceps
    # holds would measure fatigue rather than repeatability.
    out.append(("D", f"human floor - break the pose fully and re-hit it, {HUMAN_FLOOR_N} times", [
        (p, "front", "marked", r)
        for p in FLOOR_POSES
        for r in range(1, HUMAN_FLOOR_N + 1)
    ]))

    out.append(("A", "chirality sweep, FRONT camera", [
        (c, "front", "marked", r) for c, _, _, _ in POSES for r in (1, 2)
    ]))

    out.append(("B", "chirality sweep, REAR camera", [
        (c, "rear", "marked", r) for c, _, _, _ in POSES for r in (1, 2)
    ]))

    out.append(("E", "marker control - TAPE REMOVED", [
        (c, "rear", "unmarked", 1) for c in CONTROL_POSES
    ]))

    out.append(("F", "mirror in frame - your reflection must be visible", [
        (c, "front", "marked", 1) for c in MIRROR_POSES
    ]))

    return out


def sequence():
    """Flat, numbered, in the order they should actually be shot."""
    rows = []
    n = 0
    for code, note in CAL_FRAMES:
        n += 1
        rows.append({"n": n, "block": "CAL", "pose": code, "camera": "rear",
                     "condition": "calibration", "rep": 1, "note": note})
    for block, note, shots in blocks():
        for pose, cam, cond, rep in shots:
            n += 1
            name, orient, _ = POSE_BY_CODE[pose] if pose in POSE_BY_CODE else (pose, "", False)
            rows.append({"n": n, "block": block, "pose": pose, "camera": cam,
                         "condition": cond, "rep": rep,
                         "note": f"{name} [{orient}] - {note}"})
    return rows


if __name__ == "__main__":
    rows = sequence()
    cur = None
    for r in rows:
        if r["block"] != cur:
            cur = r["block"]
            print(f"\n=== BLOCK {cur} " + "=" * 50)
        print(f"{r['n']:4d}  {r['pose']:6s} {r['camera']:5s} "
              f"{r['condition']:11s} rep {r['rep']:2d}  {r['note']}")
    print(f"\n{len(rows)} frames total "
          f"({len(CAL_FRAMES)} calibration + {len(rows) - len(CAL_FRAMES)} captures)")
