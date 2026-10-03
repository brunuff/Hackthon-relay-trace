"""Frozen extraction comparison. No acquisition, curated overrides or auto-labeling."""
from __future__ import annotations
import argparse
from collections import Counter
import copy
import json
import os
from pathlib import Path
from .safe_io import open_directory
from .pipeline import normalize_revisions, generate_edges, artifacts, read_jsonl, sha256

PROTOCOL = 'BENCHMARK_v1'
VARIANTS = ('full', 'lines', 'tokens')


def extract_variants(revisions):
    normalized = normalize_revisions(revisions)
    bodies = {str(r.get('rev_id') or r.get('id')): str(r.get('body', r.get('text', ''))) for r in revisions}
    variants = {}
    for variant in VARIANTS:
        events = copy.deepcopy(normalized)
        for event in events:
            text = bodies[event['source_revision_id']] if variant == 'full' else event['text'] if variant == 'lines' else event['matching_text']
            event['text'] = event['matching_text'] = text
        variants[variant] = events
    return variants


def candidate_report(revisions, *, held_out_pages, demo_revision_ids=(), demo_pages=()):
    return _candidate_report(extract_variants(revisions), held_out_pages=held_out_pages, demo_revision_ids=demo_revision_ids, demo_pages=demo_pages)


def _candidate_report(variants, *, held_out_pages, demo_revision_ids=(), demo_pages=()):
    pages = set(held_out_pages)
    demo_ids = set(demo_revision_ids)
    blocked = set(demo_pages) | {e['page_key'] for e in variants['full'] if e['source_revision_id'] in demo_ids}
    if not pages or pages & blocked:
        raise ValueError('Held-out population overlaps demonstration pages or is empty.')
    variants = {name: [e for e in events if e['page_key'] in pages] for name, events in variants.items()}
    if not variants['full'] or any(e['source_revision_id'] in demo_ids for e in variants['full']):
        raise ValueError('Missing held-out records or demo revision leakage.')
    frequency = Counter(token for e in variants['full'] for token in artifacts(e))
    union = {}
    event_pages = {e['id']: e['page_key'] for e in variants['full']}
    for name in VARIANTS:
        for edge in generate_edges(variants[name], max_elapsed_seconds=86400, artifact_frequency=frequency, population_size=len(variants['full'])):
            pair = tuple(sorted((edge['source'], edge['target'])))
            key = sha256(json.dumps(pair))[:24]
            entry = union.setdefault(key, {'id': key, 'events': list(pair), 'pages': sorted({event_pages[e] for e in pair}), 'variants': [], 'label': 'unresolved'})
            entry['variants'].append(name)
    represented = {page for candidate in union.values() for page in candidate['pages']}
    return {'protocol': PROTOCOL, 'curated_overrides': False, 'held_out_pages': sorted(pages),
            'population_count': len(variants['full']), 'max_elapsed_seconds': 86400,
            'normalized_population_sha256': sha256(json.dumps(variants['full'], sort_keys=True)),
            'candidates': [union[k] for k in sorted(union)],
            'candidate_count': len(union), 'group_count': len(pages), 'candidate_group_count': len(represented),
            'target_met': 30 <= len(union) <= 50 and len(represented) >= 5,
            'label_status': 'unreviewed; no research metrics'}


def metrics(predicted, labels):
    if set(predicted) - set(labels):
        raise ValueError('Predictions outside reviewed union.')
    for row in labels.values():
        if row.get('label') not in {'supported', 'contradicted', 'unresolved'} or row.get('origin') not in {'automated', 'AI-assisted', 'human'} or not row.get('reviewer') or not row.get('rationale'):
            raise ValueError('Label requires valid status, origin, reviewer and rationale.')
    tp = sum(k in predicted and r['label'] == 'supported' for k, r in labels.items())
    fp = sum(k in predicted and r['label'] == 'contradicted' for k, r in labels.items())
    fn = sum(k not in predicted and r['label'] == 'supported' for k, r in labels.items())
    resolved = sum(r['label'] != 'unresolved' for r in labels.values())
    return {'tp': tp, 'fp': fp, 'fn': fn, 'precision': tp / (tp + fp) if tp + fp else None,
            'recall': tp / (tp + fn) if tp + fn else None,
            'unresolved_predicted': sum(k in predicted and r['label'] == 'unresolved' for k, r in labels.items()),
            'adjudicated_count': resolved, 'union_count': len(labels),
            'adjudicated_coverage': resolved / len(labels) if labels else None,
            'origins': dict(sorted(Counter(r['origin'] for r in labels.values()).items()))}


