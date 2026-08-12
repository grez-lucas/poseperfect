#!/usr/bin/env bash
# One-command iOS inner loop from Linux. Issue #8.
#
# `builder dev flutter` alone does not work on this repo, for four separate
# reasons, all found and verified in #8:
#
#   1. It runs `flutter attach` with its own cwd, and this repo's Flutter
#      project is `app/`, not the root. From the root, attach dies with
#      `Target file "lib/main.dart" not found`; from `app/`, builder cannot
#      find `dist/`. Hence: builder runs from the root, attach runs from app/.
#   2. MobAI's POST /api/v1/devices/{id}/forward creates a host listener that
#      relays nothing on Linux - reading through it returns "Empty reply from
#      server". iproxy, over the same system usbmuxd, returns HTTP 200 on the
#      same VM service. Hence: tool/iproxy_forward.sh replaces it.
#   3. `builder dev flutter` calls EnsureCustomDevice and REWRITES
#      ~/.config/flutter/custom_devices.json on every invocation, reverting
#      that replacement. Hence: the patch is applied AFTER builder runs, on
#      every run, not once.
#   4. `flutter build ios` never registers --track-widget-creation, so the IPA
#      is built with it off, while `flutter attach` defaults it on. The
#      mismatch makes every reloaded widget throw
#      "Lookup failed: _location in widget_inspector.dart". Hence:
#      --no-track-widget-creation on attach, to match the build.
#
# Measured result: hot reload in ~700ms.
#
# Prerequisites: MobAI running, iPhone on USB, an IPA in dist/ (see
# docs/ios-pipeline.md), iproxy (apt: libusbmuxd-tools).
set -uo pipefail

ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
APP=$ROOT/app
BUNDLE_ID=${POSEPERFECT_BUNDLE_ID:-com.grezlucas.poseperfect.UUGFKB5GBP}
UDID=${MOBAI_DEVICE_ID:-00008120-00092D4E2270201E}
CUSTOM_DEVICES=${HOME}/.config/flutter/custom_devices.json

command -v iproxy >/dev/null || { echo "iproxy missing: sudo apt-get install -y libusbmuxd-tools" >&2; exit 1; }
command -v builder >/dev/null || { echo "builder missing" >&2; exit 1; }

echo "==> launching $BUNDLE_ID under the debugger"
URL=$(cd "$ROOT" && builder dev flutter --no-attach --skip-install \
        --bundle-id "$BUNDLE_ID" </dev/null 2>&1 \
      | grep -oE 'debug-url=\S+' | tail -1 | cut -d= -f2-)

if [ -z "$URL" ]; then
  echo "failed to get a debug URL. Is MobAI running and the phone unlocked?" >&2
  exit 1
fi
echo "==> VM service: $URL"

# Must come AFTER builder, which rewrites this file every run (reason 3).
echo "==> repointing the custom device's forwardPort at iproxy"
python3 - "$CUSTOM_DEVICES" "$ROOT" "$UDID" <<'PY'
import json, sys
path, root, udid = sys.argv[1], sys.argv[2], sys.argv[3]
with open(path) as fh:
    cfg = json.load(fh)
for device in cfg.get('custom-devices', []):
    if device.get('id') == 'mobai-ios':
        device['forwardPort'] = [f'{root}/tool/iproxy_forward.sh',
                                 '${hostPort}', '${devicePort}', udid]
        device['forwardPortSuccessRegex'] = 'FORWARD_READY'
with open(path, 'w') as fh:
    json.dump(cfg, fh, indent=2)
PY

echo "==> attaching (press r to hot reload, R to restart, q to quit)"
cd "$APP"
exec env MOBAI_DEVICE_ID="$UDID" flutter attach \
  -d mobai-ios \
  --no-track-widget-creation \
  --debug-url="$URL"
