"""Delivery integrity regressions, not kernel or host acceptance tests."""

import copy
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import tarfile
import tempfile
import unittest

spec = importlib.util.spec_from_file_location("bundle", Path(__file__).parents[1] / "bundle.py")
bundle = importlib.util.module_from_spec(spec)
spec.loader.exec_module(bundle)


class DeliveryTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.inputs = self.root / "inputs"
        self.inputs.mkdir()
        (self.inputs / "chio").write_bytes(b"fixture kernel bytes, never executed\n")
        (self.inputs / "package.tgz").write_bytes(b"fixture package bytes\n")
        (self.inputs / "OPERATOR.md").write_text("Pending candidate instructions\n")
        self.template = {
            "schema": "chio.required-agent-delivery-template.v1",
            "kernelVersion": bundle.VERSION,
            "target": bundle.TARGET,
            "publication": None,
            "acceptance": {host: "unresolved" for host in bundle.HOSTS},
            "pending": ["real artifact qualification"],
            "entries": [
                {"component": "kernel", "path": "bin/chio", "input": "kernel", "sourcePath": "chio", "sha256": None, "bytes": None},
                {"component": "package", "path": "packages/package.tgz", "input": "prior", "sourcePath": "package.tgz",
                 "sha256": bundle.sha256(self.inputs / "package.tgz"), "bytes": (self.inputs / "package.tgz").stat().st_size},
                {"component": "instructions", "path": "README.md", "input": "instructions", "sourcePath": "OPERATOR.md"},
            ],
        }
        self.binding = {"sha256": bundle.sha256(self.inputs / "chio"), "bytes": (self.inputs / "chio").stat().st_size,
                        "version": bundle.VERSION, "target": bundle.TARGET, "sourceRevision": "a" * 40}
        self.roots = {"kernel": str(self.inputs), "prior": str(self.inputs)}

    def resolve(self, binding=True):
        return bundle.resolve_inputs(self.template, self.roots, self.inputs, self.binding if binding else None)

    def assemble(self, name="bundle"):
        selected, files, pending = self.resolve()
        return bundle.assemble(selected, files, pending, self.root / name)

    def rewrite_manifest(self, root, change):
        manifest = json.loads((root / "manifest.json").read_text())
        change(manifest)
        path = root / "manifest.json"
        path.chmod(0o644)
        bundle.write_json(path, manifest)
        path.chmod(0o444)
        sums = [f"{entry['sha256']}  {entry['path']}\n" for entry in manifest["entries"]]
        sums.append(f"{bundle.sha256(path)}  manifest.json\n")
        checksum = root / "SHA256SUMS"
        checksum.chmod(0o644)
        checksum.write_text("".join(sums))
        checksum.chmod(0o444)

    def test_pending_kernel_verifies_independent_inputs_but_cannot_assemble(self):
        selection, files, pending = self.resolve(binding=False)
        self.assertEqual(pending, ["bin/chio"])
        self.assertEqual(len(files), 2)
        with self.assertRaisesRegex(ValueError, "assembly is unresolved"):
            bundle.assemble(selection, files, pending, self.root / "pending")
        self.assertFalse((self.root / "pending").exists())

    def test_repeated_assembly_is_identical_and_preserves_unaccepted_state(self):
        self.assemble("one")
        self.assemble("two")
        for path in (self.root / "one").rglob("*"):
            if path.is_file():
                self.assertEqual(path.read_bytes(), (self.root / "two" / path.relative_to(self.root / "one")).read_bytes())
        manifest = bundle.verify_bundle(self.root / "one")
        self.assertEqual(set(manifest["acceptance"]), bundle.HOSTS)
        self.assertEqual(set(manifest["acceptance"].values()), {"unresolved on final selected artifacts"})
        self.assertIsNone(manifest["publication"])

    def test_existing_output_is_preserved(self):
        self.assemble()
        before = (self.root / "bundle" / "SHA256SUMS").read_bytes()
        with self.assertRaisesRegex(ValueError, "output must not exist"):
            self.assemble()
        self.assertEqual(before, (self.root / "bundle" / "SHA256SUMS").read_bytes())

    def test_archives_are_reproducible_and_match_every_selected_file(self):
        self.assemble()
        one = bundle.archive_bundle(self.root / "bundle", self.root / "one.tar.gz")
        two = bundle.archive_bundle(self.root / "bundle", self.root / "two.tar.gz")
        self.assertEqual(one, two)
        self.assertEqual((self.root / "one.tar.gz").read_bytes(), (self.root / "two.tar.gz").read_bytes())
        with self.assertRaisesRegex(ValueError, "archive output must not exist"):
            bundle.archive_bundle(self.root / "bundle", self.root / "one.tar.gz")

    def test_old_version_and_wrong_target_are_not_compatible_bindings(self):
        for key, value in [("version", "0.1.0"), ("target", "x86_64-apple-darwin"), ("sourceRevision", "a" * 7)]:
            with self.subTest(key=key):
                wrong = dict(self.binding, **{key: value})
                with self.assertRaises(ValueError):
                    bundle.bind_kernel(copy.deepcopy(self.template), wrong)

    def test_modified_input_and_wrong_size_are_refused(self):
        for key, value in [("sha256", "b" * 64), ("bytes", 1)]:
            entry = self.template["entries"][1]
            original = entry[key]
            entry[key] = value
            with self.subTest(key=key), self.assertRaisesRegex(ValueError, "differs from selected"):
                self.resolve()
            entry[key] = original

    def test_paths_cannot_escape_or_alias_input_root(self):
        for name in ["../private", "/private", "sub/../private", "sub//private", "sub/./private", "sub\\private"]:
            with self.subTest(path=name), self.assertRaises(ValueError):
                bundle.relative(name)
        (self.inputs / "alias").symlink_to(self.inputs, target_is_directory=True)
        with self.assertRaisesRegex(ValueError, "symlinks"):
            bundle.regular(self.inputs, "alias/chio")

    def test_duplicate_inventory_destinations_are_refused(self):
        self.template["entries"].append(copy.deepcopy(self.template["entries"][1]))
        with self.assertRaisesRegex(ValueError, "duplicate or reserved"):
            self.resolve()

    def test_duplicate_json_keys_are_refused(self):
        path = self.root / "ambiguous.json"
        path.write_text('{"sha256":"first","sha256":"second"}')
        with self.assertRaisesRegex(ValueError, "duplicate JSON key"):
            bundle.read_json(path)

    def test_modified_bundle_bytes_are_refused(self):
        self.assemble()
        path = self.root / "bundle" / "packages/package.tgz"
        path.chmod(0o644)
        path.write_bytes(b"changed bytes")
        path.chmod(0o444)
        with self.assertRaisesRegex(ValueError, "differs from selected"):
            bundle.verify_bundle(self.root / "bundle")

    def test_unlisted_private_state_is_refused(self):
        self.assemble()
        (self.root / "bundle" / "operator.json").write_text("fixture only")
        with self.assertRaisesRegex(ValueError, "unlisted artifacts"):
            bundle.verify_bundle(self.root / "bundle")

    def test_self_asserted_acceptance_or_publication_is_refused(self):
        for name, mutate in [
            ("acceptance", lambda m: m["acceptance"].update(claude="accepted")),
            ("publication", lambda m: m.update(publication="https://example.invalid/release")),
        ]:
            with self.subTest(name=name):
                self.assemble(name)
                self.rewrite_manifest(self.root / name, mutate)
                with self.assertRaisesRegex(ValueError, "promotion"):
                    bundle.verify_bundle(self.root / name)

    def test_image_index_must_bind_selected_digest(self):
        image = self.root / "image.tar"
        content = b'{"schemaVersion":2}'
        digest = hashlib.sha256(content).hexdigest()
        index = json.dumps({"manifests": [{"digest": "sha256:" + digest, "size": len(content)}]}).encode()
        with tarfile.open(image, "w") as archive:
            for name, body in [("index.json", index), ("blobs/sha256/" + digest, content)]:
                info = tarfile.TarInfo(name)
                info.size = len(body)
                archive.addfile(info, io.BytesIO(body))
        bundle.check_image({"imageId": "sha256:" + digest}, image)
        with self.assertRaisesRegex(ValueError, "recorded immutable image"):
            bundle.check_image({"imageId": "sha256:" + "a" * 64}, image)


if __name__ == "__main__":
    unittest.main()
