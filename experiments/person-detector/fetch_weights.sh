#!/usr/bin/env bash
# PROTOTYPE - throwaway. Fetches the OFFICIAL OpenMMLab checkpoints for
# wayfinder ticket #19, straight from download.openmmlab.com, so provenance is
# first-party rather than a third-party re-upload.
set -euo pipefail

CACHE="${HOME}/.cache/poseperfect-detector"
CKPT="${CACHE}/checkpoints"
mkdir -p "${CKPT}"

BASE=https://download.openmmlab.com/mmdetection/v3.0/rtmdet

get() {  # url
  local url="$1" name
  name="$(basename "${url}")"
  [ -f "${CKPT}/${name}" ] || wget -q -c -O "${CKPT}/${name}" "${url}"
  echo "  $(du -h "${CKPT}/${name}" | cut -f1)  ${name}"
}

echo "==> RTMDet-Ins (instance segmentation, COCO-only training) - MMDetection, Apache-2.0"
get "${BASE}/rtmdet-ins_tiny_8xb32-300e_coco/rtmdet-ins_tiny_8xb32-300e_coco_20221130_151727-ec670f7e.pth"
get "${BASE}/rtmdet-ins_s_8xb32-300e_coco/rtmdet-ins_s_8xb32-300e_coco_20221121_212604-fdc5d7ec.pth"
get "${BASE}/rtmdet-ins_m_8xb32-300e_coco/rtmdet-ins_m_8xb32-300e_coco_20221123_001039-6eba602e.pth"

echo "==> RTMDet-nano person detector - the one MMPose's RTMPose project recommends."
echo "    Box-only, and trained on COCO + Objects365, which is academic-use-only."
echo "    Measured here as the comparison point, NOT as a shippable candidate."
[ -f "${CKPT}/rtmdet_nano_8xb32-100e_coco-obj365-person-05d8511e.pth" ] || \
  wget -q -c -O "${CKPT}/rtmdet_nano_8xb32-100e_coco-obj365-person-05d8511e.pth" \
    https://download.openmmlab.com/mmpose/v1/projects/rtmpose/rtmdet_nano_8xb32-100e_coco-obj365-person-05d8511e.pth
echo "  $(du -h "${CKPT}/rtmdet_nano_8xb32-100e_coco-obj365-person-05d8511e.pth" | cut -f1)  rtmdet_nano_8xb32-100e_coco-obj365-person-05d8511e.pth"

echo "==> sha256"
sha256sum "${CKPT}"/*.pth
