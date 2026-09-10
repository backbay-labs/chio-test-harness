# Initial static local bundle and cold operation observations

This is local delivery qualification, not publication or any mandatory host's
acceptance. The selected static kernel is source
`bafa02b06de93553cecb6f60b340f3dd8fd9b401`, CLI `0.1.1-rc.1`, binary SHA256
`c03a8a711dbbd15da2c59655d9ab6d8f0068a20187363db7a78f4b5422ded93e`.
The initial local bundle used the 48 inputs selected by harness source
`7b54077fd12f673ec8f22ef963df803c79739094`, plus its standalone verifier. It
retains unresolved acceptance and publication fields. The older 2026-09-09
candidate selection remains unchanged.

The checked archive SHA256 is
`0c32bdcd88b010f8cfe7e15f239972a7f3c97fbe4a6f13515606a777ed6d0574`,
518,085,611 bytes. All 51 archive files were reread against selected checksums.
Its first extraction using Python 3.14's default data filter changed read-only
file modes and correctly failed verification. A separate new extraction using
the system tar command preserved modes, passed complete inventory/OCI checks,
and ran the installed kernel's exact RC version successfully. The failed copy
remains retained; the mode gate was not weakened.

A fresh empty-cache offline operator bridge installation from this bundle
matched all 1,056 regular archive files. The first dedicated resource-owner start
exceeded the wrapper's 30-second observation window. Inspection found only the
private policy and two created volumes, with no kernel/operator credentials,
session authority, live process or retained container. These partial artifacts
were preserved. A fresh `-r2` state/volume selection then started successfully in
50.56 seconds. These startup observations overlap the separately investigated
Docker capacity problem; this record does not infer its exact causal cutpoint.

The immediate old `prepare-session.py` call raised `FileNotFoundError` because
the trusted signer file had not yet appeared. It left one empty directory and
made no preparation request or network call. Once the key existed, a separate
explicit preparation succeeded. This concrete readiness failure motivated the
owning Chio helper repair at
`3374dba0c1537e933e8f3e1074264b96668e5825`. That helper and its source README
require a distinct successor bundle and their own actual cold-start observation.

The original bundle's documented administrative procedure was exercised against
the actual dedicated kernel owner. A verified operator gateway control write
produced exactly one independently observed dispatch and the expected file
bytes. The unmodified documented revocation snippet then revoked both the
original session credential and capability; its parsed responses bound both
identities. A following write returned `not_dispatched`, the forbidden file
remained absent, and independent resource/audit state was unchanged. These are
operator procedure tests, not a Claude/Codex/Cursor/Hermes/Pi/OpenClaw workflow.
The owner was stopped successfully and all databases, journals and volumes were
retained.

The 41 raw files are losslessly compressed with original and compressed hashes
in `raw-files.json`. No owner configuration, provider credential, signer seed,
database, resource volume, installation tree or private input-root map is
included. Exact local bundle, extraction, installation and retained-state paths
are in the corresponding raw operation records.
