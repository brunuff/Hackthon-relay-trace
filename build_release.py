#!/usr/bin/env python3
"""Build a self-contained demo and source archive. No source data is executed."""
from __future__ import annotations

import argparse
import hashlib
import io
import os
import sys
import uuid
import json
from pathlib import Path
import re
import zipfile

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / 'src'))
from swarm_tracer.safe_io import open_directory, read_regular


# Reviewed exact paths; additions require explicit release review. No recursive scan.
APPROVED_FILES = ('.github/workflows/validate.yml', '.gitignore', 'DATA_NOTES.md', 'LICENSE', 'README.md', 'WORKFLOW.md', 'audit_transcript_quotes.py', 'build_release.py', 'crop_ai_village_memories.py', 'data/episodes.json', 'data/processed/evidence.json', 'docs/AI_VILLAGE_INPUTS.md', 'docs/AI_VILLAGE_PILOT.md', 'docs/AI_VILLAGE_VALIDATION.md', 'docs/LOCAL_VALIDATION.md', 'docs/RESEARCH.md', 'docs/REVIEW.md', 'docs/SUBMISSION.md', 'docs/TRANSCRIPT_CITATION_AUDIT.md', 'docs/VALIDATION.md', 'docs/images/demo-desktop.png', 'docs/images/demo-mobile.png', 'docs/specs/BENCHMARK_v1.md', 'docs/specs/RELEASE_SAFETY_v1.md', 'release_policy.json', 'src/swarm_tracer/__init__.py', 'src/swarm_tracer/__main__.py', 'src/swarm_tracer/ai_village.py', 'src/swarm_tracer/benchmark.py', 'src/swarm_tracer/pipeline.py', 'src/swarm_tracer/safe_io.py', 'tests/browser_smoke.cjs', 'tests/test_ai_village.py', 'tests/test_benchmark.py', 'tests/test_memory_crop.py', 'tests/test_pipeline.py', 'tests/test_release.py', 'tests/test_review.py', 'tests/test_transcript_quotes.py', 'web/app.js', 'web/index.html', 'web/snapshot.js', 'web/styles.css')


def validate_public_provenance(snapshot: dict, policy=None) -> None:
    if policy is None:
        policy = json.loads(read_regular(ROOT / 'release_policy.json'))
    dataset = snapshot.get('dataset', {})
    if dataset != policy['dataset'] or dataset.get('id') != 'collusion-wiki-2026-09-03' or dataset.get('synthetic') is not False or dataset.get('acquisition_mode') != 'public-redacted-dataset':
        raise ValueError('Snapshot is not the approved public Collusion dataset.')
    files = dataset.get('source_files', [])
    expected = {'revisions.jsonl.gz', 'events.jsonl.gz', 'manifest.json.gz', 'pages.jsonl.gz'}
    if len(files) != 4 or {r.get('filename') for r in files} != expected:
        raise ValueError('Complete fixed public source provenance required.')
    for record in files:
        if record.get('url') != 'https://collusion.wiki/explorer/download/' + record['filename'] or not re.fullmatch(r'[a-f0-9]{64}', record.get('sha256', '')) or not isinstance(record.get('bytes'), int) or record['bytes'] <= 0:
            raise ValueError('Invalid public source-file provenance.')
    if dataset.get('sha256') != next(r['sha256'] for r in files if r['filename'] == 'revisions.jsonl.gz'):
        raise ValueError('Revision source hash conflict.')
    if not snapshot.get('events'):
        raise ValueError('Public evidence events are required.')
    for event in snapshot['events']:
        provenance = event.get('provenance', {})
        revision = event.get('source_revision_id')
        if not revision or provenance.get('dataset_id') != dataset['id'] or provenance.get('record_path') != 'revisions.jsonl.gz#' + revision:
            raise ValueError('Invalid public event provenance.')
        if not event.get('source_url', '').startswith('https://collusion.wiki/explorer/page/') or not re.fullmatch(r'[a-f0-9]{64}', event.get('content_sha256', '')):
            raise ValueError('Invalid public source URL or hash.')
    for edge in snapshot.get('edges', []):
        if edge.get('receipt_observed') is not False or edge.get('causal_uptake_observed') is not False:
            raise ValueError('Public wiki cannot establish receipt or causal uptake.')


def preflight(snapshot_path: Path) -> dict:
    try:
        captured = {name: read_regular(ROOT / name) for name in APPROVED_FILES}
        path = snapshot_path.absolute()
        payload = captured['data/processed/evidence.json'] if path == (ROOT / 'data/processed/evidence.json').absolute() else read_regular(path)
    except OSError as error:
        raise ValueError('Missing, unsafe or symlinked approved input.') from error
    policy = json.loads(captured['release_policy.json'])
    if hashlib.sha256(payload).hexdigest() != policy['snapshot_sha256']:
        raise ValueError('Snapshot bytes have no public release approval.')
    snapshot = json.loads(payload)
    validate_public_provenance(snapshot, policy)
    if captured['data/processed/evidence.json'] != payload:
        raise ValueError('Packaged evidence differs from approved snapshot.')
    return {'snapshot': snapshot, 'files': captured, 'payload': payload}


