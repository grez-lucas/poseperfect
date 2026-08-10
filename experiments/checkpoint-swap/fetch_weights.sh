#!/usr/bin/env bash
# PROTOTYPE - throwaway. Wayfinder ticket #20.
#
# Fetches the two RTMPose-m checkpoints under audit, straight from
# download.openmmlab.com, so provenance is first-party rather than a
# third-party re-upload. SHA256s are printed and recorded in run_meta.json.
#
#   body7    - what the map committed to in #16. Trained on AI Challenger, MS
#              COCO, CrowdPose, MPII, sub-JHMDB, Halpe, PoseTrack18. Ships an
#              official ONNX bundle.
#   aic-coco - the swap candidate. Trained on AI Challenger + MS COCO only.
#              .pth ONLY - there is no official ONNX, which is exactly why
#              export_onnx.sh exists.
set -euo pipefail

CACHE="${HOME}/.cache/poseperfect-checkpoint-swap"
CKPT="${CACHE}/checkpoints"
mkdir -p "${CKPT}"

BASE=https://download.openmmlab.com/mmpose/v1/projects/rtmposev1

get() {  # url
  local url="$1" name
  name="$(basename "${url}")"
  [ -f "${CKPT}/${name}" ] || wget -q -c -O "${CKPT}/${name}" "${url}"
  echo "  $(du -h "${CKPT}/${name}" | cut -f1)  ${name}"
}

echo "==> RTMPose-m body7 (the incumbent - contains MPII)"
get "${BASE}/rtmpose-m_simcc-body7_pt-body7_420e-256x192-e48f03d0_20230504.pth"

echo "==> RTMPose-m aic-coco (the swap candidate - no MPII, .pth only)"
get "${BASE}/rtmpose-m_simcc-aic-coco_pt-aic-coco_420e-256x192-63eb25f7_20230126.pth"

echo "==> the OFFICIAL body7 ONNX bundle, i.e. the exact graph #18 and #19 ran."
echo "    Fetched here so the self-exported body7 graph can be checked against it."
[ -f "${CKPT}/rtmpose-m_simcc-body7_pt-body7_420e-256x192-e48f03d0_20230504.zip" ] || \
  wget -q -c -O "${CKPT}/rtmpose-m_simcc-body7_pt-body7_420e-256x192-e48f03d0_20230504.zip" \
    "${BASE}/onnx_sdk/rtmpose-m_simcc-body7_pt-body7_420e-256x192-e48f03d0_20230504.zip"
echo "  $(du -h "${CKPT}/rtmpose-m_simcc-body7_pt-body7_420e-256x192-e48f03d0_20230504.zip" | cut -f1)  rtmpose-m_simcc-body7_...zip"

echo "==> sha256"
sha256sum "${CKPT}"/*.pth "${CKPT}"/*.zip