def evaluate_report(report, review):
    """Bind complete union review to the frozen report; never infer missing labels."""
    unsigned = {k: v for k, v in report.items() if k != 'candidate_report_sha256'}
    digest = sha256(json.dumps(unsigned, sort_keys=True))
    if report.get('candidate_report_sha256') != digest or review.get('candidate_report_sha256') != digest:
        raise ValueError('Review does not match the frozen candidate report.')
    rows = review.get('labels', [])
    ids = [r.get('id') for r in rows]
    union = {c['id'] for c in report['candidates']}
    if len(ids) != len(set(ids)) or set(ids) != union:
        raise ValueError('Review must cover the exact union once, including unresolved labels.')
    labels = {r['id']: r for r in rows}
    return {variant: metrics({c['id'] for c in report['candidates'] if variant in c['variants']}, labels) for variant in VARIANTS}


def run(raw_dir, episodes_path):
    acquisition = json.loads((raw_dir / 'acquisition.json').read_text())
    if acquisition.get('acquisition_mode') != 'public-redacted-dataset' or acquisition.get('source_url') != 'https://collusion.wiki/explorer/download':
        raise ValueError('Eligible public Collusion acquisition required.')
    records = acquisition.get('files', [])
    revisions_record = [r for r in records if r.get('filename') == 'revisions.jsonl.gz']
    if len(revisions_record) != 1:
        raise ValueError('Unique revisions provenance required.')
    for record in records:
        name = record['filename']
        if name not in ('revisions.jsonl.gz', 'events.jsonl.gz', 'manifest.json.gz', 'pages.jsonl.gz') or record['url'] != acquisition['source_url'] + '/' + name or sha256((raw_dir / name).read_bytes()) != record['sha256']:
            raise ValueError('Invalid source provenance or hash.')
    revisions = read_jsonl(raw_dir / 'revisions.jsonl.gz')
    demo_ids = {rid for episode in json.loads(episodes_path.read_text()) for rid in episode['revision_ids']}
    variants = extract_variants(revisions)
    normalized = variants['full']
    demo_pages = {e['page_key'] for e in normalized if e['source_revision_id'] in demo_ids}
    if not demo_ids <= {e['source_revision_id'] for e in normalized}:
        raise ValueError('Demo source IDs absent; cannot establish split.')
    eligible = sorted({e['page_key'] for e in normalized} - demo_pages)
    if not eligible:
        raise ValueError('No held-out public population available.')
    # Deterministic whole-group prefix; never optimize for variant performance.
    for count in range(min(5, len(eligible)), len(eligible) + 1):
        report = _candidate_report(variants, held_out_pages=eligible[:count], demo_revision_ids=demo_ids)
        if report['candidate_count'] >= 30 and report['candidate_group_count'] >= 5:
            break
    report['source_files'] = records
    report['available_eligible_groups'] = len(eligible)
    report['candidate_report_sha256'] = sha256(json.dumps(report, sort_keys=True))
    return report


def save_report(path, report):
    path = Path(path).absolute()
    payload = (json.dumps(report, indent=2) + '\n').encode()
    parent = open_directory(path.parent, create=True)
    created = False
    try:
        fd = os.open(path.name, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600, dir_fd=parent)
        created = True
        with os.fdopen(fd, 'wb') as stream:
            stream.write(payload)
            stream.flush()
            os.fsync(stream.fileno())
    except BaseException:
        if created:
            os.unlink(path.name, dir_fd=parent)
        raise
    finally:
        os.close(parent)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--raw-dir', type=Path, required=True)
    parser.add_argument('--episodes', type=Path, default=Path('data/episodes.json'))
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    try:
        report = run(args.raw_dir, args.episodes)
    except (FileNotFoundError, ValueError) as error:
        parser.error('Cannot run the benchmark: ' + str(error))
    save_report(args.out, report)


if __name__ == '__main__':
    main()
