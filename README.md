# chio-test-harness

Shared live-daemon harness consumed by the chio plugin smoke tests
(ST.2.x: `chio-claude-code-plugin`, `chio-open-code-plugin`,
`chio-codex-plugin`) and the `@chio/bridge` live integration test
(`bun run test:live`).

The harness boots real chio subprocesses:

| Service     | Port | Command                                                        |
|-------------|------|----------------------------------------------------------------|
| trust plane | 8940 | `CHIO_TRUST_SERVICE_TOKEN=... chio --session-db ... trust serve` |
| MCP edge    | 8931 | `chio mcp serve-http ... -- node hello-mcp/server.mjs`         |

The harness exercises real kernel processes. Its API compatibility tests do not
establish containment of any agent host or replace required-host acceptance.

## Prerequisites

- `chio` binary on `PATH`, or set `CHIO_BIN=/path/to/chio`. The
  harness falls back to `../arc/target/release/chio` if present.
- `node >= 22`, Python 3, `jq`, and OpenSSL.
- `bun` (only needed to install `hello-mcp/` dependencies).
- Ports **8931** and **8940** free.

## First-time install

```bash
cd chio-test-harness/hello-mcp && bun install
```

## Smoke-test-agent usage

```bash
# 1. Bring the harness up. Prints READY when both services are healthy.
bash bin/start.sh

# 2. Source the env vars every smoke test expects.
source bin/env.sh

# 3. Drive the plugin under test. Every plugin smoke test reads:
#    - $CHIO_TRUST_URL     (http://127.0.0.1:8940)
#    - $CHIO_MCP_URL       (http://127.0.0.1:8931)
#    - $CHIO_TOKEN         (bearer for both services)
#    - $CHIO_POLICY        (path to policy/canonical.yaml)
#    - $CHIO_BIN           (absolute path to chio)
#    - $CHIO_HARNESS_DIR   (this directory)

# 4. Tear everything down.
bash bin/stop.sh
```

`start.sh` is idempotent: re-invoking it while the daemons are alive
prints `READY` and exits 0 without restarting. To force a clean start,
call `stop.sh` first.

## Layout

```
bin/
  start.sh        spins trust + edge, waits for readiness
  stop.sh         kills PIDs, removes pid files, keeps logs
  wait-ready.sh   polls /health and MCP initialize until both 200
  env.sh          source-able CHIO_* env vars

policy/
  canonical.yaml     HushSpec 0.1.0 reference policy for happy-path tests
  tiny-budget.yaml   same shape with a 3-invocation velocity window
  extensions.yaml    extensions.chio.* passthrough exercises

hello-mcp/
  server.mjs         stdio MCP server with echo / delete_file / paid_action
  package.json       pinned to @modelcontextprotocol/sdk 0.6.0 (see caveat)

var/                 runtime state (pid files, logs, tokens) — gitignored
```

## MCP SDK pin caveat

`chio mcp serve-http` forwards the client's
`capabilities.sampling.tools: true` down to the wrapped MCP subprocess.
`@modelcontextprotocol/sdk >= 0.7` rejects that input as "unknown
field" and returns JSON-RPC -32603 on initialize. We pin `0.6.0` here
so the edge boots cleanly; once chio's adapter gates this behind a
protocol negotiation, the pin can relax. See
`/Users/connor/Medica/backbay/standalone/arc/crates/chio-mcp-adapter/src/transport.rs:982`
for the forwarded capabilities shape.

## Canonical policy caveats

The canonical policy intentionally avoids two fields that otherwise
make the happy path impossible against a bare `chio check` / `chio mcp
serve-http`:

- **`human_in_loop.approve_above`** — compiles to
  `Constraint::RequireApprovalAbove` on every tool grant, which
  fail-closes when a `governed_intent` is absent. Smoke tests that
  need to exercise HIL threshold semantics must mint their own policy
  and drive chio through `bridge.check({ governed_intent: ... })`
  (not yet surfaced on `@chio/bridge@0.1.0` — see VERIFY.md).
- **`rules.velocity.max_spend_per_window`** — the velocity guard
  fail-closes when the matched grant lacks `max_cost_per_invocation`.
  `chio check`'s synthetic grant does not carry that field, so the
  canonical policy uses `max_invocations_per_window` instead. The
  spend-window path exists in the Rust guard but requires a policy +
  capability combo that carries per-tool cost ceilings.

Both limits are tracked in the parent VERIFY.md so the wave-2
plugin-rewrite agents can code around them.

## What to assert in downstream smoke tests

Minimum coverage every plugin smoke test (ST.2.x) must assert:

1. `bond({ policyPath: "$CHIO_POLICY" })` returns a `did:chio:` subject
   and a non-empty `capabilityId`.
2. `check({ tool: "echo", params: { msg: "hi" } })` returns
   `decision: "allow"`.
3. `check({ tool: "delete_file", params: { path: "/etc/hosts" } })`
   returns `decision: "deny"`.
4. At least one receipt is returned from
   `receipts({ since: T0 })` after a successful echo call, and every
   receipt passes `verifyReceipt()` (ed25519 signature valid).
5. Plugin-specific CLI surface (`claude chio bond`, `opencode plugin
   chio ...`, `codex chio ...`) is exercised end-to-end against the
   running harness — no stubbed `ChioBridge` allowed.

See `/tmp/chio-debate/SMOKE_HARNESS_VERIFY.md` for the reference run.

## CI

[![ci](https://github.com/owner/chio-test-harness/actions/workflows/ci.yml/badge.svg)](https://github.com/owner/chio-test-harness/actions/workflows/ci.yml)

Workflow: [`.github/workflows/ci.yml`](.github/workflows/ci.yml). Runs lint/typecheck (non-blocking in Wave 5.1), unit tests, and a chio-backed smoke pass. Swap `owner/...` once the GitHub org is live.

## Durable owner compatibility

The candidate kernel requires one durable admission owner. `start.sh` launches
the trust process with `var/admission.sqlite`, `var/authority.sqlite`, and
`var/receipts.sqlite`. It waits for authenticated trust readiness before starting
the MCP participant with `--control-url` and its own
`var/mcp-sessions.sqlite` identity. Split local budget/revocation stores must not
be combined with this durable owner, and the participant must not combine local
receipt/authority flags with the remote control URL.

Fixture credentials are private files under `var/` and are passed through child
environments, not command arguments. Run in a disposable clone/profile and set
`CHIO_BIN` to the exact qualified artifact; the version string alone is not an
artifact identity. Do not point delete tests at system files or normal user
state. Create a disposable sentinel, ask the kernel to deny deletion, and check
the original bytes independently. This proves the observed resource survived;
a returned denial alone does not prove prevention.

Startup was verified on 2026-09-09 using source
`d8c5f53705173e614a853bad6c0a85acfdf1212b` and kernel SHA-256
`33dd1dea21a4ca5ecddeab4f30f6b06b0b90c513f0987aef552b0633d9da1e25`.
The trust and MCP services reached readiness, explicit echo execution returned
request-bound signed evidence, and receipt queries returned that work. Remaining
consumer API compatibility failures are independent release blockers; this
startup repair is not full bridge or host acceptance.
