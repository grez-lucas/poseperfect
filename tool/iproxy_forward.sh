#!/usr/bin/env bash
# Port-forward the device's Dart VM service for `flutter attach`, using iproxy
# instead of MobAI.
#
# Why this exists (issue #8): MobAI's POST /api/v1/devices/{id}/forward creates
# a host listener that relays nothing on Linux - reading through it returns
# "Empty reply from server", so every `flutter attach` dies with "Connection
# closed before full header was received". iproxy talks to the same system
# usbmuxd that MobAI itself uses, but implements the relay correctly: the same
# VM service that MobAI cannot reach answers HTTP/1.1 200 OK through iproxy.
#
# Flutter's CustomDevicePortForwarder requires a `forwardPortSuccessRegex` and
# waits forever for a matching line, but iproxy is silent on startup. So this
# wrapper starts iproxy, waits for the socket to actually accept, prints the
# marker Flutter is waiting for, and then stays in the foreground - Flutter
# treats the process exiting as a forwarding failure.
#
# Usage: iproxy_forward.sh <hostPort> <devicePort> [udid]
set -uo pipefail

HOST_PORT=${1:?usage: iproxy_forward.sh <hostPort> <devicePort> [udid]}
DEVICE_PORT=${2:?usage: iproxy_forward.sh <hostPort> <devicePort> [udid]}
UDID=${3:-${MOBAI_DEVICE_ID:-}}

args=()
[ -n "$UDID" ] && args+=(-u "$UDID")

iproxy "${args[@]}" "${HOST_PORT}:${DEVICE_PORT}" &
IPROXY_PID=$!
trap 'kill "$IPROXY_PID" 2>/dev/null' EXIT TERM INT

# Wait for the listener to actually accept before declaring success, rather
# than sleeping a fixed amount and hoping.
for _ in $(seq 1 50); do
  if ! kill -0 "$IPROXY_PID" 2>/dev/null; then
    echo "iproxy exited before the port opened" >&2
    exit 1
  fi
  if (exec 3<>"/dev/tcp/127.0.0.1/${HOST_PORT}") 2>/dev/null; then
    exec 3<&- 3>&-
    echo "FORWARD_READY ${HOST_PORT}:${DEVICE_PORT}"
    wait "$IPROXY_PID"
    exit $?
  fi
  sleep 0.2
done

echo "timed out waiting for 127.0.0.1:${HOST_PORT}" >&2
exit 1
