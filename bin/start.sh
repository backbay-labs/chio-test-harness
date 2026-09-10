#!/usr/bin/env bash
# start.sh — launch the chio smoke-test harness.
#
# Starts two long-running chio subprocesses (trust plane on 8940 and MCP
# edge on 8931), records PIDs/logs under ./var/, waits until both are
# serving, and prints `READY` on stdout. Idempotent: if PID files exist
# and the referenced processes are alive, it prints "already running"
# and exits 0 without restarting. To force a clean start, call
# `bin/stop.sh` first.
#
# Exit codes:
#   0  both services healthy and `READY` printed
#   1  dependency missing (chio binary, node, Python 3, jq)
#   2  health timeout; logs under ./var/ retained for post-mortem

set -euo pipefail
umask 077

command -v python3 >/dev/null 2>&1 || { echo "start.sh: Python 3 is required for authenticated readiness" >&2; exit 1; }

HARNESS_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${HARNESS_DIR}"

VAR_DIR="${HARNESS_DIR}/var"
mkdir -p "${VAR_DIR}"

TRUST_PID_FILE="${VAR_DIR}/trust.pid"
MCP_PID_FILE="${VAR_DIR}/mcp.pid"
TRUST_LOG="${VAR_DIR}/trust.log"
MCP_LOG="${VAR_DIR}/mcp.log"
TOKEN_FILE="${VAR_DIR}/trust.token"

TRUST_ADDR="${CHIO_TRUST_ADDR:-127.0.0.1:8940}"
MCP_ADDR="${CHIO_MCP_ADDR:-127.0.0.1:8931}"
POLICY="${CHIO_POLICY:-${HARNESS_DIR}/policy/canonical.yaml}"

is_alive() {
  local pid_file="$1"
  [[ -f "${pid_file}" ]] || return 1
  local pid
  pid="$(cat "${pid_file}")"
  [[ -n "${pid}" ]] || return 1
  kill -0 "${pid}" 2>/dev/null
}

# Idempotent: if both daemons are already alive, short-circuit.
if is_alive "${TRUST_PID_FILE}" && is_alive "${MCP_PID_FILE}"; then
  echo "start.sh: already running (trust_pid=$(cat "${TRUST_PID_FILE}") mcp_pid=$(cat "${MCP_PID_FILE}"))" >&2
  echo "READY"
  exit 0
fi

# Clean up any stale PID files referring to dead processes and re-start.
for f in "${TRUST_PID_FILE}" "${MCP_PID_FILE}"; do
  if [[ -f "${f}" ]] && ! is_alive "${f}"; then
    rm -f "${f}"
  fi
done

# Truncate logs for a fresh run.
: > "${TRUST_LOG}"
: > "${MCP_LOG}"

# Resolve chio runtime binary. Wave 5.0.1: chio-policy re-landed
# first-class `velocity` + `human_in_loop` variants, so the canonical
# harness policy once again parses against the `chio` binary. Prefer
# `chio` here; fall back to the legacy `arc` artifact only if `chio`
# has not been built yet.
if [[ -n "${CHIO_BIN:-}" && -x "${CHIO_BIN}" ]]; then
  CHIO="${CHIO_BIN}"
elif [[ -x "${HARNESS_DIR}/../arc/target/release/chio" ]]; then
  CHIO="${HARNESS_DIR}/../arc/target/release/chio"
elif command -v chio >/dev/null 2>&1; then
  CHIO="$(command -v chio)"
elif [[ -x "${HARNESS_DIR}/../arc/target/release/arc" ]]; then
  CHIO="${HARNESS_DIR}/../arc/target/release/arc"
elif command -v arc >/dev/null 2>&1; then
  CHIO="$(command -v arc)"
else
  echo "start.sh: chio binary not found. Set CHIO_BIN or add chio/arc to PATH." >&2
  exit 1
fi

# Resolve or mint a trust service token.
if [[ -n "${CHIO_TOKEN:-}" ]]; then
  printf '%s' "${CHIO_TOKEN}" > "${TOKEN_FILE}"
