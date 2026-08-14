#!/usr/bin/env bash
# PROTOTYPE - throwaway. Wayfinder ticket #9.
#
# Two halves. The instrument is validated on COCO, where a second opinion
# exists; the athlete is measured with it, where one does not. The order is not
# cosmetic - if `synthetic_check.py` fails, nothing measured on the real
# captures means anything, and there is no way to discover that from the real
# captures themselves.
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PY="${HERE}/../person-detector/.venv310/bin/python"
PHOTOS="${1:-}"

[ -x "${PY}" ] || { echo "run ./bootstrap.sh first"; exit 1; }

echo "==> validating the instrument against COCO ground truth"
"${PY}" "${HERE}/synthetic_check.py" --limit 200

if [ -z "${PHOTOS}" ]; then
  echo
  echo "No capture directory given, so the instrument check is all that ran."
  echo "Shoot the session first - see CAPTURE.md - then:"
  echo "  ./run.sh <directory of photographs>"
  exit 0
fi

echo "==> ingesting ${PHOTOS}"
"${PY}" "${HERE}/ingest.py" --photos "${PHOTOS}"

if ! grep -qiE ',y,|,y$' "${HERE}/results/shotlog.csv"; then
  echo
  echo "results/shotlog.csv has no confirmed rows. Open it, correct the"
  echo "proposed mapping, mark rows 'y' in the confirmed column, and re-run."
  exit 1
fi

echo "==> measuring"
"${PY}" "${HERE}/run_experiment.py" --photos "${PHOTOS}"
"${PY}" "${HERE}/analyse.py"
