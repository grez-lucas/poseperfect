#!/usr/bin/env bash
# PROTOTYPE - throwaway. Builds the Python 3.10 environment used to export
# RTMDet-Ins to ONNX from the OFFICIAL MMDetection checkpoint, rather than
# trusting a third-party re-upload. Wayfinder ticket #19.
#
# Kept separate from the main .venv because mmcv/mmdet publish no wheels for
# Python 3.12 and pin numpy < 2.
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CACHE="${HOME}/.cache/poseperfect-detector"
VENV="${HERE}/.venv310"
PY="${VENV}/bin/python"

mkdir -p "${CACHE}"

if [ ! -x "${PY}" ]; then
  echo "==> creating python3.10 venv (no ensurepip on this box)"
  python3.10 -m venv --without-pip "${VENV}"
  [ -f "${CACHE}/get-pip.py" ] || curl -sSL -o "${CACHE}/get-pip.py" https://bootstrap.pypa.io/pip/get-pip.py
  "${PY}" "${CACHE}/get-pip.py"
fi

"${PY}" -m pip install -q --upgrade pip setuptools wheel
"${PY}" -m pip install -q "numpy<2" "torch==2.1.2" "torchvision==0.16.2" \
  --index-url https://download.pytorch.org/whl/cpu
"${PY}" -m pip install -q "mmengine==0.10.7"
"${PY}" -m pip install -q "mmcv==2.1.0" \
  -f https://download.openmmlab.com/mmcv/dist/cpu/torch2.1.0/index.html
"${PY}" -m pip install -q "mmdet==3.3.0"
"${PY}" -m pip install -q "onnxruntime==1.19.2" onnx opencv-python-headless pycocotools

echo "==> versions"
"${PY}" -c "import torch, mmcv, mmdet, mmengine; print('torch', torch.__version__); print('mmcv', mmcv.__version__); print('mmdet', mmdet.__version__); print('mmengine', mmengine.__version__)"