else
  if [[ ! -s "${TOKEN_FILE}" ]]; then
    # Deterministic-enough service token scoped to this harness install.
    openssl rand -hex 32 > "${TOKEN_FILE}"
  fi
fi
TOKEN="$(cat "${TOKEN_FILE}")"

# ----- Trust plane -------------------------------------------------------
# The trust process owns durable admission and shared authority/receipts.
# Each MCP participant keeps only its own durable kernel identity.
RECEIPT_DB="${VAR_DIR}/receipts.sqlite"
AUTHORITY_DB="${VAR_DIR}/authority.sqlite"
ADMISSION_DB="${VAR_DIR}/admission.sqlite"
MCP_SESSION_DB="${VAR_DIR}/mcp-sessions.sqlite"
# Passport lifecycle registry — required for /v1/passport/statuses publish
# flows to return anything other than HTTP 409. Wave 2 bridge unlocks
# bond() against this registry.
PASSPORT_STATUSES_FILE="${VAR_DIR}/passport-statuses.json"

CHIO_TRUST_SERVICE_TOKEN="${TOKEN}" nohup "${CHIO}" \
  --receipt-db "${RECEIPT_DB}" \
  --authority-db "${AUTHORITY_DB}" \
  --session-db "${ADMISSION_DB}" \
  trust serve \
    --listen "${TRUST_ADDR}" \
    --passport-statuses-file "${PASSPORT_STATUSES_FILE}" \
    --allow-local-peer-urls \
  >>"${TRUST_LOG}" 2>&1 &
TRUST_PID=$!
echo "${TRUST_PID}" > "${TRUST_PID_FILE}"

# The MCP participant reconciles against the single trust admission owner.
# Wait for that owner before starting a participant; do not use split local
# budget/revocation databases or disable durable admission to hide a mismatch.
CHIO_HARNESS_TOKEN="${TOKEN}" CHIO_HARNESS_TRUST_ADDR="${TRUST_ADDR}" python3 - <<'PY'
import os
import time
import urllib.error
import urllib.request

request = urllib.request.Request(
    "http://" + os.environ["CHIO_HARNESS_TRUST_ADDR"] + "/health",
    headers={"Authorization": "Bearer " + os.environ["CHIO_HARNESS_TOKEN"]},
)
deadline = time.monotonic() + 30
while time.monotonic() < deadline:
    try:
        with urllib.request.urlopen(request, timeout=2) as response:
            if response.status == 200:
                break
    except (urllib.error.URLError, TimeoutError):
        pass
    time.sleep(0.2)
else:
    raise SystemExit("trust admission owner did not become ready")
PY

# ----- MCP edge ---------------------------------------------------------
# The edge wraps our local hello-mcp stdio server and gates every call
# through the specified policy.
CHIO_AUTH_TOKEN="${TOKEN}" CHIO_CONTROL_TOKEN="${TOKEN}" nohup "${CHIO}" \
  --session-db "${MCP_SESSION_DB}" \
  --control-url "http://${TRUST_ADDR}" \
  mcp serve-http \
    --listen "${MCP_ADDR}" \
    --policy "${POLICY}" \
    --server-id hello-mcp \
    --server-name "chio-harness-hello-mcp" \
    -- node "${HARNESS_DIR}/hello-mcp/server.mjs" \
  >>"${MCP_LOG}" 2>&1 &
MCP_PID=$!
echo "${MCP_PID}" > "${MCP_PID_FILE}"

# ----- Wait for readiness -----------------------------------------------
export CHIO_TRUST_URL="http://${TRUST_ADDR}"
export CHIO_MCP_URL="http://${MCP_ADDR}"

if ! bash "${HARNESS_DIR}/bin/wait-ready.sh"; then
  echo "start.sh: services did not become ready within the timeout" >&2
  # Best-effort post-mortem: surface the last few log lines so the
  # caller (downstream smoke agent) can diagnose without digging.
  echo "--- trust.log tail ---" >&2
  tail -20 "${TRUST_LOG}" >&2 || true
  echo "--- mcp.log tail ---" >&2
  tail -20 "${MCP_LOG}" >&2 || true
  exit 2
fi

echo "READY"
