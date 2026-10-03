"""Guard the executable/data boundary in the standalone release."""
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location('build_release', ROOT / 'build_release.py')
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class ReleaseTests(unittest.TestCase):
    def test_script_closing_text_cannot_escape_snapshot(self):
        if not (ROOT / 'web/app.js').is_file():
            self.skipTest('Viewer has not been built yet')
        payload = '</script><script>window.INJECTED=true</script>'
        snapshot = {'dataset': {'id': 'synthetic-test-fixture'}, 'events': [{'id': 'test', 'text': payload}]}
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'demo.html'
            MODULE.inline_demo(snapshot, path)
            text = path.read_text()
        self.assertNotIn(payload, text)
        encoded = text.split('window.SWARM_TRACER_DATA = ', 1)[1].split(';</script>', 1)[0]
        self.assertEqual(json.loads(encoded)['events'][0]['text'], payload)
        self.assertNotIn('src="app.js"', text)
        self.assertNotIn('href="styles.css"', text)

    def test_empty_release_is_refused(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(ValueError):
                MODULE.inline_demo({'dataset': {}}, Path(tmp) / 'empty.html')

class ReleaseSafetyTests(unittest.TestCase):
    def setUp(self):
        import shutil
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name).resolve()
        # Explicitly synthetic test-only restricted files below; no real private rows.
        for name in MODULE.APPROVED_FILES:
            source = ROOT / name
            target = self.root / name
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source, target)
        self.old_root = MODULE.ROOT
        MODULE.ROOT = self.root

    def tearDown(self):
        MODULE.ROOT = self.old_root
        self.tmp.cleanup()

    def test_exact_allowlist_excludes_surprise_files(self):
        import zipfile
        for name in ('secret.json', 'docs/private-packet.json', 'web/crop.json', 'data/processed/restricted.json'):
            path = self.root / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text('{"synthetic_restricted": true}')
        result = MODULE.build(self.root / 'data/processed/evidence.json')
        with zipfile.ZipFile(result['archive']) as archive:
            expected = {'RelayTrace/' + name for name in MODULE.APPROVED_FILES}
            expected.add('RelayTrace/RelayTrace_demo.html')
            self.assertEqual(set(archive.namelist()), expected)
            self.assertEqual(len(archive.namelist()), len(expected))

    def test_rejected_snapshot_preserves_outputs(self):
        for name in ('web/snapshot.js', 'RelayTrace_demo.html', 'artifacts/RelayTrace_demo.html', 'artifacts/RelayTrace_hackathon.zip', 'artifacts/release_manifest.json'):
            path = self.root / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(b'sentinel')
        before = {str(p.relative_to(self.root)): p.read_bytes() for p in self.root.rglob('*') if p.is_file()}
        public = json.loads((ROOT / 'data/processed/evidence.json').read_text())
        for snapshot in ({'dataset': {'id': 'ai-village', 'synthetic': False}, 'events': [{'text': 'SYNTHETIC PRIVATE'}]}, public | {'unexpected': 'SYNTHETIC PRIVATE'}, {'events': [], 'dataset': {}}):
            path = self.root / 'candidate.json'
            path.write_text(json.dumps(snapshot))
            with self.assertRaises(ValueError):
                MODULE.build(path)
            for name, content in before.items():
                self.assertEqual((self.root / name).read_bytes(), content)

    def test_provenance_validation(self):
        import copy
        snapshot = json.loads((ROOT / 'data/processed/evidence.json').read_text())
        MODULE.validate_public_provenance(snapshot)
        for mutate in (lambda s: s['dataset'].update(acquisition_mode='restricted'), lambda s: s['events'][0]['provenance'].update(dataset_id='ai-village'), lambda s: s['dataset']['source_files'][0].update(url='https://private.invalid/data')):
            candidate = copy.deepcopy(snapshot)
            mutate(candidate)
            with self.assertRaises(ValueError):
                MODULE.validate_public_provenance(candidate)

    def test_invalid_allowlist_input_preserves_outputs(self):
        target = self.root / 'LICENSE'
        target.unlink()
        target.symlink_to(ROOT / 'LICENSE')
        with self.assertRaises(ValueError):
            MODULE.build(self.root / 'data/processed/evidence.json')
        self.assertFalse((self.root / 'artifacts').exists())
        target.unlink()
        with self.assertRaises(ValueError):
            MODULE.build(self.root / 'data/processed/evidence.json')
        self.assertFalse((self.root / 'artifacts').exists())

class ReleaseRaceTests(unittest.TestCase):
    setUp = ReleaseSafetyTests.setUp
    tearDown = ReleaseSafetyTests.tearDown
    def seed_outputs(self):
        names = ('web/snapshot.js', 'RelayTrace_demo.html', 'artifacts/RelayTrace_demo.html', 'artifacts/RelayTrace_hackathon.zip', 'artifacts/release_manifest.json')
        for name in names:
            path = self.root / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(b'prior-output')
        return {name: (self.root / name).read_bytes() for name in names}

    def test_swapped_inputs_are_never_reopened(self):
        from unittest.mock import patch
        import zipfile
        original = MODULE.preflight
        evidence = (self.root / 'data/processed/evidence.json').read_bytes()
        license_bytes = (self.root / 'LICENSE').read_bytes()
        private = self.root / 'synthetic-private.json'
        private.write_bytes(b'SYNTHETIC RESTRICTED')
        def swap(path):
            captured = original(path)
            (self.root / 'data/processed/evidence.json').write_bytes(b'SYNTHETIC RESTRICTED')
            (self.root / 'LICENSE').unlink()
            (self.root / 'LICENSE').symlink_to(private)
            return captured
        with patch.object(MODULE, 'preflight', side_effect=swap):
            result = MODULE.build(self.root / 'data/processed/evidence.json')
        with zipfile.ZipFile(result['archive']) as archive:
            self.assertEqual(archive.read('RelayTrace/LICENSE'), license_bytes)
            self.assertEqual(archive.read('RelayTrace/data/processed/evidence.json'), evidence)

    def test_render_failure_preserves_prior_outputs(self):
        before = self.seed_outputs()
        (self.root / 'web/app.js').write_text('</script>')
        with self.assertRaises(ValueError):
            MODULE.build(self.root / 'data/processed/evidence.json')
        for name, content in before.items():
            self.assertEqual((self.root / name).read_bytes(), content)

    def test_archive_failure_preserves_prior_outputs(self):
        from unittest.mock import patch
        import zipfile
        before = self.seed_outputs()
        # Both old disk archive.write and new in-memory writestr must fail.
        with patch.object(zipfile.ZipFile, 'write', side_effect=OSError('injected archive failure')), patch.object(zipfile.ZipFile, 'writestr', side_effect=OSError('injected archive failure')):
            with self.assertRaises(OSError):
                MODULE.build(self.root / 'data/processed/evidence.json')
        for name, content in before.items():
            self.assertEqual((self.root / name).read_bytes(), content)

    def test_staging_failure_preserves_prior_outputs(self):
        from unittest.mock import patch
        before = self.seed_outputs()
        real = MODULE.os.fsync
        calls = []
        def fail_third(fd):
            calls.append(fd)
            if len(calls) == 3:
                raise OSError('injected staged write failure')
            return real(fd)
        with patch.object(MODULE.os, 'fsync', side_effect=fail_third):
            with self.assertRaises(OSError):
                MODULE.build(self.root / 'data/processed/evidence.json')
        for name, content in before.items():
            self.assertEqual((self.root / name).read_bytes(), content)
        self.assertFalse(list(self.root.rglob('.relaytrace-*')))


if __name__ == '__main__':
    unittest.main()
