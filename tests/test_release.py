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


if __name__ == '__main__':
    unittest.main()
