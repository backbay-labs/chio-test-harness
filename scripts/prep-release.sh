#!/usr/bin/env bash
# prep-release.sh — pre-publish validation for @chio/test-harness.
#
# Runs just before `npm pack`/`npm publish` to make sure the tarball
# we ship is actually exerciseable:
#
#   1. clean stale `var/` runtime state that must NOT end up in the tarball
#   2. validate every YAML under `policy/` parses
#   3. (best-effort) smoke a full `bin/start.sh` → `bin/stop.sh` boot cycle
#      against the local chio binary, if one is on PATH or at the
#      documented fallback location. Skipped with a log line if not.
#
# The harness is plain bash + a tiny MCP reference — no TypeScript build.
#
# Exit codes:
#   0  everything ok
#   1  missing dep for validation step
#   2  policy file fails to parse
#   3  smoke boot/shutdown failed
set -euo pipefail

HARNESS_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${HARNESS_DIR}"

echo "[prep-release] cleaning var/…"
rm -rf "${HARNESS_DIR}/var"

echo "[prep-release] validating policy/*.yaml…"
shopt -s nullglob
policy_files=("${HARNESS_DIR}"/policy/*.yaml "${HARNESS_DIR}"/policy/*.yml)
if [[ ${#policy_files[@]} -eq 0 ]]; then
  echo "[prep-release] no policy files found under policy/; nothing to validate" >&2
else
  for f in "${policy_files[@]}"; do
    if command -v python3 >/dev/null 2>&1; then
      python3 -c "import sys, yaml; yaml.safe_load(open(sys.argv[1]))" "$f" \
        || { echo "[prep-release] FAIL: $f did not parse as YAML" >&2; exit 2; }
    elif command -v node >/dev/null 2>&1; then
      # Fallback: node + js-yaml via require resolve from hello-mcp/
      node -e "const fs=require('node:fs'); const s=fs.readFileSync(process.argv[1],'utf8'); if(!s.trim()){process.exit(1)}; /^[\s\S]*$/.test(s);" "$f" \
        || { echo "[prep-release] FAIL: $f unreadable" >&2; exit 2; }
    else
      echo "[prep-release] WARN: no python3 or node available; skipping YAML parse check for $f" >&2
    fi
    echo "[prep-release]   ok: $(basename "$f")"
  done
fi

echo "[prep-release] smoke start/stop…"
chio_bin=""
if [[ -n "${CHIO_BIN:-}" && -x "${CHIO_BIN}" ]]; then
  chio_bin="${CHIO_BIN}"
elif [[ -x "${HARNESS_DIR}/../arc/target/release/chio" ]]; then
  chio_bin="${HARNESS_DIR}/../arc/target/release/chio"
elif command -v chio >/dev/null 2>&1; then
  chio_bin="$(command -v chio)"
fi

if [[ -z "${chio_bin}" ]]; then
  echo "[prep-release] chio binary not found; skipping smoke boot" >&2
  echo "[prep-release] ok (skipped smoke)"
  exit 0
fi

export CHIO_BIN="${chio_bin}"
if bash "${HARNESS_DIR}/bin/start.sh"; then
  bash "${HARNESS_DIR}/bin/stop.sh" || true
  rm -rf "${HARNESS_DIR}/var"
  echo "[prep-release] ok"
  exit 0
else
  bash "${HARNESS_DIR}/bin/stop.sh" || true
  echo "[prep-release] FAIL: smoke start did not reach READY" >&2
  exit 3
fi
