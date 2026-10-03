# RelayTrace

An offline evidence explorer for information reuse between AI agents.

RelayTrace links an agent's recorded contribution to later references,
acknowledgements and claims of reuse. Each relation retains source records,
timestamps, provenance and a reason for its evidence status. It helps an
investigator inspect a proposed transmission chain without turning a matching
phrase or an agent's narration into proof of causal influence.

Built for the October 3–4, 2026 AI Swarm Dynamics Hackathon.

Repository: https://github.com/brunuff/Hackthon-relay-trace

## Try the demo

Download this repository as a ZIP, extract it, and open `RelayTrace_demo.html`.
It works offline and contains a small, real, attributed snapshot from the public Collusion.wiki
export. No installation, API key or model call is required.

You can also open `web/index.html`. Search, filter by episode, handle, relation
type or evidence status, and select a relation to inspect both records and
their source provenance. The JSON import operates locally in your browser.

## Reproduce the analysis

Requires Python 3.10 or later; the pipeline uses only the standard library.
Run from the project directory:

```sh
PYTHONPATH=src python3 -m swarm_tracer acquire
PYTHONPATH=src python3 -m swarm_tracer build
python3 build_release.py
```

Acquisition downloads only the fixed publisher export files, never URLs
embedded in agent text. Build verifies data integrity, normalizes contributions
between revisions, generates candidate relations and selects the curated
episodes. The release builder produces a standalone HTML demo and source ZIP
under `artifacts/`.

The original bulk export is not included in the release. Source links and
hashes are retained so another researcher can acquire and verify it.

## Evidence semantics

| Status | Meaning |
|---|---|
| Observed | A textual reference or acknowledgement is present in a source record. |
| Inferred | Shared distinctive material and usable chronology suggest a relation. |
| Unknown | Attribution or chronology is too uncertain to support an ordered relation. |

These labels apply to the observable relation, not to task success or causal
adoption. An explicit claim of reuse is still a claim. Private read receipts,
model context, independently verified actions and grader outcomes are not
available in this corpus. Different handles are not necessarily different
agent instances; the same handle is not necessarily one continuous instance.

Saved wiki revisions contain earlier contributions. The pipeline distinguishes
new material from inherited page text and suppresses matching signals carried
over during a replacement-line edit. Source timing grades and uncertainties
remain attached to events. The curated cases are selected examples, not a
random sample from which to estimate a universal propagation rate.

## Validate

```sh
PYTHONPATH=src python3 -m unittest discover -s tests -v
```

Tests cover false transmission from copied snapshots, unchanged artifacts in
replacement lines, generic shared words, missing or malformed times, identity
assumptions, data integrity, and untrusted-content boundaries. See
`docs/REVIEW.md` for the independent review and `docs/VALIDATION.md` for the
release checks.

## Data and limitations

The source is the public redacted export at
https://collusion.wiki/explorer/download. It contains 14,591 saved revisions;
the default demo shows selected evidence records rather than the entire corpus.
The export is incomplete for private agent state and other communication
channels. Missing evidence cannot establish that a transfer did not occur.

Original code is MIT licensed. Third-party evidence and datasets retain their
original rights and terms; see `DATA_NOTES.md`. No gated AI Village data is
included. Agent-authored content is displayed as literal text and never
executed.

## Next research step

With approved AI Village access, extend the same evidence model to connect a
message with a recipient's subsequent memory consolidation and computer
actions. Exact raw prompts are not in the ordinary dataset, so availability
and observed receipt must remain distinct. A controlled replay could later
test causal influence by comparing otherwise matched contexts with and without
the candidate message.

The current release does not resolve the July Hugging Face swarm's stopping
event or establish that an unrelated later agent adopted its collective goal.

## Submission materials

- `docs/SUBMISSION.md`: project description, demo walkthrough and remaining
  registration/submission inputs.
- `docs/RESEARCH.md`: current official schedule, forms, source links and data
  access conditions.
- `WORKFLOW.md`: work ownership, research contract and release gates.

Project concept: Bruno. Implementation and review: AI-assisted, with separate
data, interface, requirements and independent-review workstreams.
