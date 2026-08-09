#!/usr/bin/env bash
# PROTOTYPE - throwaway. Exports RTMDet-Ins to ONNX for wayfinder ticket #19,
# using MMDeploy's OWN deploy config for this exact model
# (configs/mmdet/instance-seg/instance-seg_rtmdet-ins_onnxruntime_static-640x640.py)
# and the OFFICIAL checkpoint from download.openmmlab.com.
#
# Deliberately NOT a third-party ONNX re-upload: the whole point of the ticket
# is that a permissive badge on somebody else's converted weights proves
# nothing about provenance.
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CACHE="${HOME}/.cache/poseperfect-detector"
SRC="${CACHE}/mmdeploy-src"
CKPT="${CACHE}/checkpoints"
OUT="${CACHE}/onnx"
PY="${HERE}/.venv310/bin/python"
IMG="${HOME}/.cache/poseperfect-rearview/data/val2017/000000000139.jpg"

if [ ! -d "${SRC}" ]; then
  git clone -q --depth 1 --branch v1.3.1 https://github.com/open-mmlab/mmdeploy.git "${SRC}"
fi

# MMDeploy 1.3.1 cannot export RTMDet-Ins on a CPU-only box: its mask head calls
# mmdet's MlvlPointGenerator.single_level_grid_priors() without a device, and
# that argument defaults to 'cuda', so the export dies with
# "Torch not compiled with CUDA enabled" before it emits anything. One-line
# upstream workaround, applied to the clone rather than to site-packages.
PATCHFILE="${SRC}/mmdeploy/codebase/mmdet/models/dense_heads/rtmdet_ins_head.py"
if ! grep -q "device=mask_feat.device" "${PATCHFILE}"; then
  python3 - "${PATCHFILE}" <<'PY'
import sys
p = sys.argv[1]
s = open(p).read()
old = "    coord = self.prior_generator.single_level_grid_priors(\n        hw, level_idx=0).to(mask_feat.device)"
new = "    coord = self.prior_generator.single_level_grid_priors(\n        hw, level_idx=0, device=mask_feat.device).to(mask_feat.device)"
assert old in s, "mmdeploy source moved; re-check the patch"
open(p, "w").write(s.replace(old, new))
print("patched", p)
PY
fi

MIM="$(${PY} -c 'import mmdet, os; print(os.path.join(os.path.dirname(mmdet.__file__), ".mim", "configs"))')"
DEPLOY="${SRC}/configs/mmdet/instance-seg/instance-seg_rtmdet-ins_onnxruntime_static-640x640.py"

export PYTHONPATH="${SRC}:${PYTHONPATH:-}"

for v in tiny s; do
  case "${v}" in
    tiny) CK="rtmdet-ins_tiny_8xb32-300e_coco_20221130_151727-ec670f7e.pth" ;;
    s)    CK="rtmdet-ins_s_8xb32-300e_coco_20221121_212604-fdc5d7ec.pth" ;;
  esac
  echo "==> exporting rtmdet-ins_${v}"
  "${PY}" "${SRC}/tools/deploy.py" \
    "${DEPLOY}" \
    "${MIM}/rtmdet/rtmdet-ins_${v}_8xb32-300e_coco.py" \
    "${CKPT}/${CK}" \
    "${IMG}" \
    --work-dir "${OUT}/rtmdet-ins_${v}" \
    --device cpu
done

echo "==> exported sizes"
find "${OUT}" -name "*.onnx" -printf "%s\t%p\n" | sort -n
