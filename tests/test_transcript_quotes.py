"""Synthetic checks of citation ambiguity, literal data, clocks and publication."""
import importlib.util
from pathlib import Path
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location('audit_transcript_quotes', ROOT / 'audit_transcript_quotes.py')
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)
QUOTE = 'This distinctive synthetic explanation says the registry should preserve a previous state while the endpoint is being checked.'


def export(source_time='2026-03-31T17:22:21.029Z', duplicate=False, quoted=QUOTE, speaker='Alpha'):
    source = {'type': 'AGENT_TALK', 'timestamp': source_time, 'speakerName': 'Alpha', 'content': 'Before. ' + QUOTE + ' After.'}
    answer = '[Day 350, 17:22:21] ' + speaker + '\n> ' + quoted + '\n'
    result = {'days': [{'day': 350, 'events': [source, {'type': 'SEARCH_HISTORY', 'timestamp': '2026-03-31T18:04:02Z', 'agentName': 'Beta', 'query': 'SYNTHETIC test', 'answerToQuery': answer}]}]}
    if duplicate:
        result['days'][0]['events'].insert(1, dict(source))
    return result


class TranscriptQuoteTests(unittest.TestCase):
    def test_indented_room_and_speaker_prefix_preserves_literal_offsets(self):
        data = export()
        answer = '    [Day 350, 17:22:21]\n    > [#best] Alpha: ' + QUOTE + '\n    >\n    > A short continuation.\n'
        data['days'][0]['events'][1]['answerToQuery'] = answer
        row = MODULE.audit_export(data)['candidates'][0]
        self.assertEqual(row['citation_status'], 'unique-literal-match')
        self.assertEqual(row['cited_speaker_display_name'], 'Alpha')
        self.assertEqual(answer[row['answer_char_start']:row['answer_char_end']], QUOTE)

    def test_header_without_a_known_speaker_does_not_guess_identity(self):
        data = export()
        data['days'][0]['events'][1]['answerToQuery'] = '[Day 350, 17:22:21]\n> [#best] Gamma: ' + QUOTE + '\n'
        row = MODULE.audit_export(data)['candidates'][0]
        self.assertEqual(row['citation_status'], 'unresolved-citation')
        self.assertEqual(row['cited_speaker_display_name'], '')

    def test_unicode_line_separator_is_literal_quoted_content(self):
        quote = QUOTE + '\u2028' + QUOTE
        data = export(quoted=quote)
        data['days'][0]['events'][0]['content'] = quote
        row = MODULE.audit_export(data)['candidates'][0]
        self.assertEqual(row['quote'], quote)
        self.assertEqual(row['citation_status'], 'unique-literal-match')

    def test_exact_quote_offsets_and_record_chronology(self):
        result = MODULE.audit_export(export())
        row = result['candidates'][0]
        self.assertEqual(row['citation_status'], 'unique-literal-match')
        self.assertEqual(row['source_candidates'][0]['content_char_start'], 8)
        self.assertEqual(row['source_candidates'][0]['record_order'], 'source-earlier')
        self.assertFalse(row['receipt_verified'])
        self.assertFalse(row['causal_uptake_verified'])

    def test_duplicate_literal_source_is_ambiguous(self):
        row = MODULE.audit_export(export(duplicate=True))['candidates'][0]
        self.assertEqual(row['citation_status'], 'ambiguous-literal-match')
        self.assertEqual(len(row['source_candidates']), 2)

    def test_repeated_passage_in_one_source_keeps_both_offsets(self):
        data = export()
        data['days'][0]['events'][0]['content'] = QUOTE + '\n' + QUOTE
        row = MODULE.audit_export(data)['candidates'][0]
        self.assertEqual(row['citation_status'], 'ambiguous-literal-match')
        self.assertEqual([x['content_char_start'] for x in row['source_candidates']], [0, len(QUOTE) + 1])

    def test_wrong_speaker_or_rewritten_quote_does_not_match(self):
        self.assertEqual(MODULE.audit_export(export(speaker='Gamma'))['candidates'][0]['citation_status'], 'unresolved-citation')
        self.assertEqual(MODULE.audit_export(export(quoted=QUOTE.upper()))['candidates'][0]['citation_status'], 'unresolved-citation')

    def test_future_and_naive_source_time_cannot_prove_earlier_order(self):
        self.assertEqual(MODULE.audit_export(export(source_time='2026-03-31T19:00:00Z'))['candidates'][0]['source_candidates'][0]['record_order'], 'source-not-earlier')
        self.assertEqual(MODULE.audit_export(export(source_time='2026-03-31T17:22:21'))['candidates'][0]['source_candidates'][0]['record_order'], 'unresolved')

    def test_window_filters_summary_but_keeps_prior_source(self):
        row = MODULE.audit_export(export(), start=MODULE.utc_time('2026-03-31T18:00:00Z'))['candidates'][0]
        self.assertEqual(row['citation_status'], 'unique-literal-match')
        self.assertEqual(MODULE.audit_export(export(), end=MODULE.utc_time('2026-03-31T18:04:02Z'))['candidates'], [])

    def test_short_quotes_not_promoted_and_unicode_offsets_exact(self):
        self.assertEqual(MODULE.audit_export(export(quoted='Thanks for the idea'))['candidates'], [])
        data = export()
        data['days'][0]['events'][0]['content'] = 'é🙂 ' + QUOTE
        self.assertEqual(MODULE.audit_export(data)['candidates'][0]['source_candidates'][0]['content_char_start'], 3)

    def test_embedded_code_is_data_and_existing_output_survives(self):
        with tempfile.TemporaryDirectory() as tmp:
            marker = Path(tmp) / 'executed'
            payload = "__import__('pathlib').Path(" + repr(str(marker)) + ").write_text('bad'); " + QUOTE
            data = export(quoted=payload)
            data['days'][0]['events'][0]['content'] = payload
            result = MODULE.audit_export(data)
            self.assertFalse(marker.exists())
            output = Path(tmp) / 'audit.json'
            MODULE.atomic_write(output, result)
            previous = output.read_bytes()
            with self.assertRaises(ValueError):
                MODULE.atomic_write(output, {})
            self.assertEqual(output.read_bytes(), previous)


if __name__ == '__main__':
    unittest.main()
