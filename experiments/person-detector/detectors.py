"""PROTOTYPE - throwaway. Detector adapters for wayfinder ticket #19.

Every detector runs in IMAGE mode / static single-image inference. No tracking,
no temporal smoothing - map constraint 1.

Each adapter returns, for one image, every PERSON detection it made, sorted by
the model's own score, with no score threshold applied. Thresholding is done
downstream in the analysis so the threshold can be swept rather than baked in.

Adapters return, per detection:
    box   (x0, y0, x1, y1) in the coordinates of the image passed in
    score the model's own confidence
    mask  bool HxW instance mask, or None for a box-only detector
"""

from __future__ import annotations

import os

import numpy as np

COCO80_PERSON = 0   # 'person' is class 0 in the COCO 80-class ordering


class MMDetDetector:
    """Any MMDetection model, run through mmdet.apis.inference_detector.

    Weights come from download.openmmlab.com, i.e. from the same project that
    publishes the Apache-2.0 code, not from a third-party re-upload.
    """

    def __init__(self, name: str, config: str, checkpoint: str,
                 person_class: int = COCO80_PERSON, with_mask: bool = False):
        from mmdet.apis import init_detector

        self.name = name
        self.with_mask = with_mask
        self.person_class = person_class
        self.checkpoint = checkpoint
        self.checkpoint_bytes = os.path.getsize(checkpoint)
        self._model = init_detector(config, checkpoint, device="cpu")

    def detect(self, img_rgb: np.ndarray):
        from mmdet.apis import inference_detector

        # mmdet's default test pipeline reads BGR from disk; inference_detector
        # on an ndarray applies the same normalisation, so hand it BGR.
        res = inference_detector(self._model, img_rgb[:, :, ::-1])
        inst = res.pred_instances
        labels = inst.labels.cpu().numpy()
        keep = np.where(labels == self.person_class)[0]
        boxes = inst.bboxes.cpu().numpy()[keep]
        scores = inst.scores.cpu().numpy()[keep]
        masks = None
        if self.with_mask and "masks" in inst:
            masks = inst.masks.cpu().numpy()[keep]

        order = np.argsort(-scores)
        out = []
        for rank, i in enumerate(order):
            out.append({
                "box": boxes[i].astype(np.float64),
                "score": float(scores[i]),
                "mask": (masks[i].astype(bool) if masks is not None else None),
            })
        return out


def build(name: str, ckpt_dir: str, cfg_dir: str) -> MMDetDetector:
    """Named detectors. Config paths are mmdet's own bundled configs, so the
    architecture definition and the checkpoint come from the same release."""
    import mmdet

    mim = os.path.join(os.path.dirname(mmdet.__file__), ".mim", "configs")

    if name == "rtmdet_ins_tiny":
        return MMDetDetector(
            name, os.path.join(mim, "rtmdet", "rtmdet-ins_tiny_8xb32-300e_coco.py"),
            os.path.join(ckpt_dir, "rtmdet-ins_tiny_8xb32-300e_coco_20221130_151727-ec670f7e.pth"),
            with_mask=True)
    if name == "rtmdet_ins_s":
        return MMDetDetector(
            name, os.path.join(mim, "rtmdet", "rtmdet-ins_s_8xb32-300e_coco.py"),
            os.path.join(ckpt_dir, "rtmdet-ins_s_8xb32-300e_coco_20221121_212604-fdc5d7ec.pth"),
            with_mask=True)
    if name == "rtmdet_ins_m":
        return MMDetDetector(
            name, os.path.join(mim, "rtmdet", "rtmdet-ins_m_8xb32-300e_coco.py"),
            os.path.join(ckpt_dir, "rtmdet-ins_m_8xb32-300e_coco_20221123_001039-6eba602e.pth"),
            with_mask=True)
    if name == "rtmdet_nano_person":
        # The detector MMPose's own RTMPose project recommends pairing with
        # RTMPose. Box-only, and trained on COCO + Objects365 - see the writeup,
        # Objects365 is academic-use-only. Measured as the comparison point,
        # not as a shippable candidate.
        return MMDetDetector(
            name, os.path.join(cfg_dir, "rtmdet_nano_320-8xb32_coco-person.py"),
            os.path.join(ckpt_dir, "rtmdet_nano_8xb32-100e_coco-obj365-person-05d8511e.pth"),
            person_class=0, with_mask=False)
    raise SystemExit(f"unknown detector {name}")
