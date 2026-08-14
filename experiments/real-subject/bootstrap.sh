#!/usr/bin/env bash
# PROTOTYPE - throwaway. Wayfinder ticket #9.
#
# Reuses ticket #20's environment verbatim rather than building a second one, so
# that a chirality number measured here decodes SimCC through the same rtmlib,
# the same onnxruntime and the same numpy that produced #18's, #19's and #20's.
# A separate venv would quietly cost that comparability.
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PY="${HERE}/../person-detector/.venv310/bin/python"

"${HERE}/../checkpoint-swap/bootstrap.sh"
# Pillow reads Apple's EXIF, which is where camera identity lives - a domain
# invariant (map constraint 5) and not something to take on trust from a filename.
"${PY}" -m pip install -q "pillow>=10,<12"
"${PY}" -c "import PIL; print('pillow', PIL.__version__)"
