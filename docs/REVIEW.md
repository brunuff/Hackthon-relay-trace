# Independent evidence and safety review

This review evaluates whether the prototype supports inspectable textual relationships without upgrading them into claims about agent identity, successful exposure, goal adoption, or causation.

## Required evidence distinctions

| Claim | Minimum evidence | What it does not prove |
|---|---|---|
| Text or link appears in a later record | Exact recoverable text/link and the containing revision | That the later author read the earlier record |
| Explicit attribution or acknowledgement | Recoverable excerpt naming the source, plus a source candidate | Genuine identity, a verified read receipt, truthful self-report |
| Candidate reuse | Distinct records sharing sufficiently distinctive content | Direction, causation, successful transfer, common-source exclusion |
| Ordered candidate reuse | Candidate reuse plus usable timestamps | True event order within uncertainty, stable identity |
| New page content | Delta from the previous snapshot for the same page | That the revision label authored every sentence in the snapshot |
| Behavior or adoption | An independently recorded action/outcome linked to the receiving system | Must not be claimed from text similarity alone |

“Observed” must modify the observable textual feature, rather than the inferred interpersonal relationship. An unknown or low-quality timestamp must not silently become a date, a zero interval, or proof of chronological transmission. Handles are labels, not persistent identities. A same-handle pair is not proof of a single continuing agent, and a different-handle pair is not proof of different agents.

## False positive checks

1. Common words, greetings, generic completion markers, and benchmark boilerplate must not create reuse links alone.
2. Repeated or cumulative snapshots must not count inherited text as a new contribution by the current revision label.
3. Duplicate revisions, self-replies, and same-page continuations must not inflate the number of recipients or independent transmissions.
4. Similarity must remain a candidate relation, with a visible match excerpt and a documented threshold.
5. Unsupported chronology must remain unknown. Source revision time and a timestamp written in message text are distinct evidence.
6. Any scalar used to rank examples must be named as a heuristic, not a calibrated probability.
7. No visual metric may count aliases as verified people, agents, read receipts, adoptions, or successful goal transfers.

## Untrusted data checks

All recovered content, aliases, excerpts, page names, and URL values are untrusted. The viewer must render them as text; it must never evaluate embedded code, interpret recovered HTML, auto-load remote resources, or follow payload URLs automatically. Navigable links must be limited to HTTP(S) and preferably to explicitly approved source pages. New-tab links require `noopener`/`noreferrer` protection. Data parsing must use JSON parsing rather than evaluation, reject malformed structure with an actionable error, and avoid deserializers with execution semantics.

## Review result

**Pass for the stated public-text evidence scope, subject to the limitations below.** Review performed on 2026-10-03. The final inspected snapshot contains 10 evidence records, 6 relations and 3 purposively selected episodes. Its relations comprise 3 observed textual attributions, 2 inferred connections and 1 undirected unknown connection. Every relation explicitly sets `receipt_observed=false` and `causal_uptake_observed=false`.

The review found and verified corrections for four material issues:

1. A minor edit to an existing line originally made its unchanged URL and attribution look newly authored. Matching now uses genuinely introduced lexical fragments, while retaining changed-line context for inspection. The regression excludes the inherited artifact.
2. A handle prefix such as `AgentA` could originally match a reference to `AgentAB`. Whole-handle boundary checks now prevent the false observed attribution.
3. Undirected relations originally displayed directional arrows and earlier/later labels. The viewer now uses an undirected connection, Record A/B and “Order unresolved.”
4. Numeric or timezone-less imported timestamps could originally be interpreted as dates and labelled UTC. Such values now remain unknown; invalid array members are also rejected.

The same-page grocery cache acknowledgement is supported by newly added text containing the earlier handle and the value 34,770. The technique reproduction examples have inspectable text claiming success, but those claims remain unverified. One associates the shorthand “Dec30” with a source handle by an explicitly labelled curated contextual interpretation. The independent-sequence example remains undirected and unknown. No example establishes successful delivery, authentic agent identity, goal adoption or an independently observed outcome.

## Executed checks

Command: `PYTHONPATH=src python -m unittest discover -s tests -v`

At review completion, all 23 project tests passed, including 11 independent checks in `tests/test_review.py`. Independent coverage includes unchanged snapshots, inherited URLs in cumulative revisions, minor replacement-line edits, generic completion language, handle-prefix confusion, conflicting duplicate IDs, unknown/malformed timestamps, explicit receipt/causation disclaimers, literal embedded Python/HTML, and viewer imports.

The viewer test executes the actual `web/app.js` against a deliberately narrow Node DOM harness. HTML and script payloads placed in record text, handles, page names, dataset titles, rationale and evidence excerpts remained literal. The test detected no dynamically created image/script/frame elements or unsafe hyperlinks. Non-HTTP source links were excluded, embedded URLs were not fetched, malformed JSON produced a visible error, and invalid event members were rejected. The release tests also check that a closing-script payload cannot escape the embedded snapshot.

## Remaining limits

- A real Chromium browser could not initially launch because this environment lacked its executable. The DOM harness verifies import and rendering control flow, but it does not substitute for browser layout, accessibility or a complete browser security review. The integration owner should record any separate browser checks.
- The selected examples are not a random sample and do not establish prevalence, precision or recall. There is no held-out adjudicated evaluation set.
- The conservative matcher may miss genuine reuse that is paraphrased, occurs outside the selected window, repeats already present material, or uses the same handle. Same-handle suppression is a scope choice, not proof that no inter-agent reuse occurred.
- Publisher timestamps and their stated uncertainty are retained. Time between public posts is not time to read, decide, act or transmit.
- Private prompts, memories, execution traces and task outcomes are unavailable in this corpus. The July Hugging Face swarm's ending and later unrelated-agent adoption remain unresolved.
