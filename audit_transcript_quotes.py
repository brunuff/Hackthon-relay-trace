#!/usr/bin/env python3
"""Audit literal citations in local AI Village history answers. No code or URLs are executed."""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import tempfile

HEADER = re.compile(r'^[ \t]*\[Day (\d+), (\d{2}:\d{2}:\d{2})\][ \t]*([^\n]*)\n((?:[ \t]*>[^\n]*(?:\n|$))+)', re.MULTILINE)
QUOTE_LINE = re.compile(r'^[ \t]*> ?')
MIN_QUOTE_CHARS = 80


def canonical_hash(value: object) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(',', ':')).encode('utf-8')).hexdigest()


def utc_time(value: object) -> datetime | None:
    if not isinstance(value, str):
        return None
    try:
        parsed = datetime.fromisoformat(value.replace('Z', '+00:00'))
    except ValueError:
        return None
    return parsed.astimezone(timezone.utc) if parsed.tzinfo is not None else None


def audit_export(data: dict, *, start: datetime | None = None, end: datetime | None = None,
                 max_events: int = 500000) -> dict:
    if not isinstance(data, dict) or not isinstance(data.get('days'), list):
        raise ValueError('Expected a rendered transcript with a days array')
    sources = defaultdict(list)
    summaries = []
    types = Counter()
    event_count = 0
    for di, day in enumerate(data['days']):
        if not isinstance(day, dict) or not isinstance(day.get('events'), list):
            raise ValueError('Invalid day group at index ' + str(di))
        for ei, event in enumerate(day['events']):
            if not isinstance(event, dict):
                raise ValueError('Invalid event at /days/' + str(di) + '/events/' + str(ei))
            event_count += 1
            if event_count > max_events:
                raise ValueError('Event cap exceeded')
            kind = event.get('type', '<missing>')
            if not isinstance(kind, str):
                raise ValueError('Event type must be a string')
            types[kind] += 1
            pointer = '/days/' + str(di) + '/events/' + str(ei)
            if kind == 'AGENT_TALK' and isinstance(event.get('speakerName'), str) and isinstance(event.get('content'), str):
                sources[(day.get('day'), event['speakerName'])].append((pointer, event))
            if kind == 'SEARCH_HISTORY' and isinstance(event.get('answerToQuery'), str):
                summaries.append((pointer, event))

    candidates = []
    checked = 0
    header_count = 0
    short_quotes = 0
    statuses = Counter()
    for pointer, event in summaries:
        when = utc_time(event.get('timestamp'))
        if start is not None and (when is None or when < start):
            continue
        if end is not None and (when is None or when >= end):
            continue
        checked += 1
        answer = event['answerToQuery']
        for header in HEADER.finditer(answer):
            header_count += 1
            day, clock, label = int(header.group(1)), header.group(2), header.group(3).strip()
            quoted = header.group(4)
            # One export shape puts the room/name on the first quoted line.
            # Resolve only an exact existing display label, never an alias.
            inline_label = not label
            day_labels = [name for source_day, name in sources if source_day == day]
            first_line = True
            # Preserve each exported quotation line literally after its quote marker.
            # Wrapped/rewritten passages are not silently normalized into exact matches.
            cursor = header.start(4)
            for line in re.findall(r'[^\n]*(?:\n|$)', quoted):
                if not line:
                    continue
                raw = line.rstrip('\r\n')
                marker_chars = QUOTE_LINE.match(raw).end()
                text = raw[marker_chars:]
                answer_start = cursor + marker_chars
                cursor += len(line)
                if first_line and inline_label:
                    room = re.match(r'^\[#[^\]\n]+\] ', text)
                    prefix_start = room.end() if room else 0
                    known = [name for name in day_labels if text[prefix_start:].startswith(name + ': ')]
                    if len(known) == 1:
                        label = known[0]
                        prefix_size = prefix_start + len(label) + 2
                        text = text[prefix_size:]
                        answer_start += prefix_size
                first_line = False
                if len(text) < MIN_QUOTE_CHARS:
                    short_quotes += 1
                    continue
                matches = []
                for source_pointer, source in sources.get((day, label), []):
                    offset = source['content'].find(text)
                    source_when = utc_time(source.get('timestamp'))
                    delta = (when - source_when).total_seconds() if when and source_when else None
                    source_clock = source_when.strftime('%H:%M:%S') if source_when else None
                    while offset >= 0:
                        matches.append({'source_json_pointer': source_pointer,
                            'source_timestamp': source.get('timestamp'), 'source_event_canonical_sha256': canonical_hash(source),
                            'content_char_start': offset, 'content_char_end': offset + len(text),
                            'seconds_between_recorded_timestamps': delta,
                            'record_order': 'source-earlier' if delta is not None and delta > 0 else 'source-not-earlier' if delta is not None else 'unresolved',
                            'header_clock_equals_source_event_second': source_clock == clock if source_clock else None})
                        offset = source['content'].find(text, offset + 1)
                status = 'unique-literal-match' if len(matches) == 1 else 'ambiguous-literal-match' if matches else 'unresolved-citation'
                statuses[status] += 1
                candidates.append({'summary_json_pointer': pointer, 'summary_timestamp': event.get('timestamp'),
                    'summary_agent_display_name': event.get('agentName'), 'summary_event_canonical_sha256': canonical_hash(event),
                    'recorded_query': event.get('query'), 'cited_day': day, 'cited_clock': clock, 'cited_speaker_display_name': label,
                    'answer_char_start': answer_start, 'answer_char_end': answer_start + len(text),
                    'quote': text, 'quote_sha256_utf8': hashlib.sha256(text.encode()).hexdigest(),
                    'citation_status': status, 'source_candidates': matches,
                    'receipt_verified': False, 'causal_uptake_verified': False})
    return {'schema_version': 'relaytrace.transcript-quote-audit.v1', 'private_working_data': True,
        'access_class': 'restricted-research', 'synthetic': False,
        'counts': {'export_events': event_count, 'event_types': dict(types), 'history_answers_total': len(summaries),
                   'history_answers_checked': checked, 'recognized_quote_headers': header_count,
                   'short_quote_lines_excluded': short_quotes, 'candidate_quote_lines': len(candidates), 'citation_statuses': dict(statuses)},
        'method': {'minimum_quote_characters': MIN_QUOTE_CHARS, 'source_basis': 'same exported day number and literal speaker label, with exact quotation substring',
                   'window_applies_to': 'history answers; all earlier/later source chat remains available as context',
                   'start_inclusive': start.isoformat() if start else None, 'end_exclusive': end.isoformat() if end else None},
        'limitations': ['This audits literal citations, not truth, belief, memory injection or causal transmission.',
                       'Names are display labels. No stable agent UUID or session/foreign-key join is inferred.',
                       'A unique source match is not an independent receipt record; shared inputs and prior discussion remain alternatives.',
                       'Only bracketed Day/time with a header speaker or first quoted room/speaker prefix is recognized. Indentation and quote markers are removed; quoted content is otherwise literal. Unrecognized, short, wrapped or paraphrased citations are not silently repaired.',
                       'Cited time and source event time are separate; exact-second differences can reflect different export clocks.',
                       'Event hashes are canonical JSON hashes, not original source byte-slice hashes.',
                       'Counts describe recognized citation candidates and do not estimate propagation prevalence.'],
        'candidates': candidates}


