#!/usr/bin/env bash
# PROTOTYPE - throwaway. One command to reproduce wayfinder ticket #19.
#
#   ./run.sh
#
# Builds the Python 3.10 environment (mmcv/mmdet publish no wheels for 3.12 and
# pin numpy < 2), fetches the OFFICIAL OpenMMLab checkpoints, runs the sweep
# over ticket #18's COCO cohort, exports RTMDet-Ins to ONNX with MMDeploy's own
# deploy config, benchmarks the exported graphs, and writes results/.
#
# It reuses experiments/rear-view/ for the cohort and the COCO download, so run
# that experiment's run.sh first if ~/.cache/poseperfect-rearview is empty.
#
# Nothing is installed outside experiments/person-detector/.venv310 and
# ~/.cache/poseperfect-detector.
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PY="${HERE}/.venv310/bin/python"
DATA="${HOME}/.cache/poseperfect-rearview/data"

if [ ! -f "${DATA}/annotations/person_keypoints_val2017.json" ]; then
  echo "COCO val2017 is missing. Run experiments/rear-view/run.sh first." >&2
  exit 1
fi

"${HERE}/bootstrap_mmdet.sh"
"${HERE}/fetch_weights.sh"

echo "==> sweep (IMAGE mode only, CPU, ~25 min over 5 shards)"
"${HERE}/sweep.sh" 5 4

echo "==> unconstrained-input control (whole source image, not the crop)"
"${PY}" "${HERE}/run_fullimage.py"

echo "==> analysis"
"${PY}" "${HERE}/analyse.py"

echo "==> ONNX export (MMDeploy's own RTMDet-Ins deploy config)"
"${HERE}/export_onnx.sh"

echo "==> ONNX Runtime cost"
"${PY}" "${HERE}/bench_onnx.py"

echo
echo "results/per_instance.csv   one row per (instance, detector), plus a gt_box baseline row"
echo "results/summary.md         every table"
echo "results/onnx_cost.json     exported graph sizes and ORT CPU latency"
