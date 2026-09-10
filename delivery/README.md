# Required-agent delivery preparation

This directory assembles a new immutable candidate from explicit, checksummed
inputs. It does not publish artifacts, replace the retained 2026-09-09 selection,
or accept a host. All six hosts remain mandatory. The compatible public release,
final artifact qualification and Cursor's server enforcement contract remain
unresolved.

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
  "kernel": "/absolute/final-kernel-directory"
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

## Bind and assemble after final qualification

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

`OPERATOR.md` becomes the root bundle README. `RESOURCE-OWNER.md` replaces the
predecessor's stale build/version instructions. The remaining resource-owner
files are copied byte-for-byte from the explicit predecessor selection. The
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
