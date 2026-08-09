"""PROTOTYPE - throwaway. Engine adapters for wayfinder ticket #18.

Every engine runs in IMAGE mode / static single-image inference. No VIDEO,
no LIVE_STREAM, no tracking, no smoothing - research established those modes
are non-deterministic and let a wrong front/back interpretation latch via the
ROI feedback loop.

Each adapter returns keypoints remapped into the COCO 17-keypoint schema in
CROP pixel coordinates, plus a per-keypoint confidence and a detected flag.
"""

from __future__ import annotations

import numpy as np

# BlazePose 33-landmark index -> COCO 17 index.
BLAZEPOSE_TO_COCO = [
    0,   # nose
    2,   # left_eye
    5,   # right_eye
    7,   # left_ear
    8,   # right_ear
    11,  # left_shoulder
    12,  # right_shoulder
    13,  # left_elbow
    14,  # right_elbow
    15,  # left_wrist
    16,  # right_wrist
    23,  # left_hip
    24,  # right_hip
    25,  # left_knee
    26,  # right_knee
    27,  # left_ankle
    28,  # right_ankle
]


class BlazePose:
    """MediaPipe Pose Landmarker, Tasks API, RunningMode.IMAGE.

    CAVEAT recorded in the writeup: this is MediaPipe, not ML Kit. Both are
    BlazePose-derived and share the face-anchored person detector, but they
    are not the same binary. ML Kit cannot run on Linux.
    """

    def __init__(self, model_path: str, det_conf: float = 0.5, presence_conf: float = 0.5):
        import mediapipe as mp
        from mediapipe.tasks.python import vision, BaseOptions

        self._mp = mp
        self.name = "blazepose_" + model_path.rsplit("_", 1)[-1].split(".")[0]
        opts = vision.PoseLandmarkerOptions(
            base_options=BaseOptions(model_asset_path=model_path),
            running_mode=vision.RunningMode.IMAGE,
            num_poses=1,
            min_pose_detection_confidence=det_conf,
            min_pose_presence_confidence=presence_conf,
            min_tracking_confidence=0.5,
            output_segmentation_masks=False,
        )
        self._lm = vision.PoseLandmarker.create_from_options(opts)

    def infer(self, crop_rgb: np.ndarray, bbox_xywh=None):
        h, w = crop_rgb.shape[:2]
        img = self._mp.Image(image_format=self._mp.ImageFormat.SRGB,
                             data=np.ascontiguousarray(crop_rgb))
        res = self._lm.detect(img)
        if not res.pose_landmarks:
            return None
        lms = res.pose_landmarks[0]
        xy = np.zeros((17, 2), np.float64)
        conf = np.zeros(17, np.float64)
        presence = np.zeros(17, np.float64)
        for coco_i, bp_i in enumerate(BLAZEPOSE_TO_COCO):
            lm = lms[bp_i]
            xy[coco_i] = (lm.x * w, lm.y * h)
            conf[coco_i] = getattr(lm, "visibility", float("nan"))
            presence[coco_i] = getattr(lm, "presence", float("nan"))
        return {"xy": xy, "conf": conf, "presence": presence}


class MoveNetThunder:
    """MoveNet SinglePose Thunder, TFLite float16.

    CenterNet-style: a single-shot keypoint regressor with a person-centre
    heatmap. No face anchor and no separate person detector, which is exactly
    why it is the control for the architecture hypothesis. Apache-2.0.

    Always returns 17 keypoints - it has no abstain path, so `detected` is
    always True. That asymmetry against BlazePose is itself a finding.
    """

    name = "movenet_thunder"
    INPUT = 256

    def __init__(self, model_path: str):
        from ai_edge_litert.interpreter import Interpreter
        self._it = Interpreter(model_path=model_path, num_threads=4)
        self._it.allocate_tensors()
        self._in = self._it.get_input_details()[0]
        self._out = self._it.get_output_details()[0]

    def infer(self, crop_rgb: np.ndarray, bbox_xywh=None):
        import cv2
        h, w = crop_rgb.shape[:2]
        resized = cv2.resize(crop_rgb, (self.INPUT, self.INPUT), interpolation=cv2.INTER_LINEAR)
        if self._in["dtype"] == np.float32:
            inp = resized.astype(np.float32)[None, ...]
        else:
            inp = resized.astype(self._in["dtype"])[None, ...]
        self._it.set_tensor(self._in["index"], inp)
        self._it.invoke()
        out = self._it.get_tensor(self._out["index"])[0, 0]   # (17, 3) as y, x, score
        xy = np.stack([out[:, 1] * w, out[:, 0] * h], axis=1).astype(np.float64)
        return {"xy": xy, "conf": out[:, 2].astype(np.float64),
                "presence": np.full(17, np.nan)}


RTMPOSE_M_BODY7 = (
    "https://download.openmmlab.com/mmpose/v1/projects/rtmposev1/onnx_sdk/"
    "rtmpose-m_simcc-body7_pt-body7_420e-256x192-e48f03d0_20230504.zip"
)


class RTMPose:
    """RTMPose-m (body7, COCO-17) via ONNX Runtime, through rtmlib. Apache-2.0.

    Third engine. Top-down like BlazePose, but its ROI comes from a general
    object detector and the model has no face anchor of any kind - the pose
    head is a SimCC coordinate classifier over the whole crop. Run here with
    ground-truth boxes, so only the pose head is under test. That makes its
    numbers an upper bound, not a deployable figure.

    Decoding is delegated to rtmlib rather than hand-rolled, so the SimCC
    split ratio and the top-down affine are the reference implementation's.
    """

    name = "rtmpose_m"

    def __init__(self, onnx_model: str = RTMPOSE_M_BODY7, input_size=(192, 256)):
        from rtmlib import RTMPose as _RTMPose
        self._m = _RTMPose(onnx_model=onnx_model, model_input_size=input_size,
                           backend="onnxruntime", device="cpu")

    def infer(self, crop_rgb: np.ndarray, bbox_xywh=None):
        h, w = crop_rgb.shape[:2]
        if bbox_xywh is None:
            box = [0.0, 0.0, float(w), float(h)]
        else:
            x, y, bw, bh = bbox_xywh
            box = [x, y, x + bw, y + bh]
        kps, scores = self._m(crop_rgb, bboxes=[box])
        xy = np.asarray(kps[0], np.float64)
        conf = np.asarray(scores[0], np.float64)
        return {"xy": xy, "conf": conf, "presence": np.full(len(xy), np.nan)}
