# Required-agent candidate operation

Status: **0 of 6 integrations accepted by this delivery record**. This is an
immutable qualification bundle. Public compatible-combination delivery and
complete final-artifact [I01-I08 records](https://github.com/backbay-labs/chio/blob/codex/required-agent-integrations-20260909/docs/strategy/chio-direction/19-priority-agent-integrations.md) are required before acceptance. Cursor
still has an unresolved server enforcement contract. Installing its package does
not make protected prompt execution available.

Use only the kernel, packages and images selected in `manifest.json`. The CLI is
`0.1.1-rc.1`; the public historical `0.1.0` and the previous debug candidate are
incompatible selections. An identical version string is not an identical binary.
Retain the exact source revision, SHA256, host executable identity, configuration
and test record for every session.

## Selected versions and supported work

| Host | Native host selection | Integration archive | Supported mode |
|---|---|---|---|
| Claude Code | 2.1.267, `claude-sonnet-5` | `@chio/claude-code-plugin` 0.3.1-rc.1 | Restricted native subscription launch |
| Codex | 0.153.4, `gpt-5.5` | `@chio/codex-plugin` 0.3.0 | Restricted native ChatGPT subscription launch |
| Cursor | CLI 2026.09.08-6caf4ff, GUI 3.19.13 | `chio-cursor` 0.3.0 and matching VSIX | Discovery/activation only; protected prompt launch refuses |
| Hermes | 0.20.5, upstream `175054c14b54404663d8614a178280cffe6062eb`, `gpt-5.5` | `chio-hermes` 0.1.2 | Restricted native Codex subscription launch |
| Pi Agent | `@earendil-works/pi-coding-agent` 0.85.1, `gpt-5.5` | `@chio/pi-plugin` 0.1.0 | Restricted native Codex subscription launch |
| OpenClaw | 2026.5.20, upstream e510042, `gpt-5.5`, selected Linux arm64 image | `@chio/openclaw-kernel` 0.1.0 | Native agent in the restricted container |

The shared TypeScript SDK is `@chio-protocol/sdk` 0.1.1-rc.1. Bridge archives
report 0.3.0 but contain distinct qualified builds: common preparation, Hermes
runtime and operator recovery have separate SHA256s and filenames. Keep each
host's bundled runtime bridge intact. The Hermes adapter wheelhouse includes
`chio-adapter-base` 0.2.0, `chio-code-agent` 0.1.0 and `chio-sdk-python` 0.1.0.
Those Python version labels do not select the historical CLI.

This candidate targets macOS arm64. The delivery verification environment is macOS
26.4 build 25E246, Node 25.5.0, npm 11.8.0, Python 3.11.4 and Docker 28.3.3.
Package engines require Node >=22; a different Node or OS version still needs its
own compatibility record. The Hermes wheelhouse contains Python 3.11 macOS arm64
native wheels. OpenClaw and the resource server run in their pinned Linux arm64
images. Hosts and subscriptions are separate upstream prerequisites.

The five working restricted modes offer useful remote file operations:
`read_text_file`, `write_file`, `edit_file` and `list_directory`. The resource
owner, kernel, policy, signer, authority and resource volume stay outside the
untrusted host. Shell execution, arbitrary network destinations, other MCP or
custom tools, delegation, background work, remote administration and alternate
resource access are disabled or confined. Do not enable them in this mode.
Ordinary advisory hook sessions and the historical OpenClaw chat gateway are
separate products and do not establish this enforcement boundary.

## Verify and install in separate directories

Verify the release's publisher signature and provenance through its shipped
procedure first. A downloaded checksum is an integrity check, not independent
proof of its publisher. This candidate has no asserted public release URL yet.

```sh
cd /absolute/selected-bundle
python3 verify.py verify-bundle --bundle . --images
shasum -a 256 -c SHA256SUMS
docker image load --input images/filesystem-owner.tar
docker image load --input images/openclaw-host.tar
docker image inspect sha256:188cb84d5d0bb4063d4ce5a3b9c3832445a5acda5604911cda80a9136d1850a0
docker image inspect sha256:7f925d68ced724f4a6314ab76dc117e9000515ba62149ee971a11c510be6637f
```

Keep the bundle read-only. Put installs, caches, operator state, host profiles
and workspaces outside it. Select fresh absolute directories for the variables
below; never use a normal host profile or an existing kernel state directory.

```sh
CHIO_BUNDLE=/absolute/selected-bundle
CHIO_INSTALL=/absolute/new-install-directory
CHIO_CACHE=/absolute/new-empty-cache-directory
mkdir -m 700 "$CHIO_INSTALL" "$CHIO_CACHE"
npm install --prefix "$CHIO_INSTALL/bridge" --cache "$CHIO_CACHE/bridge" \
  --offline --ignore-scripts --no-audit --no-fund "$CHIO_BUNDLE/packages/chio-bridge-0.3.0.tgz"
npm install --prefix "$CHIO_INSTALL/claude" --cache "$CHIO_CACHE/claude" \
  --offline --ignore-scripts --no-audit --no-fund "$CHIO_BUNDLE/packages/chio-claude-code-plugin-0.3.1-rc.1.tgz"
npm install --prefix "$CHIO_INSTALL/codex" --cache "$CHIO_CACHE/codex" \
  --offline --ignore-scripts --no-audit --no-fund "$CHIO_BUNDLE/packages/chio-codex-plugin-0.3.0.tgz"
npm install --prefix "$CHIO_INSTALL/cursor" --cache "$CHIO_CACHE/cursor" \
  --offline --ignore-scripts --no-audit --no-fund "$CHIO_BUNDLE/packages/chio-cursor-0.3.0.tgz"
npm install --prefix "$CHIO_INSTALL/openclaw" --cache "$CHIO_CACHE/openclaw" \
  --offline --ignore-scripts --no-audit --no-fund "$CHIO_BUNDLE/packages/chio-openclaw-kernel-0.1.0.tgz"
```

These archives bundle their required JavaScript runtime dependencies. An npm
warning about a package name/version is not discovery or host acceptance. Record
the actual installed package bytes and the launcher discovery result.

Cursor's matching VSIX can be installed for diagnostic activation in a separate
GUI profile. This does not enable the refused protected prompt mode:

```sh
cursor --user-data-dir /absolute/new-cursor-data \
  --extensions-dir /absolute/new-cursor-extensions \
  --install-extension "$CHIO_BUNDLE/packages/chio-cursor-0.3.0.vsix"
```

Keep the same data/extension arguments for removal with
`--uninstall-extension chio.chio-cursor`. Follow the package's `OPERATIONS.md`
for its own hook entries and configuration backups; preserve other extensions.

Pi additionally needs its exactly pinned public upstream peer. The plugin-only
offline install fails with an empty cache. Both commands use the same fresh
prefix and preserve the nested dependency layout:

```sh
npm install --prefix "$CHIO_INSTALL/pi" --cache "$CHIO_CACHE/pi" \
  --ignore-scripts --no-audit --no-fund --install-strategy=nested \
  @earendil-works/pi-coding-agent@0.85.1
npm install --prefix "$CHIO_INSTALL/pi" --cache "$CHIO_CACHE/pi" \
  --ignore-scripts --no-audit --no-fund --install-strategy=nested \
  "$CHIO_BUNDLE/packages/chio-pi-plugin-0.1.0.tgz"
```

Install the Hermes adapter and its distinct bridge without an index or sibling
checkout:

```sh
python3.11 -m venv "$CHIO_INSTALL/hermes"
"$CHIO_INSTALL/hermes/bin/python" -m pip install --no-index --no-cache-dir \
  --find-links "$CHIO_BUNDLE/hermes-wheelhouse" chio-hermes==0.1.2
"$CHIO_INSTALL/hermes/bin/python" -m pip check
npm install --prefix "$CHIO_INSTALL/hermes-bridge" --cache "$CHIO_CACHE/hermes-bridge" \
  --offline --ignore-scripts --no-audit --no-fund \
  "$CHIO_BUNDLE/packages/chio-bridge-hermes-0.3.0-b7785282b4f4.tgz"
```

Hermes itself is a separate public upstream prerequisite. Its wheel's packaged
runbook pins uv 0.12.11, Python 3.11.3 and the public upstream lockfile. Upstream
requires an editable source installation; it does not provide a host wheel.
Use fresh explicit installation paths:

```sh
git init /absolute/new-hermes-source
git -C /absolute/new-hermes-source fetch --no-tags --depth=1 \
  https://github.com/NousResearch/hermes-agent.git \
  175054c14b54404663d8614a178280cffe6062eb
git -C /absolute/new-hermes-source checkout --detach FETCH_HEAD
UV_PROJECT_ENVIRONMENT=/absolute/new-hermes-host-venv uv sync \
  --project /absolute/new-hermes-source --locked --extra mcp --no-dev --python 3.11.3
```

Check `uv --version` before this step; uv 0.9.10 cannot parse that upstream
lockfile. The selected public source tree is
`b485d3e994bda896e30ba7e3216aadb641b1d8e3`; its `uv.lock` SHA256 is
`64a66f8a0ce1d23ea10c16ca89b7104f1828a8f21cf1dd95d7cb74e4bd3efa10`.
Retain the resulting source, lock and installed dependency identities.
Keep the host installation's `.env` absent: upstream may load it despite a
separate `HERMES_HOME`, so this candidate refuses that configuration. The adapter
launcher requires the pinned host checkout and Python executable explicitly.
That public host dependency is distinct from an unpublished Chio sibling checkout.
The wheel embeds its complete README in distribution metadata; display it with:

```sh
"$CHIO_INSTALL/hermes/bin/python" -c 'from importlib.metadata import metadata; print(metadata("chio-hermes").get_payload())'
```

Claude, Codex and Cursor require their selected native executables. Do not
silently upgrade a host that its launcher pins by hash or version.

## Prepare one disposable resource owner

Create a mode-0700 private parent outside all guest-visible profiles, workspaces
and install trees. Every host sandbox must deny that parent, other operator
states and other host profiles. Mode 0600 alone does not isolate same-user
processes. Select a fresh state directory, volume and unused loopback port.

```sh
CHIO_OWNER=/absolute/private/new-owner
CHIO_KERNEL_SHA256=$(python3 -c 'import json,sys; print(next(e["sha256"] for e in json.load(open(sys.argv[1]))["entries"] if e["component"]=="kernel"))' "$CHIO_BUNDLE/manifest.json")
python3 "$CHIO_BUNDLE/resource-owner/serve-filesystem.py" start \
  --state-dir "$CHIO_OWNER" \
  --kernel "$CHIO_BUNDLE/bin/chio" --kernel-sha256 "$CHIO_KERNEL_SHA256" \
  --image sha256:188cb84d5d0bb4063d4ce5a3b9c3832445a5acda5604911cda80a9136d1850a0 \
  --volume chio-required-new-owner --port 58510
python3 "$CHIO_BUNDLE/resource-owner/prepare-session.py" \
  --operator-state "$CHIO_OWNER" \
  --bridge "$CHIO_INSTALL/bridge/node_modules/@chio/bridge"
```

Preparation first waits up to 60 seconds for the retained owner's trusted signer,
checking its private state, selected kernel hash, live process and recorded
session database/listener. No session directory or network request is created
before that check succeeds. `--readiness-timeout-seconds` selects another bounded
deadline up to 300 seconds. A timeout or changed/dead owner fails closed without
an automatic preparation retry. A persistent signer after restart is not proof
of transport readiness; the subsequent authenticated MCP step must also succeed.

Preparation prints a private gateway config path. It pins the trusted kernel
signer and actual subject, session, capability and resource, then exchanges the
operator authority for a delegated 15-minute session credential and exactly four
tools. The policy grants a shared 64-invocation budget and one-hour capability.
Preparation executes no protected tool action. The credential TTL, capability
TTL and retained session's 15-minute idle limit are distinct limits. An expired
session is terminal; refresh/authentication is not unknown-outcome recovery.

Never give the untrusted host `operator.json`, the preparation request, signing
seeds, Docker socket, resource volume, provider credential or kernel bearer.
The launcher retains privileged config and journal in the trusted parent; the
guest receives only its bounded ephemeral transport. Do not create another
kernel session to retry a fenced operation or replenish revoked/exhausted work.
Detailed policy, approval and observation procedures are in
`resource-owner/README.md` and `resource-owner/qualification/APPROVALS.md`.

## Start the actual host with its supported launcher

| Host | Installed launcher | Packaged configuration reference |
|---|---|---|
| Claude | `claude/node_modules/@chio/claude-code-plugin/scripts/restricted.mjs` | `docs/RESTRICTED-MODE.md`: host/gateway hashes, private config, fresh profile/workspace; `--model-auth claude-login` |
| Codex | `codex/node_modules/@chio/codex-plugin/dist/cli/main.js restricted` | `RESTRICTED.md`: private config, pinned binary, fresh evidence directory; `--model-auth-file` |
| Cursor | `cursor/node_modules/chio-cursor/bin/chio-cursor-protected.mjs --probe` | `OPERATIONS.md`: isolated activation and probe only; protected prompt remains refused |
| Hermes | `hermes/bin/python -m chio_hermes.restricted` | Wheel distribution metadata README: pinned host Python/source and bridge; `--model-auth codex-subscription --codex-auth-file ... --model gpt-5.5` |
| Pi | `pi/node_modules/@chio/pi-plugin/dist/protected-cli.js` | `README.md`: config, new profile/workspace; `--provider openai-codex --model gpt-5.5 --codex-auth ...` |
| OpenClaw | `openclaw/node_modules/@chio/openclaw-kernel/scripts/protected.mjs` | `README.md`: private config, new state, pinned image; `--model-auth-file` |

For Codex, after preparation, a useful first workflow is:

```sh
node "$CHIO_INSTALL/codex/node_modules/@chio/codex-plugin/dist/cli/main.js" restricted \
  --gateway-config /absolute/private/new-owner/new-session-ID/gateway.json \
  --codex-binary /absolute/pinned/codex \
  --evidence-dir /absolute/private/new-evidence \
  --model-auth-file /absolute/private/codex-auth.json \
  --prompt 'Use Chio to write /workspace/example.txt, then read the same remote file.'
```

Native subscription authentication is an available supported test path. Claude's
trusted parent uses the existing native login through its fixed Anthropic
origin. Check `claude auth status`; if needed complete `claude auth login` in the
trusted operator profile. Remove an inherited alternate `ANTHROPIC_BASE_URL`.
Codex, Pi, Hermes and OpenClaw use a designated operator-owned regular mode-0600
native Codex auth cache outside guest/install/profile/workspace trees. Initialize
or refresh it with the native Codex CLI. Do not manually copy tokens into guest
configuration, prompts or evidence. The ordinary CLI login does not activate the
restricted launcher; supply its explicit parent-only auth argument.

Observe resource effects through an independent operator-only read-only mount,
and compare its dispatch log before/after forbidden actions. A model summary or
hook deny JSON is insufficient. A verified `completed` response with
`result.isError: true` is a tool failure, not useful work. Output may be sanitized
independently of receipt-detail redaction. Preserve original known user arguments
without reconstructing hidden data or retrying uncertain actions.

## Recover without redispatching uncertainty

Stop the host before operator recovery. Preserve its exact configuration,
authority, journal and request ID. `status` inspects the journal; `recover-lock`
only handles a proven dead process on the same machine and preserves operation
records. Neither operation decides whether a resource action committed.

If the resource owner retained a signed completion, install the separately
selected operator bridge. Do not replace the host's embedded runtime bridge.

```sh
npm install --prefix "$CHIO_INSTALL/operator-bridge" --cache "$CHIO_CACHE/operator-bridge" \
  --offline --ignore-scripts --no-audit --no-fund \
  "$CHIO_BUNDLE/packages/chio-bridge-operator-0.3.0-02a0e4ad4e61.tgz"
python3 "$CHIO_BUNDLE/resource-owner/export-owner-outcome.py" \
  --operator-state /absolute/private/original-owner \
  --gateway-config /absolute/private/original-owner/original-session/gateway.json \
  --request-id ORIGINAL_REQUEST_ID --output /absolute/private/new-owner-result.json
node "$CHIO_INSTALL/operator-bridge/node_modules/@chio/bridge/dist/gateway-operator.js" \
  owner-result-import /absolute/private/original-owner/original-session/gateway.json \
  /absolute/private/new-owner-result.json
node "$CHIO_INSTALL/operator-bridge/node_modules/@chio/bridge/dist/gateway-operator.js" \
  delivery-export /absolute/private/original-owner/original-session/gateway.json \
  ORIGINAL_REQUEST_ID /absolute/private/new-received-result.json
```

The exporter reads the exact retained session/request row without dispatching a
tool. Import verifies the intended signer, original caller/authority, bound
request and entire result. It preserves the previous outcome and leaves the
completion fenced and unacknowledged. Inspect the exported result and independent
resource observation, then acknowledge that exact delivered result explicitly:

```sh
node "$CHIO_INSTALL/operator-bridge/node_modules/@chio/bridge/dist/gateway-operator.js" \
  delivery-acknowledge /absolute/private/original-owner/original-session/gateway.json \
  /absolute/private/new-received-result.json
```

Missing, pending, invalid, mismatched or unverifiable completion remains unknown.
No step renews expired/revoked authority or redispatches the original action.
A session can idle-expire before its delegated credential expires. Credential
expiry alone does not establish that the retained session is live. If the owner
records the original session as expired, preserve that tombstone, journal and
resource observation; a fresh session is independent new work, not recovery of
the original authority. A failed acknowledgement retains the fence. Never clear
a journal, replace its identity, or create a replacement session to hide
uncertainty. Retain state and request operator reconciliation when the resource
lacks a trustworthy outcome.

## Upgrade, restart and remove

Stop the specific host and retain receipts, resource observations and any unknown
outcomes. Keep the owner running while reconciling results and explicitly
revoking the original delegated credential and capability. These administrative
requests read credentials only from the original private files; they print no
tokens and dispatch no tool:

```sh
python3 - /absolute/private/original-owner \
  /absolute/private/original-owner/original-session/gateway.json <<'PY'
import json
from pathlib import Path
import sys
from urllib.parse import quote
from urllib.request import Request, build_opener, ProxyHandler, HTTPRedirectHandler

class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs):
        raise RuntimeError("operator request must not redirect")

state = Path(sys.argv[1])
operator = json.loads((state / "operator.json").read_text())
execution = json.loads(Path(sys.argv[2]).read_text())["execution"]
origin = "http://127.0.0.1:" + str(operator["port"])
if execution["endpoint"] != origin:
    raise SystemExit("gateway and original resource owner do not match")
session = quote(execution["sessionId"], safe="")
opener = build_opener(ProxyHandler({}), NoRedirect())
for path, body, field, expected in [
    ("/admin/sessions/" + session + "/credential/revoke", {}, "sessionId", execution["sessionId"]),
    ("/admin/revocations", {"capability_id": execution["capabilityId"]}, "capabilityId", execution["capabilityId"]),
]:
    request = Request(origin + path, data=json.dumps(body).encode(), method="POST",
                      headers={"Authorization": "Bearer " + operator["adminToken"],
                               "Content-Type": "application/json"})
    with opener.open(request, timeout=10) as response:
        if response.status != 200:
            raise SystemExit("revocation did not complete; preserve state")
        result = json.load(response)
        if result.get("revoked") is not True or result.get(field) != expected:
            raise SystemExit("revocation response does not bind the original authority")
print("Original session credential and capability revocation requests completed.")
PY
```

A failed request leaves removal incomplete; preserve the original state and
resolve it as the operator. Revocation prevents new authority use, but cannot
undo a committed effect or resolve a missing outcome. No step clears a journal.
Then stop the resource owner with `serve-filesystem.py stop --state-dir ...`.
That command preserves databases and both resource/audit volumes. A same-artifact
restart with `restart --state-dir ...` checks the retained binary and policy
hashes and reuses the same durable owner. It is not a database migration or an
upgrade procedure.

Install a newly qualified combination into a separate fresh prefix. Keep the
previous immutable artifacts and a retained-state backup. Finish or fence old
work, reconcile outcomes and revoke its session authority. Validate the new
combination using the applicable upgrade, storage, recovery and real-host tests
before authorizing independent new work. Do not replace a running executable,
mutate a policy snapshot, transplant a journal across identities, or edit the
retained binary hash to bypass the restart check. In-place kernel database
migration is not supplied by this candidate.

For removal, revoke the session credential and capability, stop the parent
launcher and selected owner, and retain required evidence and unresolved state.
Inspect ownership before removing only designated disposable installation
prefixes, host profiles and volumes. No script here deletes normal-home plugin or
citizen state. If a legacy marketplace plugin was installed, use that host's
supported uninstall command in the exact profile where it was installed.
Removing the Chio artifact does not qualify an unrestricted host session.

The release installer is a separate version-pinned artifact owned by Chio's
website repository. Its staged executable/version/checksum gates must pass for
the actual signed RC asset before delivery is claimed. The historical website
default remains independent of this candidate; do not silently install 0.1.0 as
a fallback when an RC download or verification fails.