def atomic_write(destination: Path, payload: dict) -> None:
    if destination.exists():
        raise ValueError('Refusing to overwrite ' + str(destination))
    destination.parent.mkdir(parents=True, exist_ok=True)
    staged = None
    try:
        with tempfile.NamedTemporaryFile('w', encoding='utf-8', dir=destination.parent, delete=False) as stream:
            staged = Path(stream.name)
            os.chmod(staged, 0o600)
            json.dump(payload, stream, ensure_ascii=False, indent=2)
            stream.write('\n')
        # Same-directory hard link publishes without replacing a concurrently created file.
        os.link(staged, destination)
    finally:
        if staged is not None:
            staged.unlink(missing_ok=True)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('transcript', type=Path)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--start')
    parser.add_argument('--end')
    args = parser.parse_args()
    try:
        start, end = utc_time(args.start), utc_time(args.end)
        if (args.start and start is None) or (args.end and end is None):
            raise ValueError('Window timestamps require valid explicit UTC offsets')
        if start and end and start >= end:
            raise ValueError('Start must precede end')
        if args.output.exists():
            raise ValueError('Refusing to overwrite output')
        if args.transcript.stat().st_size > 1024**3:
            raise ValueError('Transcript exceeds the 1 GiB local parse cap')
        raw = args.transcript.read_bytes()
        if len(raw) > 1024**3:
            raise ValueError('Transcript exceeds the 1 GiB local parse cap')
        byte_count = len(raw)
        digest = hashlib.sha256(raw).hexdigest()
        data = json.loads(raw)
        del raw
        result = audit_export(data, start=start, end=end)
        result['source'] = {'path': str(args.transcript), 'bytes': byte_count, 'sha256': digest,
                            'upstream_revision_authenticated': False}
        atomic_write(args.output, result)
    except (OSError, ValueError) as exc:
        parser.exit(2, 'Audit rejected: ' + str(exc) + '\n')
    print(json.dumps({'output': str(args.output), 'counts': result['counts']}))


if __name__ == '__main__':
    main()
