#!/usr/bin/env bash
# PROTOTYPE - throwaway. One command to reproduce wayfinder ticket #18.
#
# Bootstraps a venv, fetches COCO val2017 and the three engines' weights,
# runs the sweep, and writes results/ + a Markdown summary.
#
#   ./run.sh
#
# Nothing is installed outside experiments/rear-view/.venv and
# ~/.cache/poseperfect-rearview. Note: this box has no pip and no ensurepip,
# so pip is bootstrapped from get-pip.py.
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CACHE="${HOME}/.cache/poseperfect-rearview"
DATA="${CACHE}/data"
MODELS="${CACHE}/models"
VENV="${HERE}/.venv"
PY="${VENV}/bin/python"

mkdir -p "${DATA}" "${MODELS}"

if [ ! -x "${PY}" ]; then
  echo "==> creating venv (no ensurepip on this box, bootstrapping pip)"
  python3 -m venv --without-pip "${VENV}"
  curl -sSL -o "${CACHE}/get-pip.py" https://bootstrap.pypa.io/get-pip.py
  "${PY}" "${CACHE}/get-pip.py"
fi
"${PY}" -m pip install -q -r "${HERE}/requirements.txt"

echo "==> COCO val2017 (designated fallback; COCO-MEBOW is access-gated)"
if [ ! -f "${DATA}/annotations/person_keypoints_val2017.json" ]; then
  wget -q -c -P "${DATA}" http://images.cocodataset.org/annotations/annotations_trainval2017.zip
  unzip -q -o "${DATA}/annotations_trainval2017.zip" \
    'annotations/person_keypoints_val2017.json' -d "${DATA}"
fi
if [ ! -d "${DATA}/val2017" ]; then
  wget -q -c -P "${DATA}" http://images.cocodataset.org/zips/val2017.zip
  unzip -q -o "${DATA}/val2017.zip" -d "${DATA}"
fi

echo "==> models"
BASE=https://storage.googleapis.com/mediapipe-models/pose_landmarker
for v in heavy full; do
  [ -f "${MODELS}/pose_landmarker_${v}.task" ] || \
    curl -sSL -o "${MODELS}/pose_landmarker_${v}.task" \
      "${BASE}/pose_landmarker_${v}/float16/latest/pose_landmarker_${v}.task"
done
# MoveNet Thunder is only served from Kaggle Models; the old TF Hub mirrors
# now 403. kagglehub downloads it anonymously.
if [ ! -f "${MODELS}/movenet_singlepose_thunder.tflite" ]; then
  KAGGLEHUB_CACHE="${CACHE}/kagglehub" "${PY}" -c "
import kagglehub, shutil, os, glob
p = kagglehub.model_download('google/movenet/tfLite/singlepose-thunder')
shutil.copy(glob.glob(os.path.join(p, '*.tflite'))[0],
            '${MODELS}/movenet_singlepose_thunder.tflite')"
fi
# RTMPose-m is fetched into ~/.cache/rtmlib by rtmlib on first use.

echo "==> sweep (IMAGE mode only, ~5 min on CPU)"
"${PY}" "${HERE}/run_experiment.py" --data "${DATA}" --models "${MODELS}"

echo "==> analysis"
"${PY}" "${HERE}/analyse.py"
echo
echo "results/per_instance.csv   one row per (instance, engine)"
echo "results/predictions.jsonl  raw predicted keypoints, for re-checking"
echo "results/summary.md         every table above"
