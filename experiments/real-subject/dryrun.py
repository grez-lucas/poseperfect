"""PROTOTYPE - throwaway. Wayfinder ticket #9: does the harness run at all?

NOT A RESULT. Nothing this file produces says anything about RTMPose, about the
real subject, or about the noise floor. It fabricates a capture set shaped like
the shot plan out of one COCO person, runs `ingest.py`, `run_experiment.py` and
`analyse.py` over it, and checks that the whole path completes and that the
tables come out populated.

It exists because the alternative is discovering a crash, a missing column or an
empty group AFTER an athlete has held a rear double biceps eight times. The
session is expensive and not casually repeatable; this is cheap.

    python dryrun.py

Everything it writes lands in results/_dryrun/ and is gitignored.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys

import cv2
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
EXPS = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(EXPS, "rear-view"))

from cohort import build_cohort, IDX                               # noqa: E402
import shotplan                                                    # noqa: E402
from synthetic_check import TAPE_BGR                               # noqa: E402

DATA = os.path.expanduser("~/.cache/poseperfect-rearview/data")
OUT = os.path.join(HERE, "results", "_dryrun")
PHOTOS = os.path.join(OUT, "photos")
SCALE_PX_PER_CM = 2.0      # the fabricated CAL-S frame is built to this


def pick_subject():
    """One large, fully-keypointed COCO person to stand in for the athlete."""
    ann = os.path.join(DATA, "annotations", "person_keypoints_val2017.json")
    best = None
    for i in build_cohort(ann):
        kp = np.array(i.keypoints, np.float64).reshape(17, 3)
        need = [IDX[n] for n in ("left_wrist", "right_wrist",
                                 "left_ankle", "right_ankle",
                                 "left_shoulder", "right_shoulder",
                                 "left_hip", "right_hip")]
        if all(kp[j, 2] == 2 for j in need) and (best is None or i.area > best[0].area):
            best = (i, kp)
    if best is None:
        raise SystemExit("no fully-keypointed COCO person found")
    return best


def frame(img, kp, tape=True, jitter=0.0, mirror=False, rng=None):
    out = img.copy()
    if mirror:
        # A crude stand-in for a reflection: the person flipped and pasted
        # beside themselves, so the detector sees two people. Enough to exercise
        # the subject-selection code path; it is not a photograph of a mirror.
        h, w = out.shape[:2]
        wide = np.zeros((h, w * 2, 3), out.dtype)
        wide[:, :w] = out
        wide[:, w:] = cv2.flip(out, 1)
        out = wide
    if jitter and rng is not None:
        dx, dy = rng.normal(0, jitter, 2)
        M = np.float32([[1, 0, dx], [0, 1, dy]])
        out = cv2.warpAffine(out, M, (out.shape[1], out.shape[0]))
    if tape:
        r = max(3, int(round(0.030 * np.sqrt((kp[:, 0].ptp() * kp[:, 1].ptp())))))
        for side, (wj, aj) in (("L", ("left_wrist", "left_ankle")),
                               ("R", ("right_wrist", "right_ankle"))):
            for name in (wj, aj):
                c = tuple(int(v) for v in np.round(kp[IDX[name], :2]))
                cv2.circle(out, c, r, TAPE_BGR[side], -1)
    return out


def main():
    shutil.rmtree(OUT, ignore_errors=True)
    os.makedirs(PHOTOS)
    inst, kp = pick_subject()
    img = cv2.imread(os.path.join(DATA, "val2017", inst.file_name))
    print(f"stand-in subject: {inst.file_name} area={inst.area:.0f}")

    rng = np.random.default_rng(0)
    plan = shotplan.sequence()
    for r in plan:
        name = f"IMG_{r['n']:04d}.jpg"
        p = os.path.join(PHOTOS, name)
        if r["pose"] == "CAL-L" or r["pose"] == "CAL-R":
            side = r["pose"][-1]
            cv2.imwrite(p, np.full((256, 256, 3), TAPE_BGR[side], np.uint8))
            continue
        if r["pose"] == "CAL-S":
            cal = np.full((400, 600, 3), 30, np.uint8)
            for x in (150, 150 + int(100 * SCALE_PX_PER_CM)):
                cv2.circle(cal, (x, 300), 8, TAPE_BGR["L"], -1)
            cv2.imwrite(p, cal)
            continue
        # Blocks C and D get injected jitter so the dispersion code has
        # something non-degenerate to chew on. C is tighter than D on purpose,
        # mirroring the real relationship between the two floors.
        j = {"C": 1.0, "D": 4.0}.get(r["block"], 0.0)
        cv2.imwrite(p, frame(img, kp, tape=(r["condition"] != "unmarked"),
                             jitter=j, mirror=(r["block"] == "F"), rng=rng))

    py = os.path.join(EXPS, "person-detector", ".venv310", "bin", "python")
    res = os.path.join(OUT, "res")
    os.makedirs(res, exist_ok=True)

    def run(*cmd):
        print("\n$", " ".join(str(c) for c in cmd), flush=True)
        subprocess.run([py, *cmd], check=True, cwd=HERE)

    run("ingest.py", "--photos", PHOTOS, "--out", res)

    # Auto-confirm, which is the ONE step a real session must never skip: the
    # proposed mapping assumes nothing was re-shot. Here nothing was.
    import csv
    path = os.path.join(res, "shotlog.csv")
    with open(path, newline="") as f:
        rows = list(csv.DictReader(f))
        fields = list(rows[0])
    for r in rows:
        r["confirmed"] = "y"
        # The fabricated "reflection" is pasted on the right half, so the
        # stand-in athlete sits at about a quarter across. In a real session
        # these four numbers come from Lucas.
        if r["block"] == "F":
            r["subject_hint"] = "0.25"
    with open(path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)

    run("run_experiment.py", "--photos", PHOTOS, "--shotlog", path, "--out", res)
    run("analyse.py", "--out", res)

    print("\n" + "=" * 70)
    print("DRY RUN COMPLETE. The numbers above are fabricated and mean nothing.")
    print("What it proves: the path runs end to end and the tables populate.")


if __name__ == "__main__":
    main()
