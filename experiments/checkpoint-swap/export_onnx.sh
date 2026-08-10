#!/usr/bin/env bash
# PROTOTYPE - throwaway. Wayfinder ticket #20.
#
# Exports BOTH RTMPose-m checkpoints to ONNX with MMDeploy's own deploy config,
# following the command MMPose itself documents in
# projects/rtmpose/README.md ("run the command to convert RTMPose"), which uses
# configs/mmpose/pose-detection_simcc_onnxruntime_dynamic.py and - not by our
# choice - the aic-coco checkpoint as its worked example.
#
# WHY BOTH. aic-coco ships .pth only, so it has to be converted. body7 already
# ships an official ONNX bundle and does NOT need converting. It is exported
# here anyway, from the same config, the same MMDeploy version and the same
# command, so the sweep can carry a self-exported body7 arm. That arm is the
# control: if self-exported body7 reproduces #18's and #19's numbers, then the
# aic-coco number is a checkpoint difference and not an export artefact.
#
# Same precedent as ../person-detector/export_onnx.sh: convert the OFFICIAL
# first-party checkpoint yourself rather than trust a third-party ONNX
# re-upload.
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DETCACHE="${HOME}/.cache/poseperfect-detector"
CACHE="${HOME}/.cache/poseperfect-checkpoint-swap"
SRC="${DETCACHE}/mmdeploy-src"          # reused from #19, same v1.3.1 clone
POSESRC="${CACHE}/mmpose-src"
CKPT="${CACHE}/checkpoints"
OUT="${CACHE}/onnx"
PY="${HERE}/../person-detector/.venv310/bin/python"
IMG="${HOME}/.cache/poseperfect-rearview/data/val2017/000000000139.jpg"

mkdir -p "${OUT}"

if [ ! -d "${SRC}" ]; then
  git clone -q --depth 1 --branch v1.3.1 https://github.com/open-mmlab/mmdeploy.git "${SRC}"
fi
# The RTMPose model config lives under projects/, which is not shipped inside
# the mmpose wheel's .mim tree, and it uses _base_ paths relative to the mmpose
# source root. So the source tree is needed, at the same tag as the wheel.
if [ ! -d "${POSESRC}" ]; then
  git clone -q --depth 1 --branch v1.3.2 https://github.com/open-mmlab/mmpose.git "${POSESRC}"
fi

DEPLOY="${SRC}/configs/mmpose/pose-detection_simcc_onnxruntime_dynamic.py"
MODEL="${POSESRC}/projects/rtmpose/rtmpose/body_2d_keypoint/rtmpose-m_8xb256-420e_coco-256x192.py"

export PYTHONPATH="${SRC}:${PYTHONPATH:-}"

export_one() {  # tag checkpoint
  local tag="$1" ck="$2"
  echo "==> exporting ${tag}"
  "${PY}" "${SRC}/tools/deploy.py" \
    "${DEPLOY}" \
    "${MODEL}" \
    "${CKPT}/${ck}" \
    "${IMG}" \
    --work-dir "${OUT}/${tag}" \
    --device cpu
}

export_one aic-coco rtmpose-m_simcc-aic-coco_pt-aic-coco_420e-256x192-63eb25f7_20230126.pth
export_one body7    rtmpose-m_simcc-body7_pt-body7_420e-256x192-e48f03d0_20230504.pth

echo "==> exported sizes"
find "${OUT}" -name "*.onnx" -printf "%s\t%p\n" | sort -n

echo "==> graph shape, read out of the exported files"
"${PY}" - "${OUT}" <<'PY'
import glob, os, sys
import onnx
for p in sorted(glob.glob(os.path.join(sys.argv[1], "*", "end2end.onnx"))):
    m = onnx.load(p, load_external_data=False)
    doms = sorted({(o.domain or "''") for o in m.opset_import})
    vers = {o.domain or "": o.version for o in m.opset_import}
    ins = [(i.name, [d.dim_param or d.dim_value for d in i.type.tensor_type.shape.dim])
           for i in m.graph.input]
    outs = [(o.name, [d.dim_param or d.dim_value for d in o.type.tensor_type.shape.dim])
            for o in m.graph.output]
    print(f"{os.path.basename(os.path.dirname(p))}: opset={vers} domains={doms}")
    print(f"  in  {ins}")
    print(f"  out {outs}")
PY
