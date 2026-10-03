"""Tests that distinguish source snapshots, textual relations and causal claims."""

import unittest

from swarm_tracer.pipeline import DatasetRedirectHandler, generate_edges, normalize_revisions


def revision(rid, text, actor="Alpha", stamp="2026-06-20T12:00:00Z", page="dse~One", seq=1, **extra):
    return {"rev_id": rid, "body": text, "label": actor, "time": stamp, "page_key": page, "seq": seq, **extra}


class PipelineTests(unittest.TestCase):
    def test_cross_origin_redirect_is_rejected_before_request(self):
        with self.assertRaises(ValueError):
            DatasetRedirectHandler().redirect_request(None, None, 302, "Found", {}, "https://unapproved.invalid/payload")

    def test_http_downgrade_is_rejected_before_request(self):
        with self.assertRaises(ValueError):
            DatasetRedirectHandler().redirect_request(None, None, 302, "Found", {}, "http://collusion.wiki/payload")

    def test_backward_input_is_ordered_by_publisher_time(self):
        records = [
            revision("b", "Used Alpha's https://example.invalid/specific?answer=4719021", "Beta", "2026-06-20T12:03:00Z", "dse~Two"),
            revision("a", "https://example.invalid/specific?answer=4719021"),
        ]
        events = normalize_revisions(records)
        edge = generate_edges(list(reversed(events)))[0]
        by_id = {event["id"]: event for event in events}
        self.assertEqual(by_id[edge["source"]]["source_revision_id"], "a")
        self.assertEqual(edge["seconds_elapsed"], 180)
        self.assertEqual(edge["status"], "observed")
        self.assertFalse(edge["causal_uptake_observed"])

    def test_same_handle_is_not_cross_handle_transmission(self):
        events = normalize_revisions([
            revision("a", "https://example.invalid/unique-answer?id=4719021"),
            revision("b", "Alpha: https://example.invalid/unique-answer?id=4719021", stamp="2026-06-20T12:03:00Z", page="dse~Two"),
        ])
        self.assertEqual(generate_edges(events), [])

    def test_duplicate_rows_have_stable_ids(self):
        item = revision("a", "Original")
        self.assertEqual(normalize_revisions([item]), normalize_revisions([item, item]))

    def test_hunks_extract_only_the_added_writer_line(self):
        old = revision("a", "Alpha posted a shared result.\n", diff_base=None, diff_base_reason="page_created", hunks=[{"op": "insert", "b0": 0, "b1": 1}])
        new = revision("b", "Alpha posted a shared result.\nBeta responds with a question.", "Beta", "2026-06-20T12:03:00Z", seq=2, diff_base="a", hunks=[{"op": "insert", "b0": 1, "b1": 2}])
        events = normalize_revisions([old, new])
        later = next(event for event in events if event["source_revision_id"] == "b")
        self.assertEqual(later["text"], "Beta responds with a question.")
        self.assertNotIn("shared result", later["text"])

    def test_missing_base_does_not_invent_added_content(self):
        events = normalize_revisions([revision("a", "Unresolved inherited snapshot", diff_base="missing", hunks=[{"op": "insert", "b0": 0, "b1": 1}])])
        self.assertEqual(events[0]["text"], "")
        self.assertEqual(events[0]["provenance"]["extraction"], "missing-diff-base")

    def test_overlap_in_timestamp_uncertainty_is_undirected(self):
        url = "https://example.invalid/unique-answer?id=4719021"
        events = normalize_revisions([
            revision("a", url, uncertainty_seconds=10),
            revision("b", "Alpha: " + url, "Beta", "2026-06-20T12:00:05Z", "dse~Two", uncertainty_seconds=10),
        ])
        edge = generate_edges(events)[0]
        self.assertEqual(edge["status"], "unknown")
        self.assertFalse(edge["directed"])
        self.assertIsNone(edge["seconds_elapsed"])

    def test_known_same_time_is_not_assigned_direction(self):
        url = "https://example.invalid/unique-answer?id=4719021"
        events = normalize_revisions([revision("a", url), revision("b", "Alpha: " + url, "Beta", page="dse~Two")])
        edge = generate_edges(events)[0]
        self.assertEqual(edge["status"], "unknown")
        self.assertFalse(edge["directed"])

    def test_independent_sequence_agreement_stays_unknown(self):
        sequence = "Massachusetts -> Connecticut -> Michigan -> West Virginia"
        events = normalize_revisions([revision("a", sequence), revision("b", "Confirmed independently: " + sequence, "Beta", "2026-06-20T12:03:00Z", "dse~Two")])
        edge = generate_edges(events)[0]
        self.assertEqual(edge["edge_type"], "independent_agreement")
        self.assertEqual(edge["status"], "unknown")
        self.assertFalse(edge["directed"])


if __name__ == "__main__":
    unittest.main()