def render_demo(snapshot: dict, captured: dict) -> bytes:
    if not snapshot.get('events') or not snapshot.get('dataset'):
        raise ValueError('A real evidence snapshot with events and provenance is required.')
    html = captured['web/index.html'].decode('utf-8')
    css = captured['web/styles.css'].decode('utf-8')
    app = captured['web/app.js'].decode('utf-8')
    if re.search(r'</script', app, flags=re.I):
        raise ValueError('Unexpected closing script sequence in application code.')
    encoded = json.dumps(snapshot, ensure_ascii=True).replace('<', '\\u003c')
    html = html.replace('<link rel="stylesheet" href="styles.css">', '<style>\n' + css + '\n</style>')
    html = html.replace('<script defer src="snapshot.js"></script>', '')
    html = html.replace('<script defer src="app.js"></script>', '')
    # Place scripts after the DOM: the source version uses defer, but an inline
    # classic script does not defer. Keep untrusted data separate from source.
    html = html.replace('</body>', '<script>window.SWARM_TRACER_DATA = ' + encoded + ';</script>\n<script>\n' + app + '\n</script>\n</body>')
    return html.encode('utf-8')


def inline_demo(snapshot: dict, destination: Path) -> None:
    captured = {name: read_regular(ROOT / name) for name in ('web/index.html', 'web/styles.css', 'web/app.js')}
    payload = render_demo(snapshot, captured)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_bytes(payload)


def replace_staged(outputs):
    """Stage every complete output before replacements; each replacement is atomic.

    This is not a multi-file transaction: a failure during the final replacements
    can leave a mixed generation. Rendering/ZIP/staging failures preserve outputs.
    Directory descriptors prevent a parent-symlink swap redirecting writes.
    """
    staged = []
    try:
        for relative, payload in outputs.items():
            path = ROOT / relative
            parent = open_directory(path.parent, create=True)
            temporary = '.relaytrace-' + uuid.uuid4().hex
            staged.append((parent, temporary, path.name))
            fd = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600, dir_fd=parent)
            with os.fdopen(fd, 'wb') as stream:
                stream.write(payload)
                stream.flush()
                os.fsync(stream.fileno())
        for parent, temporary, destination in staged:
            os.replace(temporary, destination, src_dir_fd=parent, dst_dir_fd=parent)
    finally:
        for parent, temporary, destination in staged:
            try:
                os.unlink(temporary, dir_fd=parent)
            except FileNotFoundError:
                pass
            finally:
                os.close(parent)


def build(snapshot_path: Path) -> dict:
    approved = preflight(snapshot_path)
    snapshot, captured, payload = approved['snapshot'], approved['files'], approved['payload']
    demo = render_demo(snapshot, captured)
    encoded = json.dumps(snapshot, ensure_ascii=True).replace('<', '\\u003c')
    viewer = ('window.SWARM_TRACER_DATA = ' + encoded + ';\n').encode('utf-8')
    captured['web/snapshot.js'] = viewer
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, 'w', compression=zipfile.ZIP_DEFLATED) as archive:
        for name in APPROVED_FILES:
            info = zipfile.ZipInfo('RelayTrace/' + name, date_time=(2026, 10, 3, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            archive.writestr(info, captured[name])
        info = zipfile.ZipInfo('RelayTrace/RelayTrace_demo.html', date_time=(2026, 10, 3, 0, 0, 0))
        info.compress_type = zipfile.ZIP_DEFLATED
        archive.writestr(info, demo)
    zipped = buffer.getvalue()
    result = {'demo': str(ROOT / 'artifacts/RelayTrace_demo.html'), 'archive': str(ROOT / 'artifacts/RelayTrace_hackathon.zip'),
              'file_count': len(APPROVED_FILES) + 1, 'snapshot_sha256': hashlib.sha256(payload).hexdigest(),
              'demo_sha256': hashlib.sha256(demo).hexdigest(), 'archive_sha256': hashlib.sha256(zipped).hexdigest()}
    replace_staged({'web/snapshot.js': viewer, 'RelayTrace_demo.html': demo, 'artifacts/RelayTrace_demo.html': demo,
                    'artifacts/RelayTrace_hackathon.zip': zipped,
                    'artifacts/release_manifest.json': (json.dumps(result, indent=2) + '\n').encode()})
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--snapshot', type=Path, default=ROOT / 'data/processed/evidence.json')
    args = parser.parse_args()
    print(json.dumps(build(args.snapshot), indent=2))
