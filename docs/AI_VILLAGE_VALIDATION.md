# AI Village input validation

On October 3, 2026, the project owner supplied the publisher's schema,
manifest, changelog, example, compressed agent table, chat table, memory crop
with selection report, and rendered transcript for local analysis.
These source files remain outside the public repository and release archive.
These are input checks, not transmission findings.

The local importer is implemented with 21 clearly synthetic adapter tests.
The memory crop helper adds seven synthetic boundary/transfer tests.
The citation audit adds 11 synthetic source-span and literal-data tests.
All 62 repository tests pass, including the existing viewer/data-boundary
checks. A CLI import of the actual supplied agents and manifest produces 46
agent metadata entries and zero behavioral records or relations. The supplied
chat table also imports successfully. The actual 146-row memory crop also
imports successfully with no automatically inferred relations. Session/turn
support remains tested against synthetic fixtures until those actual rows arrive.

## Checks performed on actual supplied data

| Check | Result |
| --- | --- |
| Manifest export time | `2026-09-20T13:05:12.097Z` |
| Agent rows | 46; matches the manifest |
| Agent identifiers | 46 unique, canonical UUIDs |
| Village identity | Every agent's village ID matches the manifest |
| Columns | Documented identity, name, model, and timestamp fields are present |
| Export-only URL fields | Both URL fields listed as dropped are absent |
| Timestamp precision | Supplied values include fractional seconds of differing lengths |
| Repository revision | Not supplied; unknown |
| Chat rows | 183,485 unique IDs; matches the manifest |
| Chat identities | All agent speaker IDs resolve to the supplied agent registry |
| Memory crop | 146 unique rows; all raw line hashes match the supplied selection report |
| Memory selection roles | 140 in-window, three preceding, three following |
| Rendered transcript | 375,426 events in 404 day groups; lacks source row IDs and agent UUIDs |
| Other raw behavioral tables | Full memory table, events table, sessions and turns not yet retrieved |

The manifest reports 183,485 chat messages, 246,151 memories, 381,610 events,
78,362 computer-use sessions, and 2,510,487 turns. These are expected export
counts. Chat and the memory crop have been independently validated. The
selection report lists 246,151 full-source memories, but that complete file
has not been independently checked. The rendered transcript is a separate
export format; its event count is not the raw events-table count. The schema's
approximate table sizes are older than this manifest; do not hard-code them
as validation limits.

## Local source fingerprints

| Source | SHA-256 |
| --- | --- |
| Schema | `50f27bda7b862723b8d47d7f7652a6b1c0e0ce9d7c5db572252da4d886bd9903` |
| Manifest | `28383809e34d38f00037dd31d830fa9b826b59fd91c0460e03efcbed6ee9e332` |
| Compressed agents | `b7af5dd3bed6f58d0f7627706b103bdba387ed678d6ac9caf5f084799dec0350` |
| Changelog | `65cac86a5ace6442879331ca7aadc7a46d4c77f7dd59979865cce708661e63d5` |
| Example | `af38b153448e4ff73fba44ae5b35c6c73d0de1ec964439ace9008d477d070a3c` |
| Compressed chat | `c1d56ab7b437f65c985c3353697d92f668f3a7b83776913aa5e3eb93ed867bb7` |
| Compressed memory crop | `20246eec0ae198c02bb846afa8e8e909b1c80eff4d2257f242ac7c061cdcbe46` |
| Memory selection report | `27b17aae4758416da17ca8498696d5ff60bdf412ad852e64f35d6447e35e727a` |
| Rendered transcript | `d29760ff9f15603d0dd64570884e5cb2126d1d1bb033b2c621134a65b58a6ee0` |

The memory crop helper is original project code. Its synthetic checks cover
unsorted rows, boundary ties, inclusive/exclusive timestamps, UTC offsets,
missing context, compressed/plain inputs, corrupt gzip, selected-row limits,
overwrite refusal, ambiguous labels, and reimported mutation warnings.
The calendar preset's three exact labels resolve to three distinct UUIDs in
the supplied agent registry. The user ran the extraction locally; all 146
supplied selected rows agree with the report's IDs, agent IDs, timestamps and
source-line hashes. This verifies crop/report consistency, not full-source
authenticity. All 114 memory-review excerpts were independently checked at
their exact character offsets. The reviewed content and source excerpts are
not included in the public repository or demo.

The viewer now distinguishes known record chronology from transport direction.
An explicitly reviewed undirected association can have ordered record
timestamps; it displays earlier/later records without a transport arrow.
Synthetic DOM checks cover known chronology with nullable uncertainty,
unresolved associations, invalid/reversed/equal times and uncertainty overlap.

The publisher's example was read without execution. It operates on the
rendered transcript and does not validate raw table joins or memory exposure.

The original [citation checker](TRANSCRIPT_CITATION_AUDIT.md) also ran on the
actual supplied rendered transcript. Its two explicit citation shapes were
checked against real source/answer spans. Coverage is limited to recognized
literal quotations; unresolved candidates are not automatically incorrect.
Source excerpts and the audit output remain private. It does not establish
causal transmission or infer session/UUID joins.

## Implications for the initial pilot

The changelog describes chat rooms as filtering perceived messages by current
room from February 25, 2026. Room availability is therefore contextual;
membership and timestamps alone cannot reconstruct an exact model input.

It also lists an own-message turn-windowing fix on June 1 and an Anthropic
multiple-tool-result history fix on June 2. These overlap the selected
Geological Clock window and must be annotated. The changelog explicitly says
it was generated by an LLM from private git history and dates changes by when
they landed on the main branch. Deployment time and actual effects on a given
turn are not established by that description.

Stable UUIDs establish dataset-entity attribution. Export-time model/name
fields do not establish historical prompt contents or an unchanged model
version. Memories cannot be joined directly to sessions or consolidation
events because the schema supplies no such foreign key.

Attribution: AI Digest / AI Village, publisher-supplied export documentation
agent registry, and chat export. Dataset: https://huggingface.co/datasets/aidigestorg/ai-village.
