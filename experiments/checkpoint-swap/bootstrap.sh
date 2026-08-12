#!/usr/bin/env bash
# PROTOTYPE - throwaway. Wayfinder ticket #20.
#
# Reuses ticket #19's Python 3.10 environment verbatim
# (experiments/person-detector/bootstrap_mmdet.sh) and adds only what #19 did
# not need: mmpose, so MMDeploy can export an RTMPose checkpoint, and rtmlib,
# so the exported graph is decoded by exactly the same reference implementation
# #18 and #19 used.
#
# The environment is SHARED with #19 on purpose. A second venv would mean a
# second numpy, a second onnxruntime and a second rtmlib, and then the swap
# rates measured here would not be strictly comparable to #19's.
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DET="$(cd "${HERE}/../person-detector" && pwd)"
PY="${DET}/.venv310/bin/python"

"${DET}/bootstrap_mmdet.sh"

# mmpose 1.3.2 is the release that ships the RTMPose configs MMDeploy needs.
#
# One upstream defect, recorded rather than hidden: mmpose's runtime
# requirements pull in chumpy 0.70, whose setup.py does `import pip`. Under
# pip's default build isolation that import fails with
# "ModuleNotFoundError: No module named 'pip'" and the whole mmpose install
# aborts. Installing chumpy first with --no-build-isolation, so it builds
# against the venv's own pip, is the one-line fix. chumpy is only used by
# mmpose's SMPL mesh code and is not on RTMPose's path at all.
"${PY}" -m pip install -q --no-build-isolation "chumpy==0.70"
"${PY}" -m pip install -q "mmpose==1.3.2"
# torch 2.1.2 is built against numpy 1, and mmcv 2.1.0 will not import under
# numpy 2. opencv 5.x hard-requires numpy >= 2, so it has to be held at 4.x -
# otherwise pip resolves a combination that imports but silently fails
# torch<->numpy interop with "Failed to initialize NumPy: _ARRAY_API not found".
"${PY}" -m pip install -q "opencv-python==4.10.0.84" "opencv-python-headless==4.10.0.84"
# mmengine 0.10.7 calls `import pkg_resources` when resolving a config's
# `_base_` across packages, which setuptools >= 81 no longer ships.
"${PY}" -m pip install -q "setuptools<81"
"${PY}" -m pip install -q "numpy<2"
# rtmlib is what #18 and #19 used to decode SimCC and to build the top-down
# affine. Reused rather than reimplemented - that reuse is what makes this
# ticket's chirality numbers comparable to theirs.
"${PY}" -m pip install -q "rtmlib==0.0.13"

echo "==> versions"
"${PY}" - <<'PY'
import importlib.metadata as md
import numpy, torch, mmcv, mmdet, mmpose, mmengine, onnxruntime, cv2, rtmlib
for m in (numpy, torch, mmcv, mmdet, mmpose, mmengine, onnxruntime, cv2):
    print(f"{m.__name__:14s} {m.__version__}")
print(f"{'rtmlib':14s} {md.version('rtmlib')}")
PY
