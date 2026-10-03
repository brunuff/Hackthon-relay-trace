#!/usr/bin/env python3
"""Build a self-contained demo and source archive. No source data is executed."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import zipfile

ROOT = Path(__file__).resolve().parent


def inline_demo(snapshot: dict, destination: Path) -> None:
    if not snapshot.get('events') or not snapshot.get('dataset'):
        raise ValueError('A real evidence snapshot with events and provenance is required.')
    html = (ROOT / 'web/index.html').read_text(encoding='utf-8')
    css = (ROOT / 'web/styles.css').read_text(encoding='utf-8')
    app = (ROOT / 'web/app.js').read_text(encoding='utf-8')
    if re.search(r'</script', app, flags=re.I):
        raise ValueError('Unexpected closing script sequence in application code.')
    encoded = json.dumps(snapshot, ensure_ascii=True).replace('<', '\\u003c')
    html = html.replace('<link rel="stylesheet" href="styles.css">', '<style>\n' + css + '\n</style>')
    html = html.replace('<script defer src="snapshot.js"></script>', '')
    html = html.replace('<script defer src="app.js"></script>', '')
    # Place scripts after the DOM: the source version uses defer, but an inline
    # classic script does not defer. Keep untrusted data separate from source.
    html = html.replace('</body>', '<script>window.SWARM_TRACER_DATA = ' + encoded + ';</script>\n<script>\n' + app + '\n</script>\n</body>')
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(html, encoding='utf-8')


def build(snapshot_path: Path) -> dict:
    snapshot = json.loads(snapshot_path.read_text(encoding='utf-8'))
    artifacts = ROOT / 'artifacts'
    artifacts.mkdir(exist_ok=True)
    # The ordinary multi-file viewer uses the same exact reviewed snapshot.
    encoded = json.dumps(snapshot, ensure_ascii=True).replace('<', '\\u003c')
    (ROOT / 'web/snapshot.js').write_text('window.SWARM_TRACER_DATA = ' + encoded + ';\n', encoding='utf-8')
    demo_path = artifacts / 'RelayTrace_demo.html'
    inline_demo(snapshot, demo_path)
    # Keep the repository's one-file demo in sync with the packaged release.
    (ROOT / 'RelayTrace_demo.html').write_bytes(demo_path.read_bytes())
    zip_path = artifacts / 'RelayTrace_hackathon.zip'
    files = []
    for path in sorted(ROOT.rglob('*')):
        if not path.is_file():
            continue
        rel = path.relative_to(ROOT)
        if rel == Path('RelayTrace_demo.html'):
            continue
        if any(part in {'.git', '__pycache__', '.pytest_cache', 'node_modules', 'artifacts'} for part in rel.parts):
            continue
        if rel.parts[:2] == ('data', 'raw'):
            continue
        if path.suffix in {'.pyc', '.gz'}:
            continue
        if rel.parts[:2] == ('data', 'processed') and path.name != 'evidence.json':
            continue
        files.append(path)
    with zipfile.ZipFile(zip_path, 'w', compression=zipfile.ZIP_DEFLATED) as archive:
        for path in files:
            archive.write(path, arcname='RelayTrace/' + str(path.relative_to(ROOT)))
        archive.write(demo_path, arcname='RelayTrace/RelayTrace_demo.html')
    result = {'demo': str(demo_path), 'archive': str(zip_path), 'file_count': len(files) + 1,
              'snapshot_sha256': hashlib.sha256(snapshot_path.read_bytes()).hexdigest(),
              'demo_sha256': hashlib.sha256(demo_path.read_bytes()).hexdigest(),
              'archive_sha256': hashlib.sha256(zip_path.read_bytes()).hexdigest()}
    (artifacts / 'release_manifest.json').write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--snapshot', type=Path, default=ROOT / 'data/processed/evidence.json')
    args = parser.parse_args()
    print(json.dumps(build(args.snapshot), indent=2))
