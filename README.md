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

## AI Village local importer

The optional adapter now follows the supplied AI Village column schema and
has been checked against the supplied agent registry, manifest, and chat table. It uses
UUID identity links and preserves source row/file hashes. Synthetic tests
cover chat, memory snapshots, session intentions, executed actions,
provider-shaped responses, and tool outputs. No restricted AI Village rows or
transmission findings are included in this release.

Put approved local tables under `data/raw/ai-village/`, then run:

```sh
PYTHONPATH=src python3 -m swarm_tracer.ai_village \
  --input-dir data/raw/ai-village \
  --start 2026-05-29T07:00:00Z --end 2026-06-03T07:00:00Z \
  --out data/processed/ai-village-evidence.json
```

This streams source rows and bounds the selected output, requiring session
parents for selected turns. It makes no network requests and generates no
transmission edges. The dates above produce an exploration slice. For a small
pilot crop containing memory baselines just outside the interval, omit date
flags and preserve those context records; otherwise new-memory claims lack
their requested comparison. Current row content can reflect later updates,
which remain explicit in provenance.

The chat table and a 146-row memory crop have been supplied and validated
locally. The reviewed case remains private. If the full memory archive is too large to transfer, use the standalone local
filter (Python 3.10+, no extra packages):

```sh
python3 crop_ai_village_memories.py data/raw/ai-village/agent_memories.jsonl.gz \
  --agents data/raw/ai-village/agents.jsonl.gz --calendar-pilot
```

This creates a compressed crop and selection report beside the source file,
preserving nearest memory snapshots before and after the June 1-2 window.
The preset resolves exact export-time labels to UUIDs and rejects ambiguity.
See the [transfer instructions](docs/AI_VILLAGE_INPUTS.md#when-the-memory-archive-is-too-large).

Reviewed textual associations can use `directed: false` with
`ordering_status: "known"`. The viewer then shows record chronology without a
transport arrow. A matching correction in a later memory, even with a named
corrector, does not identify the exact source message or establish delivered
model context.

The supplied rendered transcript adds history-search and consolidation event
context, but lacks row IDs and agent UUIDs. It is not a replacement for raw
computer-use turns. Events and goals add
context; sessions and turns add action evidence. Event-table importing is not
implemented yet. See [input requirements](docs/AI_VILLAGE_INPUTS.md),
[metadata checks](docs/AI_VILLAGE_VALIDATION.md), and
[the pilot protocol](docs/AI_VILLAGE_PILOT.md).

The standalone [literal citation audit](docs/TRANSCRIPT_CITATION_AUDIT.md)
checks quoted history-answer lines against the supplied transcript, preserving
source/answer spans, ambiguity and recorded clocks. It helps review a source,
returned summary and later response alongside prior recipient statements and
direct corrections. A literal match establishes textual correspondence; receipt
and causal uptake remain unverified. Its outputs can contain restricted excerpts
and must stay private.

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
