"""PROTOTYPE - throwaway. Wayfinder ticket #9: the chirality ground truth.

WHY THIS FILE EXISTS. Every measure in `experiments/rear-view/` and
`experiments/checkpoint-swap/` is a difference against COCO's annotated
keypoints. Photographs of a real athlete in his own room have no annotation, so
none of those functions can be pointed at them. Map constraint 2 closes the
obvious escape - occluded points are supervised toward a "best guess and default
pose", so a rear-view skeleton looks entirely plausible while tracking a learned
average human, and validating by eye would confirm exactly the failure we are
hunting.

So the ground truth is manufactured physically instead of by annotation:
coloured tape on all four limbs, two colours, one per anatomical side. Where the
tape is in the photograph is a fact about the photograph, not a judgement about
the model's output, and reading it costs no human labour per frame.

Consequences worth stating, because they bound what this instrument can claim:

  - It labels four joints (both wrists, both ankles), not seventeen. That is
    enough for chirality and nothing else. Chosen deliberately: ticket #18 found
    19% of rear skeletons internally inconsistent between the shoulder girdle
    and the legs, so an upper and a lower limb on each side is the minimum that
    can see that failure at all.
  - An occluded marker yields no signal. It is reported as such and never
    imputed.
  - The tape changes pixels. Block E of the shot plan shoots the same poses
    unmarked so that displacement can be priced rather than assumed away.
"""

from __future__ import annotations

import json

import cv2
import numpy as np

# COCO indices of the marked joints.
MARKED_JOINTS = {"wrist": {"L": 9, "R": 10}, "ankle": {"L": 15, "R": 16}}
OPPOSITE = {"L": "R", "R": "L"}

MIN_BLOB_FRAC = 2e-6    # of frame area; ~6 px on a 12 MP frame. Deliberately
                        # low - a wrist band seen edge-on from 3 m is small.
MERGE_FACTOR = 2.5      # merge components whose centroids are within this many
                        # blob-radii of each other (tape wraps and can split).

# Where the wrist/ankle boundary sits down the person's own detection box, used
# when only ONE marker of a side is visible and the top-versus-bottom rule has
# nothing to compare against. Most Muscular brings the hands lowest of any pose
# in the plan, to roughly 0.55 of standing height, and ankles sit at about 0.97,
# so 0.80 separates them with room on both sides. The box carries no left/right
# information, which is what keeps this from being circular: it decides WHICH
# JOINT the tape is on, never which side.
WRIST_ANKLE_SPLIT = 0.80

# Decisive margin, in units of the subject's own torso length. Below it, the
# question "is the same-side or the opposite-side keypoint nearer the tape" is
# not a real question - in a profile view the two wrists are nearly coincident
# and nearest-tape is a coin flip. Ticket #18 met the same problem and set
# DECISIVE_MARGIN = 0.05 of sqrt(COCO area) for it.
#
# CALIBRATED ON COCO, in `synthetic_check.py`, and never on the real captures.
# Choosing it from the real data afterwards would be fitting the instrument to
# the answer. Swept over 681 COCO instances (`results/synthetic_check.d*.json`):
#
#   margin  coverage   false alarm (all / REAR / PROFILE)   recall (all / REAR)
#     0.15     92.5%        1.4%  /  1.1%  /  1.2%            99.2%  /  97.8%
#     0.20     90.6%        1.0%  /  0.6%  /  0.0%            99.4%  /  98.3%
#     0.30     83.3%        0.7%  /  0.6%  /  0.0%            98.9%  /  97.5%
#
# 0.20 wins on every axis that matters: the best rear recall of the three, half
# 0.15's rear false-alarm rate, and 9 points more coverage than 0.30, which buys
# nothing for the loss. PROFILE is what forces a margin this wide at all - seen
# side-on the two wrists are nearly coincident, nearest-tape is close to a coin
# flip, and a loose margin resolves the coin flip as a swap. At 0.10, on a
# smaller sample, the profile false-alarm rate was 8.1%, which could never have
# measured #18's real 9.0%.
#
# THE LIMIT THIS LEAVES, and it must be quoted alongside any rear result: a 0.6%
# rear false-alarm rate is the same order as the 1.0% rear swap rate #18
# measured for RTMPose-m on COCO. This instrument cannot resolve a rate that
# small. It can resolve the pre-registered decision boundaries in analyse.py,
# 5% and 20%, which is what it was built for, and it must not be asked for more.
DECISIVE_TORSO_FRAC = 0.20


def _centre_patch(img_bgr, frac=0.4):
    h, w = img_bgr.shape[:2]
    y0, y1 = int(h * (1 - frac) / 2), int(h * (1 + frac) / 2)
    x0, x1 = int(w * (1 - frac) / 2), int(w * (1 + frac) / 2)
    return img_bgr[y0:y1, x0:x1]


