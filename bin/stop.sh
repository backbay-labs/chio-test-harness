#!/usr/bin/env bash
# stop.sh — tear down the chio smoke-test harness daemons launched by
# start.sh. Idempotent — OK to invoke multiple times or on a cold
# install. Logs are preserved under ./var/ for post-mortem.

set -euo pipefail

HARNESS_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VAR_DIR="${HARNESS_DIR}/var"

stop_one() {
  local name="$1"
  local pid_file="$2"
  if [[ ! -f "${pid_file}" ]]; then
    echo "stop.sh: ${name} not running (no PID file)" >&2
    return 0
  fi
  local pid
  pid="$(cat "${pid_file}")"
  if [[ -z "${pid}" ]]; then
    rm -f "${pid_file}"
    return 0
  fi
  if kill -0 "${pid}" 2>/dev/null; then
    echo "stop.sh: stopping ${name} (pid ${pid})" >&2
    kill "${pid}" 2>/dev/null || true
    # Give it up to 5s to exit cleanly.
    for _ in 1 2 3 4 5; do
      if ! kill -0 "${pid}" 2>/dev/null; then
        break
      fi
      sleep 1
    done
    if kill -0 "${pid}" 2>/dev/null; then
      echo "stop.sh: SIGKILL ${name} (pid ${pid})" >&2
      kill -9 "${pid}" 2>/dev/null || true
    fi
  else
    echo "stop.sh: ${name} pid ${pid} already gone" >&2
  fi
  rm -f "${pid_file}"
}

stop_one "mcp"   "${VAR_DIR}/mcp.pid"
stop_one "trust" "${VAR_DIR}/trust.pid"

echo "stopped"
