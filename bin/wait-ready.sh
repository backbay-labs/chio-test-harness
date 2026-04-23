#!/usr/bin/env bash
# wait-ready.sh — block until both trust plane (/health on 8940) and MCP
# edge (initialize on 8931/mcp) respond. Exits 0 when both up, 1 on
# timeout. Meant to be invoked by start.sh but callable standalone for
# debugging.

set -euo pipefail

HARNESS_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TRUST_URL="${CHIO_TRUST_URL:-http://127.0.0.1:8940}"
MCP_URL="${CHIO_MCP_URL:-http://127.0.0.1:8931}"
TIMEOUT_SECS="${CHIO_READY_TIMEOUT_SECS:-30}"

TOKEN_FILE="${HARNESS_DIR}/var/trust.token"
if [[ ! -f "${TOKEN_FILE}" ]]; then
  echo "wait-ready: no trust token at ${TOKEN_FILE}" >&2
  exit 1
fi
TOKEN="$(cat "${TOKEN_FILE}")"

deadline=$(( $(date +%s) + TIMEOUT_SECS ))

poll_trust_health() {
  curl --silent --fail --max-time 2 \
    -H "Authorization: Bearer ${TOKEN}" \
    "${TRUST_URL}/health" >/dev/null 2>&1
}

poll_mcp_initialize() {
  # MCP Streamable HTTP expects a JSON-RPC initialize on POST /mcp and
  # returns MCP-Session-Id in response headers. We treat any 200 with an
  # MCP-Session-Id header as "ready".
  local body
  body='{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2025-11-25","capabilities":{},"clientInfo":{"name":"chio-harness-wait-ready","version":"0.1.0"}}}'
  local response
  response=$(curl --silent --include --max-time 3 \
    -H "Authorization: Bearer ${TOKEN}" \
    -H "Content-Type: application/json" \
    -H "Accept: application/json, text/event-stream" \
    --data "${body}" \
    "${MCP_URL}/mcp" 2>/dev/null) || return 1
  grep -iq '^mcp-session-id:' <<< "${response}"
}

trust_ok=0
mcp_ok=0

while [[ $(date +%s) -lt $deadline ]]; do
  if [[ $trust_ok -eq 0 ]] && poll_trust_health; then
    trust_ok=1
    echo "wait-ready: trust plane /health OK at ${TRUST_URL}" >&2
  fi
  if [[ $mcp_ok -eq 0 ]] && poll_mcp_initialize; then
    mcp_ok=1
    echo "wait-ready: MCP edge initialize OK at ${MCP_URL}" >&2
  fi
  if [[ $trust_ok -eq 1 && $mcp_ok -eq 1 ]]; then
    exit 0
  fi
  sleep 1
done

echo "wait-ready: TIMEOUT after ${TIMEOUT_SECS}s (trust_ok=${trust_ok} mcp_ok=${mcp_ok})" >&2
if [[ -f "${HARNESS_DIR}/var/trust.log" ]]; then
  echo "--- last 40 lines of trust.log ---" >&2
  tail -40 "${HARNESS_DIR}/var/trust.log" >&2
fi
if [[ -f "${HARNESS_DIR}/var/mcp.log" ]]; then
  echo "--- last 40 lines of mcp.log ---" >&2
  tail -40 "${HARNESS_DIR}/var/mcp.log" >&2
fi
exit 1