def calibrate(cal_paths: dict) -> dict:
    """Learn each tape colour from its own close-up frame.

    `cal_paths` maps side -> path of a frame where that tape fills the centre.
    Learning the colour from the actual roll is the whole point: it means the
    protocol works with whatever tape Lucas owns, and it removes the hardcoded
    threshold that the block-E control would otherwise be auditing.
    """
    out = {}
    for side, path in cal_paths.items():
        img = cv2.imread(path)
        if img is None:
            raise SystemExit(f"cannot read calibration frame {path}")
        patch = cv2.cvtColor(_centre_patch(img), cv2.COLOR_BGR2HSV)
        # Saturated, non-dark pixels only - the close-up still contains skin,
        # shadow and floor at its edges.
        m = (patch[:, :, 1] > 90) & (patch[:, :, 2] > 60)
        if m.sum() < 200:
            raise SystemExit(f"{path}: tape does not dominate the centre of frame")
        hsv = patch[m].astype(np.float64)
        # Hue is circular, so the mean is taken on the unit circle. A magenta or
        # red tape sits astride the 0/180 wrap and a linear mean would land on
        # cyan - the exact bug that would make the instrument silently useless.
        ang = hsv[:, 0] * (2 * np.pi / 180.0)
        hue = (np.arctan2(np.sin(ang).mean(), np.cos(ang).mean())
               * 180.0 / (2 * np.pi)) % 180.0
        dh = np.abs(((hsv[:, 0] - hue + 90) % 180) - 90)
        out[side] = {
            "hue": float(hue),
            "hue_tol": float(max(8.0, np.percentile(dh, 95) * 1.5)),
            "sat_min": float(max(70.0, np.percentile(hsv[:, 1], 5) * 0.7)),
            "val_min": float(max(50.0, np.percentile(hsv[:, 2], 5) * 0.7)),
            "n_px": int(m.sum()),
            "source": path,
        }
    _check_separable(out)
    return out


def _check_separable(calib):
    """Refuse two colours the instrument cannot tell apart.

    If the hue windows overlap, every marker reading is a coin flip and every
    downstream chirality number is meaningless. Better to fail here than to
    publish a swap rate that is really a colour-threshold artefact.
    """
    if set(calib) != {"L", "R"}:
        return
    a, b = calib["L"], calib["R"]
    sep = abs(((a["hue"] - b["hue"] + 90) % 180) - 90)
    if sep < a["hue_tol"] + b["hue_tol"]:
        raise SystemExit(
            f"tape colours are not separable: hues {a['hue']:.1f} and "
            f"{b['hue']:.1f} differ by {sep:.1f} but tolerances sum to "
            f"{a['hue_tol'] + b['hue_tol']:.1f}. Use two more distant colours.")


def _blobs(img_bgr, spec, min_area):
    hsv = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2HSV)
    dh = np.abs(((hsv[:, :, 0].astype(np.int16) - spec["hue"] + 90) % 180) - 90)
    mask = ((dh <= spec["hue_tol"]) &
            (hsv[:, :, 1] >= spec["sat_min"]) &
            (hsv[:, :, 2] >= spec["val_min"])).astype(np.uint8)
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))
    n, _, stats, cent = cv2.connectedComponentsWithStats(mask, 8)

    found = []
    for i in range(1, n):
        area = int(stats[i, cv2.CC_STAT_AREA])
        if area < min_area:
            continue
        found.append({"xy": cent[i].astype(np.float64), "area": area,
                      "w": int(stats[i, cv2.CC_STAT_WIDTH]),
                      "h": int(stats[i, cv2.CC_STAT_HEIGHT])})

    # Tape wraps around a limb and is routinely split into two components by a
    # highlight or by the limb's own edge. Merge what is obviously one band.
    merged = []
    for b in sorted(found, key=lambda d: -d["area"]):
        for m in merged:
            r = np.sqrt(m["area"] / np.pi) + np.sqrt(b["area"] / np.pi)
            if np.linalg.norm(m["xy"] - b["xy"]) < MERGE_FACTOR * r:
                tot = m["area"] + b["area"]
                m["xy"] = (m["xy"] * m["area"] + b["xy"] * b["area"]) / tot
                m["area"] = tot
                m["w"], m["h"] = max(m["w"], b["w"]), max(m["h"], b["h"])
                break
        else:
            merged.append(b)
    return merged


