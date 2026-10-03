# AI Village pilot protocol

Status on 2026-10-03: the project owner supplied the schema, manifest, changelog, example, agent table, full chat table, a 146-row memory crop with selection report, a rendered transcript, and two additional recipient-memory crops containing 28 and nine rows. All three memory crops have been validated locally; case reports and source excerpts remain private. The full memory-table bytes have not been retrieved or independently verified in this workspace. The rendered transcript supplies event context but lacks raw table IDs and computer-use turns. This public protocol reports no new transmission finding. See [the input checklist](AI_VILLAGE_INPUTS.md) and [metadata validation](AI_VILLAGE_VALIDATION.md).

## Question

Can we trace a statement from one agent into another agent's written memory, then associate that retained statement with a later recorded action? RelayTrace will distinguish availability, acknowledgement, recorded retention, and action evidence. None of these alone establishes that the earlier statement caused the later behavior.

## Initial case and window

Start with the already reported Geological Clock episode, covering May 29 through June 2, 2026 in America/Los_Angeles. The initial UTC window is [2026-05-29T07:00:00Z, 2026-06-03T07:00:00Z). Include the most recent preceding memory and the next available memory after the window for each relevant recipient; mark missing coverage explicitly.

The public observer report describes a calendar interpretation spreading between agents and later being corrected. An agent-authored June 1 note provides a separate investigation lead. These sources guide record selection; they are not a novel RelayTrace finding or a substitute for raw evidence.

- [Observer report](https://aivillageblog.substack.com/p/persuasion-in-the-ai-village-deepseek)
- [Agent-authored calendar note](https://github.com/ai-village-agents/opus-47-notes/blob/main/saturdays.md)
- [Dataset and access conditions](https://huggingface.co/datasets/aidigestorg/ai-village)

## Acquisition and schema gate

Field mappings follow the supplied SCHEMA.md, and the manifest and CHANGELOG.md are available. Obtain chat, memories, and events next; add sessions and turns for selected candidates. Obtain only the files needed to extract the window. Avoid the bulk screenshot archive unless a specific disputed action requires it.

Require documented agent identities, row identifiers, timestamp semantics, session-to-agent and turn-to-session joins, memory ordering, and tool-output structure. Reject unresolved or conflicting joins instead of matching display names. Normalize authoritative timestamps to UTC, retaining original values. Village day numbers are supplemental labels, not substitutes for timestamps.

The adapter will read approved local files only. Each record will retain its table, source row identifier and location, dataset revision, original timestamp, file SHA-256, and canonical row SHA-256. Preserve provenance across transformations. Reject ambiguous timestamps and record schema/version incompatibilities.

## Evidence record

| Stage | Evidence needed | Permitted conclusion |
| --- | --- | --- |
| Available | A timestamped message in a room or artifact | Content existed at that location |
| Acknowledged | Recipient-authored reference with a source match | Recipient reported awareness or reuse |
| Retained | A new, attributable statement in a later memory, with the preceding memory compared | Content entered recorded memory |
| Action | A later turn's executed `agent_action`, with relevant tool output/error examined | A related action was recorded; success is assessed separately |
| Outcome | Independent artifact or output supporting the result | The described result has additional support |

A memory record does not establish that it was supplied to a subsequent model call. Memories have no direct session or consolidation foreign key, so temporal association with a session remains inferred. The public dataset excludes exact model-call logs. Narrated intentions, executed-action records, tool results, and independently corroborated outcomes must remain separate.

Classify each candidate as supported, contradicted, or unresolved at every stage. Store the supporting row identifiers and the reason. Treat correction and rejection as outcomes worth tracing alongside persistence.

## Review and alternative explanations

First identify the source messages and freeze up to 30 candidate relations before tuning matching rules. Review every candidate with its preceding memory, later memory, intervening chat, and relevant tool output. Record unavailable evidence rather than interpreting absence as rejection.

Check whether the statement already appeared in the recipient's earlier memory, came from a shared goal or scaffold, was independently discovered, or was merely repeated without a relevant action. The changelog lists an own-message turn-windowing fix on June 1 and a multiple-tool-result history fix on June 2, inside this pilot window. Annotate these as potential confounders; branch dates do not establish exact deployment times or effects on these records. The changelog is LLM-written from private git history, so it is contextual documentation rather than an independently inspected code diff. Generated daily summaries are navigation aids; they cannot independently validate raw-event claims. If AI assists review, disclose it and do not describe the review as blinded human annotation.

The pilot measures agreement with reviewed evidence labels and completeness of provenance. It does not estimate causal transmission rates or generalize from a selected, already known episode to the full Village.

## Deliverables and release boundary

After access: a schema-grounded local adapter, clearly synthetic validation fixtures, a reviewed case report, and a viewer that exposes source identifiers and evidence gaps. Keep gated raw records out of the public repository and release archive. Review redistribution conditions before publishing excerpts. Cite AI Digest and AI Village in resulting research, and prepare any required publication notification for Bruno's review.

The existing hackathon submission remains as submitted.

## Draft purpose for the dataset access request

We are developing RelayTrace for the AI Swarm Dynamics Hackathon. The project investigates whether content shared by one agent subsequently appears in another agent's recorded memory and is associated with later recorded actions. We plan a small, provenance-preserving pilot using chat, memory, session, and tool-event records, with explicit distinctions between observed evidence and causal inference. The data will be used for research and analysis, with no model training or fine-tuning and no attempt to re-identify redacted information. Project: https://github.com/brunuff/Hackthon-relay-trace.
