#!/usr/bin/env python3
"""Verify and assemble explicit Chio candidate inputs without accepting or publishing them."""

import argparse
import copy
import gzip
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import shutil
import stat
import sys
import tarfile


HOSTS = {"claude", "codex", "cursor", "hermes", "pi", "openclaw"}
VERSION = "0.1.1-rc.1"
TARGET = "aarch64-apple-darwin"
SHA256 = re.compile(r"[0-9a-f]{64}")
REVISION = re.compile(r"[0-9a-f]{40}")


def sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def relative(value):
    if not isinstance(value, str) or not value or "\\" in value:
        raise ValueError("artifact path must be a nonempty relative POSIX path")
    path = PurePosixPath(value)
    if path.is_absolute() or any(part in (".", "..") for part in value.split("/")):
        raise ValueError("artifact path must not escape its selected root")
    if str(path) != value or any(ord(c) < 32 for c in value):
        raise ValueError("artifact path must be canonical and contain no control characters")
    return path


def regular(root, name):
    root = root.resolve(strict=True)
    current = root
    for part in relative(name).parts:
        current = current / part
        if current.is_symlink():
            raise ValueError(f"artifact paths must not traverse symlinks: {name}")
    metadata = current.stat()
    if not stat.S_ISREG(metadata.st_mode):
        raise ValueError(f"artifact must be a regular file: {name}")
    return current


