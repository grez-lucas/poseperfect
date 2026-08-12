#!/usr/bin/env bash
# PROTOTYPE - throwaway. One command to reproduce wayfinder ticket #20.
#
#   ./run.sh
#
# Reuses ticket #19's Python 3.10 environment, ticket #19's detector and pose
# scoring, and ticket #18's COCO cohort and chirality test. Run
# experiments/rear-view/run.sh first if ~/.cache/poseperfect-rearview is empty.
#
# Nothing is installed outside ../person-detector/.venv310,
# ~/.cache/poseperfect-detector and ~/.cache/poseperfect-checkpoint-swap.
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PY="${HERE}/../person-detector/.venv310/bin/python"
DATA="${HOME}/.cache/poseperfect-rearview/data"

if [ ! -f "${DATA}/annotations/person_keypoints_val2017.json" ]; then
  echo "COCO val2017 is missing. Run experiments/rear-view/run.sh first." >&2
  exit 1
fi

"${HERE}/bootstrap.sh"
"${HERE}/fetch_weights.sh"

echo "==> ONNX export (MMDeploy, via the command MMPose's own README documents)"
"${HERE}/export_onnx.sh"

echo "==> sweep (IMAGE mode only, CPU, ~5 min over 5 shards)"
"${HERE}/sweep.sh" 5 4

echo "==> analysis"
"${PY}" "${HERE}/analyse.py"

echo "==> ONNX Runtime cost"
"${PY}" "${HERE}/bench_onnx.py"

echo
echo "results/per_instance.csv   one row per (instance, pose arm, box source)"
echo "results/summary.md         every table"
echo "results/onnx_cost.json     exported graph sizes and ORT CPU latency"
