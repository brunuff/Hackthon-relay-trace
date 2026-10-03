"""Synthetic behavior checks; these are not research validation."""
import unittest
from swarm_tracer import benchmark as b


def fixtures():
    return [{'rev_id': 'r1', 'page_key': 'held-a', 'seq': 1, 'label': 'A', 'time': '2026-01-01T00:00:00Z', 'body': 'value 12,345'},
            {'rev_id': 'r2', 'page_key': 'held-a', 'seq': 2, 'label': 'B', 'time': '2026-01-01T00:01:00Z', 'body': 'value 12,345 extra'},
            {'rev_id': 'r3', 'page_key': 'held-b', 'seq': 1, 'label': 'C', 'time': '2026-01-01T00:02:00Z', 'body': 'value 12,345'}]


class BenchmarkTests(unittest.TestCase):
    def test_split_leakage(self):
        with self.assertRaises(ValueError):
            b.candidate_report(fixtures(), held_out_pages=['held-a'], demo_revision_ids=['r1'])

    def test_deterministic_union(self):
        a = b.candidate_report(fixtures(), held_out_pages=['held-a', 'held-b'])
        self.assertEqual(a, b.candidate_report(list(reversed(fixtures())), held_out_pages=['held-b', 'held-a']))
        self.assertTrue(a['candidates'])
        self.assertTrue(all(c['label'] == 'unresolved' for c in a['candidates']))
        self.assertFalse(a['curated_overrides'])

    def test_variants(self):
        variants = b.extract_variants(fixtures())
        self.assertEqual(set(variants), {'full', 'lines', 'tokens'})
        self.assertEqual([e['id'] for e in variants['full']], [e['id'] for e in variants['tokens']])
        full = next(e for e in variants['full'] if e['source_revision_id'] == 'r2')
        tokens = next(e for e in variants['tokens'] if e['source_revision_id'] == 'r2')
        self.assertIn('12,345', full['matching_text'])
        self.assertNotIn('12,345', tokens['matching_text'])

    def test_metrics(self):
        labels = {k: {'label': v, 'origin': 'AI-assisted', 'reviewer': 'test', 'rationale': 'synthetic'} for k, v in [('a', 'supported'), ('b', 'contradicted'), ('c', 'supported'), ('d', 'unresolved')]}
        m = b.metrics({'a', 'b', 'd'}, labels)
        self.assertEqual((m['tp'], m['fp'], m['fn']), (1, 1, 1))
        self.assertEqual((m['precision'], m['recall']), (.5, .5))
        self.assertEqual(m['unresolved_predicted'], 1)
        self.assertIsNone(b.metrics(set(), {})['precision'])
        self.assertIsNone(b.metrics(set(), {})['recall'])

    def test_invalid_labels(self):
        for label in ({'label': 'negative', 'origin': 'human'}, {'label': 'supported', 'origin': 'automated'}, {'label': 'supported', 'origin': 'robot', 'reviewer': 'x', 'rationale': 'x'}):
            with self.assertRaises(ValueError):
                b.metrics({'a'}, {'a': label})
        with self.assertRaises(ValueError):
            b.metrics({'unknown'}, {})

    def test_review_bound_to_complete_union(self):
        from swarm_tracer.pipeline import sha256
        import json
        report = b.candidate_report(fixtures(), held_out_pages=['held-a', 'held-b'])
        report['candidate_report_sha256'] = sha256(json.dumps(report, sort_keys=True))
        rows = [{'id': c['id'], 'label': 'unresolved', 'origin': 'AI-assisted', 'reviewer': 'test', 'rationale': 'synthetic unknown'} for c in report['candidates']]
        review = {'candidate_report_sha256': report['candidate_report_sha256'], 'labels': rows}
        result = b.evaluate_report(report, review)
        self.assertTrue(all(m['precision'] is None and m['recall'] is None for m in result.values()))
        for bad in (review | {'labels': rows + rows}, review | {'labels': []}, review | {'candidate_report_sha256': 'wrong'}):
            with self.assertRaises(ValueError):
                b.evaluate_report(report, bad)

    def test_exclusive_report_creation(self):
        import tempfile
        from pathlib import Path
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            target = root / 'private-target.json'
            link = root / 'report.json'
            link.symlink_to(target)
            with self.assertRaises((ValueError, OSError)):
                b.save_report(link, {'synthetic': True})
            self.assertFalse(target.exists())
            link.unlink()
            link.write_bytes(b'prior report')
            with self.assertRaises((ValueError, OSError)):
                b.save_report(link, {'synthetic': True})
            self.assertEqual(link.read_bytes(), b'prior report')
            parent = root / 'symlink-parent'
            parent.symlink_to(root, target_is_directory=True)
            with self.assertRaises((ValueError, OSError)):
                b.save_report(parent / 'new.json', {'synthetic': True})
            self.assertFalse((root / 'new.json').exists())

    def test_report_creation_race_preserves_winner(self):
        import tempfile
        import os
        from pathlib import Path
        from unittest.mock import patch
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory).resolve() / 'report.json'
            real_open = os.open
            def raced(name, flags, *args, **kwargs):
                if name == 'report.json' and flags & os.O_CREAT:
                    path.write_bytes(b'concurrent winner')
                return real_open(name, flags, *args, **kwargs)
            with patch.object(b.os, 'open', side_effect=raced):
                with self.assertRaises(FileExistsError):
                    b.save_report(path, {'synthetic': True})
            self.assertEqual(path.read_bytes(), b'concurrent winner')
