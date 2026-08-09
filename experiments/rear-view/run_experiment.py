"""PROTOTYPE - throwaway. Wayfinder ticket #18: settle the rear-view question offline.

Runs candidate pose engines over a COCO val2017 cohort bucketed by a
visibility-derived orientation proxy, and scores TWO SEPARATE failure modes:

  positional error  - OKS / PCK against ground-truth keypoints, measured
                      AFTER correcting chirality. Tolerable if systematic,
                      because systematic bias cancels when an athlete is
                      compared against their own earlier reference.

  chirality error   - whether the engine's `left_shoulder` corresponds to the
                      anatomical left shoulder. Fatal, because it is bimodal
                      rather than systematic: a coin flip between two
                      interpretations destroys self-referential comparison in
                      a way a consistent offset never does.

These are never merged into one accuracy number.

Writes one row per (instance, engine) to results/per_instance.csv.

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

from cohort import (build_cohort, BODY_PAIRS, ALL_PAIRS, OKS_SIGMAS, IDX,
                    COCO_KP_NAMES)

# Chirality is also decided independently per limb group, to answer whether a
# rear-view failure is a COHERENT global mirror (in principle correctable by
# flipping every label) or a PIECEWISE one (not correctable by anything).
GROUPS = {
    "shoulders": [(5, 6)],
    "hips": [(11, 12)],
    "arms": [(7, 8), (9, 10)],
    "legs": [(13, 14), (15, 16)],
}

CROP_PAD = 1.25   # square crop = 1.25 x the longer bbox side, centred on the
                  # bbox. Stands in for the product's constrained, frame-fit
                  # gated capture (map decisions 8 and 14) rather than for
                  # in-the-wild detection.

# Threshold on the chirality margin, in units of sqrt(COCO area), below which
# we call the identity-vs-swap decision indecisive rather than a swap.
DECISIVE_MARGIN = 0.05


def mirror_index_map():
    """COCO index -> its left/right mirror index (identity for the nose)."""
    m = list(range(17))
    for a, b in ALL_PAIRS:
        m[a], m[b] = b, a
    return np.array(m)


MIRROR = mirror_index_map()


def make_crop(img, bbox):
    """Square crop around the GT bbox, black-padded at image edges."""
    x, y, w, h = bbox
    cx, cy = x + w / 2.0, y + h / 2.0
    side = max(w, h) * CROP_PAD
    x0, y0 = cx - side / 2.0, cy - side / 2.0
    s = int(round(side))
    xi, yi = int(round(x0)), int(round(y0))

    out = np.zeros((s, s, 3), img.dtype)
    sx0, sy0 = max(0, xi), max(0, yi)
    sx1, sy1 = min(img.shape[1], xi + s), min(img.shape[0], yi + s)
    if sx1 > sx0 and sy1 > sy0:
        out[sy0 - yi:sy1 - yi, sx0 - xi:sx1 - xi] = img[sy0:sy1, sx0:sx1]
    # GT bbox expressed in crop coordinates, for engines that take a box.
    box_in_crop = [x - xi, y - yi, w, h]
    return out, float(xi), float(yi), box_in_crop


def gt_arrays(inst):
    kp = np.array(inst.keypoints, np.float64).reshape(17, 3)
    return kp[:, :2], kp[:, 2].astype(int)


def oks(pred_xy, gt_xy, vis, area, min_v=2):
    """COCO OKS over ground-truth keypoints at visibility >= min_v."""
    sel = np.where(vis >= min_v)[0]
    if len(sel) == 0:
        return float("nan"), 0
    d2 = ((pred_xy[sel] - gt_xy[sel]) ** 2).sum(axis=1)
    k = np.array(OKS_SIGMAS)[sel] * 2.0
    e = d2 / (k ** 2) / (area + np.spacing(1)) / 2.0
    return float(np.exp(-e).mean()), len(sel)


def pck(pred_xy, gt_xy, vis, area, alpha=0.2, min_v=2):
    """PCK@alpha with the reference length sqrt(COCO segmentation area)."""
    sel = np.where(vis >= min_v)[0]
    if len(sel) == 0:
        return float("nan"), 0
    d = np.linalg.norm(pred_xy[sel] - gt_xy[sel], axis=1)
    thr = alpha * np.sqrt(area)
    return float((d < thr).mean()), len(sel)


def chirality(pred_xy, gt_xy, vis, area, pairs):
    """Compare the identity assignment against the left/right-swapped one.

    Scored only on ground-truth keypoints at v == 2 that belong to `pairs`,
    so both hypotheses are scored on exactly the same target set. Distances
    are normalised by sqrt(COCO area).

    Returns (d_identity, d_swapped, n_scored).
    """
    idxs = [i for p in pairs for i in p if vis[i] == 2 and
            all(vis[j] == 2 for j in p)]
    if len(idxs) < 2:
        return float("nan"), float("nan"), 0
    idxs = np.array(idxs)
    s = np.sqrt(area) + np.spacing(1)
    d_id = np.linalg.norm(pred_xy[idxs] - gt_xy[idxs], axis=1).mean() / s
    d_sw = np.linalg.norm(pred_xy[MIRROR[idxs]] - gt_xy[idxs], axis=1).mean() / s
    return float(d_id), float(d_sw), len(idxs)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", default=os.path.expanduser(
        "~/.cache/poseperfect-rearview/data"))
    ap.add_argument("--models", default=os.path.expanduser(
        "~/.cache/poseperfect-rearview/models"))
    ap.add_argument("--out", default=os.path.join(os.path.dirname(__file__), "results"))
    ap.add_argument("--limit", type=int, default=0, help="0 = whole cohort")
    ap.add_argument("--engines", default="blazepose_heavy,blazepose_full,movenet_thunder,rtmpose_m")
    args = ap.parse_args()

    os.makedirs(args.out, exist_ok=True)
    ann = os.path.join(args.data, "annotations", "person_keypoints_val2017.json")
    imdir = os.path.join(args.data, "val2017")

    cohort = build_cohort(ann)
    if args.limit:
        # Stratified head of each bucket, so a smoke run still covers REAR.
        per = {}
        keep = []
        for i in cohort:
            per.setdefault(i.orientation, 0)
            if per[i.orientation] < args.limit:
                per[i.orientation] += 1
                keep.append(i)
        cohort = keep
    print(f"cohort: {len(cohort)} instances", flush=True)

    from engines import BlazePose, MoveNetThunder, RTMPose
    wanted = args.engines.split(",")
    engines = []
    for w in wanted:
        if w == "blazepose_heavy":
            engines.append(BlazePose(os.path.join(args.models, "pose_landmarker_heavy.task")))
        elif w == "blazepose_full":
            engines.append(BlazePose(os.path.join(args.models, "pose_landmarker_full.task")))
        elif w == "movenet_thunder":
            engines.append(MoveNetThunder(os.path.join(
                args.models, "movenet_singlepose_thunder.tflite")))
        elif w == "rtmpose_m":
            engines.append(RTMPose())
        else:
            sys.exit(f"unknown engine {w}")
    print("engines:", [e.name for e in engines], flush=True)

    fields = [
        "ann_id", "image_id", "file_name", "orientation", "face_visible",
        "ears_visible", "num_keypoints", "area", "bbox_h", "gt_shoulder_sign",
        "engine", "detected",
        "oks_raw", "oks_corrected", "pck02_raw", "pck02_corrected", "n_scored",
        "d_identity", "d_swapped", "n_chir", "chirality_swapped", "chirality_margin",
        "pred_shoulder_sign", "shoulder_sign_correct",
        "swap_shoulders", "swap_hips", "swap_arms", "swap_legs",
        "n_groups_decided", "n_groups_swapped",
        "conf_nose", "conf_eyes", "conf_shoulders", "conf_mean",
        "presence_nose", "presence_mean",
    ]
    path = os.path.join(args.out, "per_instance.csv")
    kp_path = os.path.join(args.out, "predictions.jsonl")
    kpf = open(kp_path, "w")
    t0 = time.time()
    n = 0
    with open(path, "w", newline="") as f:
        wr = csv.DictWriter(f, fieldnames=fields)
        wr.writeheader()
        for inst in cohort:
            img = cv2.imread(os.path.join(imdir, inst.file_name))
            if img is None:
                continue
            img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            crop, ox, oy, box_in_crop = make_crop(img, inst.bbox)
            gxy, gv = gt_arrays(inst)

            for eng in engines:
                row = {
                    "ann_id": inst.ann_id, "image_id": inst.image_id,
                    "file_name": inst.file_name, "orientation": inst.orientation,
                    "face_visible": inst.face_visible, "ears_visible": inst.ears_visible,
                    "num_keypoints": inst.num_keypoints, "area": f"{inst.area:.1f}",
                    "bbox_h": f"{inst.bbox[3]:.1f}",
                    "gt_shoulder_sign": inst.gt_shoulder_sign,
                    "engine": eng.name, "detected": 0,
                }
                try:
                    res = eng.infer(crop, box_in_crop)
                except Exception as exc:                      # keep the sweep alive
                    print("infer error", inst.ann_id, eng.name, exc, flush=True)
                    res = None
                if res is None:
                    wr.writerow(row)
                    continue

                pxy = res["xy"] + np.array([ox, oy])           # back to image coords
                conf, pres = res["conf"], res["presence"]

                d_id, d_sw, n_ch = chirality(pxy, gxy, gv, inst.area, BODY_PAIRS)
                swapped = int(np.isfinite(d_sw) and d_sw < d_id)
                margin = (d_id - d_sw) if np.isfinite(d_sw) else float("nan")
                cxy = pxy[MIRROR] if swapped else pxy

                o_raw, n_s = oks(pxy, gxy, gv, inst.area)
                o_cor, _ = oks(cxy, gxy, gv, inst.area)
                p_raw, _ = pck(pxy, gxy, gv, inst.area)
                p_cor, _ = pck(cxy, gxy, gv, inst.area)

                grp = {}
                for gname, gpairs in GROUPS.items():
                    gi, gs, gn = chirality(pxy, gxy, gv, inst.area, gpairs)
                    grp["swap_" + gname] = (int(gs < gi) if gn >= 2 else "")
                decided = [v for v in grp.values() if v != ""]
                row.update(grp)
                row["n_groups_decided"] = len(decided)
                row["n_groups_swapped"] = sum(decided)

                dx = pxy[IDX["right_shoulder"], 0] - pxy[IDX["left_shoulder"], 0]
                psign = 1 if dx > 0 else (-1 if dx < 0 else 0)

                row.update({
                    "detected": 1,
                    "oks_raw": f"{o_raw:.6f}", "oks_corrected": f"{o_cor:.6f}",
                    "pck02_raw": f"{p_raw:.6f}", "pck02_corrected": f"{p_cor:.6f}",
                    "n_scored": n_s,
                    "d_identity": f"{d_id:.6f}", "d_swapped": f"{d_sw:.6f}",
                    "n_chir": n_ch, "chirality_swapped": swapped,
                    "chirality_margin": f"{margin:.6f}",
                    "pred_shoulder_sign": psign,
                    "shoulder_sign_correct": int(psign == inst.gt_shoulder_sign),
                    "conf_nose": f"{conf[IDX['nose']]:.6f}",
                    "conf_eyes": f"{np.mean(conf[[IDX['left_eye'], IDX['right_eye']]]):.6f}",
                    "conf_shoulders": f"{np.mean(conf[[IDX['left_shoulder'], IDX['right_shoulder']]]):.6f}",
                    "conf_mean": f"{np.mean(conf):.6f}",
                    "presence_nose": f"{pres[IDX['nose']]:.6f}",
                    "presence_mean": f"{np.nanmean(pres):.6f}" if np.isfinite(pres).any() else "",
                })
                wr.writerow(row)
                kpf.write(json.dumps({
                    "ann_id": inst.ann_id, "engine": eng.name,
                    "xy_image": [[round(float(a), 2), round(float(b), 2)]
                                 for a, b in pxy],
                    "conf": [round(float(c), 4) for c in conf],
                }) + "\n")
            n += 1
            if n % 100 == 0:
                print(f"{n}/{len(cohort)}  {time.time()-t0:.0f}s", flush=True)

    kpf.close()
    meta = {
        "dataset": "COCO val2017 person keypoints",
        "mebow_status": "access-gated (email request, educational address); fallback used",
        "cohort_size": len(cohort),
        "crop_pad": CROP_PAD,
        "decisive_margin": DECISIVE_MARGIN,
        "engines": [e.name for e in engines],
        "mode": "IMAGE / static single-image inference only",
        "seconds": round(time.time() - t0, 1),
    }
    with open(os.path.join(args.out, "run_meta.json"), "w") as f:
        json.dump(meta, f, indent=2)
    print(json.dumps(meta, indent=2))


if __name__ == "__main__":
    main()
