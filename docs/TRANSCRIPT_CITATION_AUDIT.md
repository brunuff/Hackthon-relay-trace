# Audit literal history citations locally

`audit_transcript_quotes.py` checks quotations in an authorized local AI Village
rendered transcript. It preserves source and answer character spans, canonical
event hashes, the input byte fingerprint and both recorded timestamps. It makes
no network requests and treats transcript content as literal data.

```sh
python3 audit_transcript_quotes.py /path/to/transcript.json \
  --start 2026-03-31T00:00:00Z --end 2026-04-01T00:00:00Z \
  --output /private/path/citation-audit.json
```

Window bounds require explicit timezone offsets. Start is inclusive and end is
exclusive. They select returned history answers; source chat outside the window
is retained for comparison. The tool refuses existing output, limits input to
1 GiB and caps events at 500,000. These are local resource bounds, not expected
dataset sizes. Output can contain restricted source excerpts: keep it private.

Two explicit citation shapes are recognized: a bracketed Day/time header with
the speaker on that line, or a speaker prefix on the first quoted line, optionally
following a `[#room]` prefix. Indentation and Markdown quote markers are removed.
Quoted content is otherwise preserved literally. Speaker resolution requires an
exact exported display label on that day; aliases and model identities are not
inferred. Lines shorter than 80 characters are excluded.

Each candidate is an exact quoted line matched to same-day, same-label source
chat. One source span is `unique-literal-match`; multiple spans are
`ambiguous-literal-match`; zero spans are `unresolved-citation`. Repeated passages
in the same event retain all offsets. Source timestamps, cited header clocks and
answer timestamps remain separate. Future or missing timestamps cannot establish
earlier record chronology. Receipt and causal-uptake flags remain false.

An unresolved citation is not automatically a false quote. Summaries may
paraphrase, combine passages, use other citation shapes, quote human messages or
change formatting. This checker deliberately leaves such cases unresolved.
Coverage counts are counts of recognized candidates, not error rates or
propagation estimates. Canonical event hashes are hashes of reserialized JSON,
not original byte slices or independent authentication.

## Review the full episode

1. Inspect the literal source and returned answer, including attribution and
   qualifications. An assertive self-report repeated by a summary is still a
   self-report unless independently grounded.
2. Check the query's requested range against the timestamps actually cited.
3. Read the recipient's earlier statements and available memory baselines.
   A matching earlier explanation prevents treating later repetition as newly
   introduced adoption.
4. Look for intervening direct correction, common artifacts, shared goals and
   competing explanations. Retain counterevidence and failed candidates.
5. Inspect later chat, typed consolidation narration and available memory
   snapshots separately. A consolidation event does not establish a reset or a
   memory-row linkage. Mixed retained wording can defeat a clean-update claim.
6. Represent reviewed textual correspondences as undirected associations with
   known record chronology when supported. Do not turn a literal source match
   into a claim of delivered prompt, causal influence or successful action.

This workflow complements the raw-table importer and memory crop helper.
Private case packets can be imported into the offline viewer. The public demo
continues to use the previously reviewed public snapshot; gated transcript
excerpts and private review packets are not included.

The synthetic test suite covers literal spans, two citation shapes, Unicode,
ambiguity, repeated passages, wrong labels, changed wording, clock uncertainty,
window context, embedded commands as data and overwrite refusal. Run it with
the repository's standard command:

```sh
PYTHONPATH=src python3 -m unittest discover -s tests -v
```
