"""PROTOTYPE - throwaway. Cohort construction for wayfinder ticket #18.

Builds the evaluation cohort from COCO val2017 person keypoint annotations.

COCO-MEBOW (the first-choice dataset, hand-annotated body orientation at
5-degree resolution) is access-gated: ChenyanWu/MEBOW requires an email
request to czw390@psu.edu from an educational address. We therefore use the
designated fallback - COCO val2017 - and derive a PROXY orientation label
from the per-keypoint visibility flags.

COCO visibility semantics (official):
  v=0  not labelled (and not visible)
  v=1  labelled but not visible (occluded)
  v=2  labelled and visible

Proxy orientation label
-----------------------
`face_visible` = number of {nose, left_eye, right_eye} with v == 2.

  face_visible == 3  -> FRONT   (front-facing control)
  face_visible == 2  -> OBLIQUE
  face_visible == 1  -> PROFILE
  face_visible == 0  -> REAR    (rear-facing candidate)

Every instance in the cohort additionally requires both shoulders and both
hips at v == 2, so the torso is fully annotated in all buckets and the
chirality test always has ground truth to score against.

What this proxy does NOT establish: it is not a body-orientation angle. A
front-facing person whose face is occluded by an object, a hand, or motion
blur also lands in REAR. See the writeup for the independent check that
bounds this contamination.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, asdict

COCO_KP_NAMES = [
    "nose", "left_eye", "right_eye", "left_ear", "right_ear",
    "left_shoulder", "right_shoulder", "left_elbow", "right_elbow",
    "left_wrist", "right_wrist", "left_hip", "right_hip",
    "left_knee", "right_knee", "left_ankle", "right_ankle",
]
IDX = {n: i for i, n in enumerate(COCO_KP_NAMES)}

# Left/right pairs, COCO indices.
FACE_PAIRS = [(1, 2), (3, 4)]                       # eyes, ears
BODY_PAIRS = [(5, 6), (7, 8), (9, 10),              # shoulders, elbows, wrists
              (11, 12), (13, 14), (15, 16)]         # hips, knees, ankles
ALL_PAIRS = FACE_PAIRS + BODY_PAIRS

# COCO OKS per-keypoint sigmas, in COCO_KP_NAMES order.
OKS_SIGMAS = [
    .026, .025, .025, .035, .035, .079, .079, .072, .072,
    .062, .062, .107, .107, .087, .087, .089, .089,
]

# Cohort filters. Deliberately generous on pose difficulty and strict on
# things that would make the crop ambiguous (crowds, overlapping people,
# unresolvably small instances).
MIN_BBOX_HEIGHT = 100      # px, in the source image
MIN_NUM_KEYPOINTS = 8      # labelled keypoints on the instance
MAX_NEIGHBOUR_CONTAINMENT = 0.35   # fraction of another person's bbox inside ours

ORIENTATION_BY_FACE_VISIBLE = {3: "FRONT", 2: "OBLIQUE", 1: "PROFILE", 0: "REAR"}


@dataclass
class Instance:
    ann_id: int
    image_id: int
    file_name: str
    bbox: list          # COCO xywh, source-image pixels
    area: float         # COCO segmentation area, used as OKS scale
    keypoints: list     # flat COCO triplets x,y,v (51 values)
    num_keypoints: int
    face_visible: int
    orientation: str
    ears_visible: int
    gt_shoulder_sign: int   # sign(right_shoulder.x - left_shoulder.x), +1 => facing away

    def to_row(self):
        d = asdict(self)
        d.pop("keypoints")
        d["bbox"] = ",".join(f"{v:.1f}" for v in self.bbox)
        return d


def _containment(a, b):
    """Fraction of bbox b's area that lies inside bbox a. xywh."""
    ax, ay, aw, ah = a
    bx, by, bw, bh = b
    ix = max(0.0, min(ax + aw, bx + bw) - max(ax, bx))
    iy = max(0.0, min(ay + ah, by + bh) - max(ay, by))
    inter = ix * iy
    barea = bw * bh
    return inter / barea if barea > 0 else 0.0


def build_cohort(ann_path: str) -> list[Instance]:
    with open(ann_path) as f:
        coco = json.load(f)

    images = {im["id"]: im for im in coco["images"]}
    by_image: dict[int, list] = {}
    for ann in coco["annotations"]:
        by_image.setdefault(ann["image_id"], []).append(ann)

    out: list[Instance] = []
    for image_id, anns in by_image.items():
        person_boxes = [a["bbox"] for a in anns]
        for ann in anns:
            if ann.get("iscrowd", 0):
                continue
            if ann.get("num_keypoints", 0) < MIN_NUM_KEYPOINTS:
                continue
            x, y, w, h = ann["bbox"]
            if h < MIN_BBOX_HEIGHT or w <= 0:
                continue

            kp = ann["keypoints"]
            v = kp[2::3]

            # Torso must be fully visible: shoulders and hips at v == 2.
            if not all(v[i] == 2 for i in (IDX["left_shoulder"], IDX["right_shoulder"],
                                           IDX["left_hip"], IDX["right_hip"])):
                continue

            # No other annotated person substantially inside our crop region.
            worst = 0.0
            for ob in person_boxes:
                if ob is ann["bbox"]:
                    continue
                worst = max(worst, _containment(ann["bbox"], ob))
            if worst > MAX_NEIGHBOUR_CONTAINMENT:
                continue

            face_visible = sum(1 for i in (IDX["nose"], IDX["left_eye"], IDX["right_eye"])
                               if v[i] == 2)
            ears_visible = sum(1 for i in (IDX["left_ear"], IDX["right_ear"]) if v[i] == 2)

            lsx = kp[IDX["left_shoulder"] * 3]
            rsx = kp[IDX["right_shoulder"] * 3]
            sign = 1 if rsx > lsx else (-1 if rsx < lsx else 0)

            out.append(Instance(
                ann_id=ann["id"], image_id=image_id,
                file_name=images[image_id]["file_name"],
                bbox=[float(x), float(y), float(w), float(h)],
                area=float(ann["area"]), keypoints=kp,
                num_keypoints=ann["num_keypoints"],
                face_visible=face_visible,
                orientation=ORIENTATION_BY_FACE_VISIBLE[face_visible],
                ears_visible=ears_visible,
                gt_shoulder_sign=sign,
            ))
    out.sort(key=lambda i: i.ann_id)
    return out


if __name__ == "__main__":
    import sys
    from collections import Counter
    c = build_cohort(sys.argv[1])
    print(f"cohort size: {len(c)}")
    print("by orientation:", dict(Counter(i.orientation for i in c)))
    print("REAR by gt_shoulder_sign:",
          dict(Counter(i.gt_shoulder_sign for i in c if i.orientation == "REAR")))
    print("FRONT by gt_shoulder_sign:",
          dict(Counter(i.gt_shoulder_sign for i in c if i.orientation == "FRONT")))
