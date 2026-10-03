# AI Village input checklist

The project owner supplied the publisher's `SCHEMA.md` on October 3, 2026.
Its SHA-256 is `50f27bda7b862723b8d47d7f7652a6b1c0e0ce9d7c5db572252da4d886bd9903`.
This supports implementation against the documented columns. The owner also
supplied a manifest identifying an export at `2026-09-20T13:05:12.097Z`, the
agent table, changelog, and example. See [metadata validation](AI_VILLAGE_VALIDATION.md).
The source repository commit is still unknown. The chat table has since been
supplied and checked locally. A 146-row memory crop and two additional
recipient crops of 28 and nine rows have been validated locally; the rendered
transcript is also available as context. Full memory-table bytes and raw action
tables remain unverified or pending in this workspace. All crops and case
reports stay private.
The supplied schema itself is not redistributed in this repository.

## Small files received

| File | Purpose |
| --- | --- |
| `manifest.json` | Export time, village ID, row counts, and dropped columns. |
| `CHANGELOG.md` | Historical agent roster and changes to memory, prompts, and scaffolding. |
| `agents.jsonl.gz` | Canonical agent UUIDs and the metadata present at export. |
| `example.py` | Optional: the publisher's example for loading and interpreting its export. |

All four files above have been received and inspected. The example was read,
not executed. Keep the schema, manifest, and tables from the same dataset revision when
possible. If the revision is unavailable, record that limitation explicitly;
a schema hash is not a substitute for an export identifier.

## First real trace

`chat_messages.jsonl.gz` has been supplied. Provide `agent_memories.jsonl.gz`
only if a further approved analysis requires it; the three supplied crops
already support local memory comparisons. Add `events.jsonl.gz` when available. Chat and memories let us inspect a shared
statement and later recorded retention. Events supply canonical event order,
chat cross-references, and consolidation context. Compare duplicate chat
content across the two tables and expose conflicts or missing references.

The initial pilot covers May 29 through June 2, 2026 in America/Los_Angeles:
`2026-05-29T07:00:00Z <= created_at < 2026-06-03T07:00:00Z`.
Full files can be filtered locally. For a cropped export, also include the
most recent preceding memory and the next available memory after the window
for each relevant agent. Mark missing boundary records explicitly.

The initial adapter supports agents, chat, memories, sessions, and turns. It
does not yet import `events.jsonl.gz`; validating canonical event ordering and
consolidation context against that table is a subsequent step.

Its `--start`/`--end` flags filter every behavioral table by row creation time
and drop memory boundary records outside that interval. Import a small,
boundary-inclusive cropped pilot without those flags to preserve the requested
baseline and following context. Record the narrower analysis interval
separately. For full exports, the date-filtered output is an exploration slice;
obtain wider memory context before adjudicating newly retained content.

Add the small `village_goals.jsonl.gz` and `agent_goals.jsonl.gz` before
interpreting a candidate transfer. Shared goals can independently explain
similar language or behavior.

## When the memory archive is too large

The standalone `crop_ai_village_memories.py` reads the local archive in one
pass and does not authenticate, download, or upload anything. It needs Python
3.10+ and no additional packages. On a computer, place it alongside the source
memory and agent files and run:

```sh
python3 crop_ai_village_memories.py agent_memories.jsonl.gz \
  --agents agents.jsonl.gz --calendar-pilot
```

The calendar preset selects exact export labels Claude Opus 4.7, DeepSeek-V3.2,
and Gemini 3.1 Pro, resolving them to UUIDs from the supplied agent registry.
It uses `2026-06-01T17:00:00Z <= created_at < 2026-06-02T21:00:00Z`. Labels are
export metadata, not evidence of a historical model version. Missing or
ambiguous labels cause an error; the generic `--agent-id`, `--start`, and
`--end` options can select other validated entities and windows.

The helper produces `agent_memories-pilot.jsonl.gz` and
`agent_memories-pilot.jsonl.gz.selection.json` beside its input. Transfer only
those two files for local analysis. Their actual sizes are reported at
completion; no particular size or runtime is promised for an unseen source.
Keep both outputs out of the public repository and release.

The selection includes every memory in the interval and each selected agent's
nearest preceding/following snapshots, including ties. It scans the entire
source to handle unsorted rows, validates gzip completion, hashes the source
compressed bytes, and preserves selected JSON bytes and original row positions
in the report. Existing output files are refused. Missing boundaries are
reported. A default 10,000-row output limit prevents an accidentally broad crop.

**Import the crop separately without date filters**, supplying the agent
registry. The importer will sort by creation time; crop-file order is not
canonical event order. The report ties each cropped row back to the original
source hash and position. Preserve `updated_at` warnings: a nearest preceding
row can still contain later-edited content and cannot by itself prove a
historical memory baseline.

## Action evidence after selecting a candidate

Add `computer_use_sessions.jsonl.gz` and `computer_use_turns.jsonl.gz` for the
relevant agents and interval. A cropped turn export must include the parent
session for every retained turn, even if that session began before the date
window. Include the complete agent identity table as well.

The turn's `agent_action` is documented as the executed action. Preserve it
separately from provider-shaped `agent_messages`, tool `output`, `error`, and
`system` notes. A recorded action does not imply success or a causal link to
an earlier message. Request individual screenshots only when a concrete
disputed action requires them; the bulk image archive is unnecessary initially.

## Joins and evidence limits

| Record | Documented identity link |
| --- | --- |
| Agent chat | `agent_speaker_id` to `agents.id` |
| Memory | `agent_id` to `agents.id` |
| Computer session | `agent_id` to `agents.id` |
| Computer turn | `session_id` to sessions, then the session's `agent_id` |
| Chat event | `data.messageId` to chat, with `data.speakerId` for agent chat |

The schema defines its timestamps without a timezone suffix as UTC. This
convention belongs to this adapter and does not change the generic wiki
timestamp policy.

Memories have no session or consolidation foreign key. Temporal alignment
with `CONSOLIDATE` is an inference; the schema also does not specify whether
its `computerUseSessionId` names the old or new session. The ordinary export
cannot establish the exact memory supplied to a later model call.

An agent UUID identifies a dataset entity. Export-time name and model fields
do not establish which model/version produced every historical row. Tables
are dumped sequentially from a live database, so count differences and partial
coverage must be reported rather than concealed with guessed joins.

Keep approved local inputs under `data/raw/ai-village/` and analysis output
under an ignored private directory or `data/processed/`. Raw files and non-demo
processed output are ignored by Git and absent from the exact release allowlist.
Unexpected paths never enter the release automatically. The builder accepts
only the hash-approved public Collusion demo, after provenance validation. Do not replace the reviewed public demonstration with
synthetic fixtures or unreviewed gated records.
