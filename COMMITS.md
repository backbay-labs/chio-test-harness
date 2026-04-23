# COMMITS.md — chio-test-harness

Reusable live-daemon fixture. Consumed by `@chio/bridge` live tests and
by every plugin's smoke script (ST.2.x). No mocks — boots real
`chio trust serve` + `chio mcp serve-http` subprocesses. Target first
ship tag: `v0.1.0`.

---

## 1. chore: scaffold harness with bin scripts and gitignore

**Body.** Initial scaffold — `LICENSE`, `.gitignore` (excludes `var/`
runtime state), the `bin/` skeleton. No package.json — harness is
bash-first so smoke tests in any language can source it. Wave 1.

**Files.**

- `LICENSE`
- `.gitignore`
- `bin/` directory layout (empty placeholders committed as part of the
  next commit; included here only as the directory reservation).

---

## 2. feat: add start, stop, wait-ready, env scripts backed by real chio

**Body.** `bin/start.sh` idempotently boots `chio trust serve`
(127.0.0.1:8940) + `chio mcp serve-http` (127.0.0.1:8931), waits for
`/health` to go 200 on both. `bin/stop.sh` kills both by pid-file,
retains logs in `var/`. `bin/wait-ready.sh` polls until both services
respond. `bin/env.sh` exports the `CHIO_*` env vars every downstream
smoke script reads. Wave 1.

**Files.**

- `bin/start.sh`
- `bin/stop.sh`
- `bin/wait-ready.sh`
- `bin/env.sh`

---

## 3. feat: add canonical policy fixtures and hello-mcp subprocess

**Body.** Three HushSpec 0.1.0 policies (`canonical.yaml`,
`tiny-budget.yaml`, `extensions.yaml`) covering the happy path, a
velocity-capped variant, and the `extensions.chio.*` passthrough
path. `hello-mcp/server.mjs` is a stdio MCP server exposing `echo`,
`delete_file`, and `paid_action` — the minimum toolset needed to
exercise allow / deny-by-forbidden-path / deny-by-budget. MCP SDK
pinned to `0.6.0` to work around the `capabilities.sampling.tools`
forward-compat bug on `0.7.x`. Wave 1.

**Files.**

- `policy/canonical.yaml`
- `policy/tiny-budget.yaml`
- `policy/extensions.yaml`
- `hello-mcp/server.mjs`
- `hello-mcp/package.json`
- `hello-mcp/bun.lock`

---

## 4. feat: prefer chio over legacy arc binary during harness bootstrap

**Body.** Harness resolves the runtime binary in this order:
explicit `CHIO_BIN`, sibling `chio` next to `CHIO_ARC_BIN`,
`../arc/target/release/chio` fallback, then `chio` on `PATH`.
Mirrors the ladder `@chio/bridge` uses, so harness + bridge never
diverge on which runtime they boot. Wave 5.0.1.

**Files.**

- `bin/env.sh` — `CHIO_BIN` resolution block.
- `bin/start.sh` — uses `$CHIO_BIN` to launch trust + edge.

---

## 5. ci: smoke-test the harness against a real chio build

**Body.** GitHub Actions workflow: check out arc, run
`setup-chio@v0.1.0`, start the harness, hit `/health` on both
endpoints, run a minimal `chio check` allow/deny round-trip, tear
down. Typecheck is non-blocking per Wave 5.1. Wave 5.1.

**Files.**

- `.github/workflows/ci.yml`

---

## 6. ci: add SLSA L3 release workflow for harness tarball

**Body.** Tag-triggered workflow that packages `bin/`, `policy/`,
and `hello-mcp/package.json` as a GitHub Release asset, signs it
with Sigstore keyless, and attaches a generic SLSA L3 provenance
statement. Harness isn't on npm — it's consumed via
`actions/checkout` from downstream CI. Wave 5.5.

**Files.**

- `.github/workflows/release.yml`
- `scripts/verify-release.sh` — verifies the release asset sha256
  matches the attestation subject.

---

## 7. docs: README with usage, caveats, and smoke assertions

**Body.** Documents the prereqs, the six smoke assertions every
ST.2.x plugin must cover, the MCP SDK 0.6.0 pin rationale, and the
two canonical-policy caveats (`human_in_loop.approve_above` and
`rules.velocity.max_spend_per_window` — both require grant shapes
`chio check`'s synthetic grant doesn't provide). Wave 5.2.

**Files.**

- `README.md`