def find(img_bgr, calib, person_box=None, restrict_box=None) -> list:
    """Locate every marker in one frame.

    Returns dicts with side, joint, pixel centroid and the blob's own width,
    which downstream feeds the indecision margin.

    Wrist versus ankle is assigned by height, which is safe for every pose in
    the plan: a standing human's wrist is above their ankle in all eight
    mandatories and all four quarter turns, including Most Muscular, where the
    hands come down to the waist and no lower. When both markers of a side are
    visible that is a direct comparison. When only one is - a hand hidden behind
    the back in a rear lat spread, a far ankle behind the near leg in profile -
    it is resolved against the person's own detection box instead of being
    thrown away, which is what `person_box` is for. Without a box such a marker
    stays `unassigned` and contributes nothing rather than guessing.

    `restrict_box` discards blobs outside it BEFORE the per-side cap of two.
    Block F is why it exists: a reflection wears the same tape on the same
    limbs, so a mirrored frame contains four blobs per colour and the two
    largest are not necessarily the athlete's. Without this the mirror arm would
    silently score chirality against a mixture of a man and his reflection.
    """
    min_area = MIN_BLOB_FRAC * img_bgr.shape[0] * img_bgr.shape[1]
    out = []
    for side, spec in calib.items():
        blobs = _blobs(img_bgr, spec, min_area)
        if restrict_box is not None:
            blobs = [b for b in blobs
                     if restrict_box[0] <= b["xy"][0] <= restrict_box[2]
                     and restrict_box[1] <= b["xy"][1] <= restrict_box[3]]
        blobs = sorted(blobs, key=lambda d: -d["area"])[:2]
        if not blobs:
            continue
        blobs.sort(key=lambda d: d["xy"][1])          # top of frame first
        if len(blobs) == 2:
            joints = ["wrist", "ankle"]
        elif person_box is not None:
            y0, y1 = person_box[1], person_box[3]
            rel = (blobs[0]["xy"][1] - y0) / max(y1 - y0, 1e-9)
            joints = ["ankle" if rel >= WRIST_ANKLE_SPLIT else "wrist"]
        else:
            joints = ["unassigned"]
        for joint, b in zip(joints, blobs):
            out.append({"side": side, "joint": joint, "xy": b["xy"],
                        "area": b["area"], "width_px": float(max(b["w"], b["h"]))})
    return out


def score_chirality(markers, kps, torso_px):
    """Score one frame's markers against one set of predicted keypoints.

    THE RULE, fixed before any photograph was taken. For a marker of known side
    S on joint J, compare the distance from the tape to the model's S-side J
    against the distance to its opposite-side J:

        CORRECT    the same-side keypoint is nearer
        SWAPPED    the opposite-side keypoint is nearer
        AMBIGUOUS  the two are within half the tape's own width of each other
        GROSS_MISS neither keypoint is anywhere near the tape

    AMBIGUOUS and GROSS_MISS are buckets, not tie-breaks. Resolving either one
    in the engine's favour would be the confidence-gating mistake of ticket #18
    wearing different clothes, and it is the single easiest way to make a broken
    engine look fine.
    """
    rows = []
    for m in markers:
        if m["joint"] == "unassigned":
            rows.append(dict(m, verdict="UNASSIGNED", d_ipsi=np.nan, d_contra=np.nan))
            continue
        i_ipsi = MARKED_JOINTS[m["joint"]][m["side"]]
        i_contra = MARKED_JOINTS[m["joint"]][OPPOSITE[m["side"]]]
        d_i = float(np.linalg.norm(kps[i_ipsi] - m["xy"]))
        d_c = float(np.linalg.norm(kps[i_contra] - m["xy"]))
        margin = max(0.5 * m["width_px"], DECISIVE_TORSO_FRAC * torso_px)
        if min(d_i, d_c) > 0.25 * torso_px:
            v = "GROSS_MISS"
        elif abs(d_i - d_c) < margin:
            v = "AMBIGUOUS"
        elif d_c < d_i:
            v = "SWAPPED"
        else:
            v = "CORRECT"
        rows.append(dict(m, verdict=v, d_ipsi=d_i, d_contra=d_c))
    return rows


def frame_verdict(rows):
    """Roll per-limb verdicts up to the frame.

    INCONSISTENT is reported separately from SWAPPED on purpose. Ticket #18
    found 19% of rear skeletons transposed in the shoulders but not the legs,
    and recorded that no orientation gate can repair that class - a global flip
    is in principle correctable, a piecewise one is not. Merging the two would
    hide the difference that decides whether a mitigation is even possible.
    """
    v = [r["verdict"] for r in rows if r["verdict"] in ("CORRECT", "SWAPPED")]
    if not v:
        return "NO_SIGNAL"
    if all(x == "SWAPPED" for x in v):
        return "SWAPPED"
    if all(x == "CORRECT" for x in v):
        return "CORRECT"
    return "INCONSISTENT"


def load(path):
    with open(path) as f:
        return json.load(f)


def save(calib, path):
    with open(path, "w") as f:
        json.dump(calib, f, indent=2)
