#!/usr/bin/env bash
# env.sh — source this from smoke-test agents (ST.2.x) after `bin/start.sh`
# has returned `READY`. Populates the CHIO_* envars every downstream plugin
# test harness reads.

HARNESS_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

export CHIO_HARNESS_DIR="${HARNESS_DIR}"
export CHIO_TRUST_URL="${CHIO_TRUST_URL:-http://127.0.0.1:8940}"
export CHIO_MCP_URL="${CHIO_MCP_URL:-http://127.0.0.1:8931}"
export CHIO_POLICY="${CHIO_POLICY:-${HARNESS_DIR}/policy/canonical.yaml}"
export CHIO_POLICY_TINY_BUDGET="${CHIO_POLICY_TINY_BUDGET:-${HARNESS_DIR}/policy/tiny-budget.yaml}"
export CHIO_POLICY_EXTENSIONS="${CHIO_POLICY_EXTENSIONS:-${HARNESS_DIR}/policy/extensions.yaml}"

if [[ -f "${HARNESS_DIR}/var/trust.token" ]]; then
  export CHIO_TOKEN="$(cat "${HARNESS_DIR}/var/trust.token")"
fi

# Wave 5.0.1: chio-policy re-landed first-class `velocity` + `human_in_loop`
# variants on the renamed crate, so the `chio` binary again accepts the
# canonical harness policy. Prefer `chio` at runtime; fall back to the
# legacy `arc` artifact only if a `chio` binary has not been built.
if [[ -z "${CHIO_BIN:-}" ]]; then
  if [[ -x "${HARNESS_DIR}/../arc/target/release/chio" ]]; then
    export CHIO_BIN="${HARNESS_DIR}/../arc/target/release/chio"
  elif command -v chio >/dev/null 2>&1; then
    export CHIO_BIN="$(command -v chio)"
  elif [[ -x "${HARNESS_DIR}/../arc/target/release/arc" ]]; then
    export CHIO_BIN="${HARNESS_DIR}/../arc/target/release/arc"
  elif command -v arc >/dev/null 2>&1; then
    export CHIO_BIN="$(command -v arc)"
  fi
fi
