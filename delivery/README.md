# Required-agent bundle assembly

[Harness overview](../README.md) · [Operator runbook](OPERATOR.md) ·
[Resource owner](RESOURCE-OWNER.md) · [Candidate template](candidate-template.json)

Build a portable installation from exact, checksummed kernel, adapter, SDK and
image inputs. The assembler produces an immutable directory, a complete manifest,
a standalone verifier and an optional deterministic archive. It verifies files
without starting a kernel, host or Docker service.

This guide is for release operators who already have the selected artifacts.
The template does not download missing inputs or publish a release. Every output
retains unresolved publication and per-host acceptance; the compatible public
release, final artifact qualification and Cursor's server enforcement contract
remain separate gates. All six hosts are mandatory.

The [local documentation successor record](evidence/2026-09-10/static-docs-successor/README.md)
identifies one assembled and cold-verified candidate. Its results belong to that
exact archive. A new selection, including the eventual hosted kernel build,
needs its own recorded qualification.

`candidate-template.json` selects the retained packages, wheels and OCI images,
the corrected Claude `0.3.1-rc.1` archive, and the pending macOS arm64 kernel
`0.1.1-rc.1`. The kernel's SHA256, byte count and source revision are deliberately
null until the actual final binary is available. Never fill them with the old
debug kernel, an intermediate dynamically linked binary, or a build expectation.

The template contains no private checkout, credential or owner-state path. Input
roots are supplied in a separate local JSON file. Only named regular files are
read and copied, with symlink traversal refused. Nothing recursively copies an
input directory. No provider credential, kernel database, signer seed, host
profile, resource volume or installed `node_modules` tree belongs in delivery.

## Verify the known inputs now

Create a local `inputs.json` with absolute directories containing the exact
selected files. `prior` refers to the preserved predecessor artifact directory;
it is an assembly input, not a dependency of the output bundle. `claude` contains
the corrected archive named in the template. `kernel` will contain the final
selected binary as `chio`.

```json
{
  "prior": "/absolute/retained-predecessor-bundle",
  "claude": "/absolute/selected-claude-archive-directory",
  "kernel": "/absolute/final-kernel-directory",
  "owner-source": "/absolute/selected-public-Chio-source"
}
```

```sh
python3 delivery/bundle.py verify-inputs --inputs /absolute/private/inputs.json --images
```

Exit 2 means the known files verified but named artifacts are still pending.
Exit 1 is a failed integrity or input check. Exit 0 means all selected input
identities are available and valid; it still does not establish host acceptance.
Image verification reads the saved OCI archive, checks every blob digest and
requires its top-level descriptor to select the recorded immutable image ID.
It does not contact Docker or an image registry.

## Bind and assemble a selected candidate

The release owner supplies a `kernel-binding.json` containing the actual final
binary's recorded identity. The example below is a schema, not valid input:

```json
{
  "version": "0.1.1-rc.1",
  "target": "aarch64-apple-darwin",
  "sourceRevision": "REQUIRED_FULL_40_CHARACTER_SOURCE_REVISION",
  "sha256": "REQUIRED_ACTUAL_64_CHARACTER_BINARY_SHA256",
  "bytes": "REQUIRED_ACTUAL_INTEGER_BYTE_COUNT"
}
```

The binding is a trusted operator's selection record. The assembler verifies
bytes against it; it does not derive a binary's source from its hash or replace
release signing, SLSA provenance, source CI, SBOM validation, loader portability
checks or real-host tests. Retain those independent records for the exact hash.

```sh
python3 delivery/bundle.py assemble \
  --inputs /absolute/private/inputs.json \
  --kernel-binding /absolute/private/kernel-binding.json \
  --images \
  --output /absolute/new-candidate-directory
python3 /absolute/new-candidate-directory/verify.py verify-bundle \
  --bundle /absolute/new-candidate-directory --images
python3 delivery/bundle.py archive \
  --bundle /absolute/new-candidate-directory \
  --output /absolute/new-candidate.tar.gz
```

The output directory must not exist. All input checks occur before creation.
Each copied file is checked again and made read-only. Assembly writes a complete
manifest, SHA256 inventory and standalone verifier, then checks the result.
Repeated assembly from identical selected inputs produces identical file bytes;
file timestamps are set to the Unix epoch. A failed assembly is retained for
inspection and is never silently resumed or promoted. Select a new output path.
The optional archive command produces deterministic gzip/tar bytes with fixed
timestamps and numeric ownership, then rereads every archived file against its
selected checksum. It prints the resulting archive SHA256 and size. It refuses
an existing output and still makes no publication or acceptance claim.

For a cold local installation, first verify the archive's recorded SHA256.
For a public release, also complete the separate publisher/provenance check.
Use the system tar command to extract into a fresh private directory while
preserving the archived read-only modes, then run the verifier from that copy:

```sh
mkdir -m 700 /absolute/new-extracted-candidate
tar -xzf /absolute/selected-candidate.tar.gz -C /absolute/new-extracted-candidate
python3 /absolute/new-extracted-candidate/verify.py verify-bundle \
  --bundle /absolute/new-extracted-candidate --images
/absolute/new-extracted-candidate/bin/chio --version
```

The recorded Python 3.14 default extraction attempt added owner-write permission
to archived files and failed the immutable-mode check. That failed copy remains
retained. The system tar extraction procedure above passed against the actual
local candidate. A verifier refusal must be resolved before installing packages
or launching an owner; never disable the mode check to label an extraction valid.

`OPERATOR.md` becomes the root bundle README. `RESOURCE-OWNER.md` is the selected
Chio resource-owner README. The corrected `prepare-session.py` comes from the
explicit public source revision and checksum named in the template; `owner-source`
is needed only during assembly. All other resource-owner files are copied
byte-for-byte from the explicit predecessor selection. The
assembler records their hashes individually. It does not modify runtime plugin
archives or automatically replace a host's embedded bridge with another build.

## Public delivery gate

The owning repositories are public under `backbay-labs`. The selected kernel
must be published by [Chio's release workflow](https://github.com/backbay-labs/chio)
with its required source checks, signatures, SBOMs and provenance. The compatible
host archives, wheelhouse and saved OCI images must be publicly retrievable with
their exact hashes. Saved image archives can be release assets and do not require
GHCR credentials. No future release tag or asset URL is asserted in this template.

After publication, independently download the actual assets without credentials,
verify publisher identity and exact checksums, and repeat the documented cold
installation and applicable host lifecycle gates. A local copy, source PR,
checksummed unpublished package or tested predecessor does not close I01/I08.
Record every host's final artifact identities, cases, failures, skips and remaining
gaps separately. The assembler deliberately retains unresolved acceptance for all
six; a release evidence record must establish any later acceptance claim.

## Focused checks

```sh
python3 -m unittest discover -s delivery/tests -v
python3 -m py_compile delivery/bundle.py
```

These integrity regressions exercise corrupted/truncated inputs, path and
symlink escapes, wrong kernel version/target/source identity, overwritten output,
ambiguous JSON, unlisted state, OCI selection mismatch and attempted acceptance
promotion. Synthetic fixture bytes in these tests are never host/kernel evidence.