def read_json(path):
    def unique(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError(f"duplicate JSON key: {key}")
            result[key] = value
        return result
    return json.loads(path.read_text(), object_pairs_hook=unique)


def check_identity(entry, path):
    if not isinstance(entry.get("sha256"), str) or not SHA256.fullmatch(entry["sha256"]):
        raise ValueError(f"missing or malformed SHA256: {entry['path']}")
    if type(entry.get("bytes")) is not int or entry["bytes"] < 0:
        raise ValueError(f"missing or malformed byte count: {entry['path']}")
    if path.stat().st_size != entry["bytes"] or sha256(path) != entry["sha256"]:
        raise ValueError(f"artifact differs from selected SHA256 or size: {entry['path']}")


def check_image(entry, path):
    """Check the saved OCI archive without extracting or starting it."""
    selected = entry["imageId"]
    if not re.fullmatch(r"sha256:[0-9a-f]{64}", selected):
        raise ValueError("image identity must be an immutable SHA256 digest")
    with tarfile.open(path, "r:") as archive:
        members = archive.getmembers()
        names = [member.name for member in members]
        if len(names) != len(set(names)):
            raise ValueError("image archive has duplicate member paths")
        for member in members:
            relative(member.name.rstrip("/"))
            if not member.isfile() and not member.isdir():
                raise ValueError("image archive contains a link or special file")
            if member.isfile() and member.name.startswith("blobs/sha256/"):
                expected = member.name.removeprefix("blobs/sha256/")
                if not SHA256.fullmatch(expected):
                    raise ValueError("image archive contains a malformed blob path")
                digest = hashlib.sha256()
                with archive.extractfile(member) as stream:
                    for chunk in iter(lambda: stream.read(1024 * 1024), b""):
                        digest.update(chunk)
                if digest.hexdigest() != expected:
                    raise ValueError("image archive blob digest differs from its name")
        index = json.load(archive.extractfile("index.json"))
        descriptors = index.get("manifests", [])
        if len(descriptors) != 1 or descriptors[0].get("digest") != selected:
            raise ValueError("image archive does not select the recorded immutable image")
        blob = archive.getmember("blobs/sha256/" + selected.removeprefix("sha256:"))
        if blob.size != descriptors[0].get("size"):
            raise ValueError("selected image descriptor has an incorrect byte count")


def validate_template(template):
    if template.get("schema") != "chio.required-agent-delivery-template.v1":
        raise ValueError("unsupported delivery template schema")
    if template.get("kernelVersion") != VERSION or template.get("target") != TARGET:
        raise ValueError("this delivery selection requires the explicit macOS arm64 RC")
    if set(template.get("acceptance", {})) != HOSTS:
        raise ValueError("all six hosts must remain in the acceptance inventory")
    if template.get("publication") is not None:
        raise ValueError("candidate assembly does not establish public release delivery")
    entries = template.get("entries")
    if not isinstance(entries, list) or not entries:
        raise ValueError("template must name explicit artifact entries")
    seen = set()
    kernels = []
    for entry in entries:
        name = str(relative(entry["path"]))
        if name in seen or name in ("manifest.json", "SHA256SUMS", "verify.py"):
            raise ValueError("duplicate or reserved artifact destination")
        seen.add(name)
        relative(entry["sourcePath"])
        if entry["component"] == "kernel":
            kernels.append(entry)
    if len(kernels) != 1 or kernels[0]["path"] != "bin/chio":
        raise ValueError("selection must contain exactly one kernel at bin/chio")


def bind_kernel(template, binding):
    expected = {"version": VERSION, "target": TARGET}
    for name, value in expected.items():
        if binding.get(name) != value:
            raise ValueError(f"kernel binding requires {name} {value}")
    if not isinstance(binding.get("sourceRevision"), str) or not REVISION.fullmatch(binding["sourceRevision"]):
        raise ValueError("kernel binding requires a full source revision")
    if not isinstance(binding.get("sha256"), str) or not SHA256.fullmatch(binding["sha256"]):
        raise ValueError("kernel binding requires the exact binary SHA256")
    if type(binding.get("bytes")) is not int or binding["bytes"] < 1:
        raise ValueError("kernel binding requires the actual positive binary size")
    entry = next(e for e in template["entries"] if e["component"] == "kernel")
    for key in ("sha256", "bytes", "sourceRevision", "version", "target"):
        entry[key] = binding[key]


def resolve_inputs(template, inputs, instructions, binding=None, images=False):
    selection = copy.deepcopy(template)
    validate_template(selection)
    if binding is not None:
        bind_kernel(selection, binding)
    roots = {key: Path(value) for key, value in inputs.items()}
    roots["instructions"] = instructions
    selected = []
    pending = []
    for entry in selection["entries"]:
        if entry["input"] == "instructions":
            path = regular(instructions, entry["sourcePath"])
            entry.update(sha256=sha256(path), bytes=path.stat().st_size)
        elif entry.get("sha256") is None or entry.get("bytes") is None:
            pending.append(entry["path"])
            continue
        else:
            if entry["input"] not in roots:
                raise ValueError(f"missing explicitly selected input root: {entry['input']}")
            path = regular(roots[entry["input"]], entry["sourcePath"])
        check_identity(entry, path)
        if images and entry["component"] == "docker-image":
            check_image(entry, path)
        selected.append((entry, path))
    return selection, selected, pending


def write_json(path, value):
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")


def assemble(selection, selected, pending, output):
    if pending:
        raise ValueError("assembly is unresolved: " + ", ".join(pending))
    # Refuse any existing destination, including a broken symlink. Never update
    # an old selection, operator state, installed profile, or existing bundle.
    if os.path.lexists(output):
        raise ValueError("output must not exist; prior bundles are immutable")
    output.mkdir(mode=0o700, parents=False)
    entries = []
    for source_entry, source in selected:
        destination = output / source_entry["path"]
        destination.parent.mkdir(parents=True, exist_ok=True)
        with source.open("rb") as reader, destination.open("xb") as writer:
            shutil.copyfileobj(reader, writer, 1024 * 1024)
        check_identity(source_entry, destination)
        entry = {k: v for k, v in source_entry.items() if k not in ("input", "sourcePath")}
        entry["mode"] = "0555" if entry["component"] == "kernel" else "0444"
        destination.chmod(int(entry["mode"], 8))
        entries.append(entry)
    verifier = output / "verify.py"
    shutil.copyfile(Path(__file__), verifier)
    verifier.chmod(0o555)
    entries.append({"component": "delivery-verifier", "path": "verify.py", "sha256": sha256(verifier),
                    "bytes": verifier.stat().st_size, "mode": "0555"})
    manifest = {
        "schema": "chio.required-agent-delivery.v1",
        "status": "unaccepted qualification candidate; assembly does not qualify or publish any host",
        "kernelVersion": VERSION,
        "target": TARGET,
        "acceptance": {host: "unresolved on final selected artifacts" for host in sorted(HOSTS)},
        "publication": None,
        "pending": selection["pending"],
        "entries": sorted(entries, key=lambda entry: entry["path"]),
    }
    write_json(output / "manifest.json", manifest)
    sums = [f"{entry['sha256']}  {entry['path']}\n" for entry in manifest["entries"]]
    sums.append(f"{sha256(output / 'manifest.json')}  manifest.json\n")
    (output / "SHA256SUMS").write_text("".join(sums))
    for path in output.rglob("*"):
        if path.is_file():
            if path.name in ("manifest.json", "SHA256SUMS"):
                path.chmod(0o444)
            os.utime(path, (0, 0))
    verify_bundle(output, images=True)
    return manifest


def verify_bundle(root, images=False):
    manifest = read_json(regular(root, "manifest.json"))
    if manifest.get("schema") != "chio.required-agent-delivery.v1":
        raise ValueError("unsupported assembled bundle schema")
    if manifest.get("kernelVersion") != VERSION or manifest.get("target") != TARGET:
        raise ValueError("bundle does not select the required RC version and target")
    if (set(manifest.get("acceptance", {})) != HOSTS
            or set(manifest["acceptance"].values()) != {"unresolved on final selected artifacts"}
            or manifest.get("publication") is not None):
        raise ValueError("candidate verifier cannot validate an acceptance or publication promotion")
    expected = set()
    sums = []
    for entry in manifest["entries"]:
        name = str(relative(entry["path"]))
        if name in expected or name in ("manifest.json", "SHA256SUMS"):
            raise ValueError("duplicate or reserved bundle path")
        expected.add(name)
        path = regular(root, name)
        check_identity(entry, path)
        if entry.get("mode") not in ("0444", "0555") or stat.S_IMODE(path.stat().st_mode) != int(entry["mode"], 8):
            raise ValueError(f"artifact mode differs from immutable selection: {name}")
        if images and entry["component"] == "docker-image":
            check_image(entry, path)
        sums.append(f"{entry['sha256']}  {entry['path']}\n")
    sums.append(f"{sha256(root / 'manifest.json')}  manifest.json\n")
    if regular(root, "SHA256SUMS").read_text() != "".join(sums):
        raise ValueError("SHA256SUMS differs from the complete manifest inventory")
    kernels = [entry for entry in manifest["entries"] if entry["component"] == "kernel"]
    if len(kernels) != 1 or kernels[0]["path"] != "bin/chio":
        raise ValueError("bundle must select exactly one kernel at bin/chio")
    bind_kernel({"entries": kernels}, kernels[0])
    expected.update({"manifest.json", "SHA256SUMS"})
    actual = set()
    for path in root.rglob("*"):
        if path.is_symlink():
            raise ValueError("assembled bundle contains an unexpected symlink")
        if not path.is_dir():
            actual.add(path.relative_to(root).as_posix())
    if actual != expected:
        raise ValueError("bundle contains missing or unlisted artifacts")
    return manifest


def archive_bundle(root, output):
    manifest = verify_bundle(root, images=True)
    expected = {entry["path"]: entry["sha256"] for entry in manifest["entries"]}
    for name in ("manifest.json", "SHA256SUMS"):
        expected[name] = sha256(root / name)
    if os.path.lexists(output):
        raise ValueError("archive output must not exist")
    with output.open("xb") as raw:
        with gzip.GzipFile(filename="", mode="wb", fileobj=raw, mtime=0, compresslevel=6) as compressed:
            with tarfile.open(mode="w|", fileobj=compressed, format=tarfile.PAX_FORMAT) as archive:
                for name in sorted(expected):
                    source = regular(root, name)
                    info = tarfile.TarInfo(name)
                    info.size = source.stat().st_size
                    info.mode = stat.S_IMODE(source.stat().st_mode)
                    with source.open("rb") as stream:
                        archive.addfile(info, stream)
    # Verify archived bytes, rather than relying only on the input scan.
    with tarfile.open(output, "r:gz") as archive:
        if archive.getnames() != sorted(expected):
            raise ValueError("archived inventory differs from verified bundle")
        for member in archive.getmembers():
            digest = hashlib.sha256()
            with archive.extractfile(member) as stream:
                for chunk in iter(lambda: stream.read(1024 * 1024), b""):
                    digest.update(chunk)
            if digest.hexdigest() != expected[member.name]:
                raise ValueError(f"archived bytes changed during packing: {member.name}")
    return {"archiveSha256": sha256(output), "archiveBytes": output.stat().st_size,
            "verifiedEntries": len(expected), "acceptance": "unresolved", "publication": None}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    for command in ("verify-inputs", "assemble"):
        sub = commands.add_parser(command)
        sub.add_argument("--template", type=Path, default=Path(__file__).with_name("candidate-template.json"))
        sub.add_argument("--inputs", type=Path, required=True, help="Private JSON map of explicit artifact root paths")
        sub.add_argument("--kernel-binding", type=Path)
        sub.add_argument("--instructions", type=Path, default=Path(__file__).parent)
        sub.add_argument("--images", action="store_true")
        if command == "assemble":
            sub.add_argument("--output", type=Path, required=True)
    verify = commands.add_parser("verify-bundle")
    verify.add_argument("--bundle", type=Path, required=True)
    verify.add_argument("--images", action="store_true")
    archive = commands.add_parser("archive")
    archive.add_argument("--bundle", type=Path, required=True)
    archive.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    try:
        if args.command == "archive":
            result = archive_bundle(args.bundle, args.output)
        elif args.command == "verify-bundle":
            manifest = verify_bundle(args.bundle, images=args.images)
            result = {"verifiedEntries": len(manifest["entries"]), "completeAssembly": True,
                      "acceptance": "unresolved", "publication": None}
        else:
            binding = read_json(args.kernel_binding) if args.kernel_binding else None
            selection, selected, pending = resolve_inputs(read_json(args.template), read_json(args.inputs),
                                                          args.instructions, binding, args.images)
            result = {"verifiedEntries": len(selected), "pendingArtifacts": pending,
                      "completeAssembly": False, "acceptance": "unresolved", "publication": None}
            if args.command == "assemble":
                manifest = assemble(selection, selected, pending, args.output)
                result.update(completeAssembly=True, verifiedEntries=len(manifest["entries"]))
            print(json.dumps(result, indent=2))
            return 2 if pending else 0
        print(json.dumps(result, indent=2))
        return 0
    except (ValueError, OSError, KeyError, TypeError, tarfile.TarError) as error:
        print(f"Candidate delivery refused: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
