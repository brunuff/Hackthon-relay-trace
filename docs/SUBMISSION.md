# RelayTrace submission draft

Status: the implementation and public-data validation are complete. The project
is published at https://github.com/brunuff/Hackthon-relay-trace. This document
remains a submission draft; registration and hackathon submission have not occurred.

## Project title

RelayTrace: evidence of information reuse between AI agents

## Short description

RelayTrace is an offline evidence explorer that links public agent-written
contributions to later references, acknowledgements and claims of reuse.
Every relation has inspectable source records, timestamps, provenance and an
explicit evidence status. The tool separates observed textual relations from
inferred connections and unresolved cases, making it useful for investigating
how information moves between agents without overstating what public logs
can establish.

## What we built

A dependency-free Python pipeline acquires the redacted Collusion.wiki export,
checks integrity, extracts newly introduced material from saved page revisions,
and generates candidate information-reuse relations. A local browser viewer
supports search, filters, source inspection and import of the generated JSON.
A release script embeds the reviewed snapshot into a single HTML file that
works offline.

The demonstration contains 10 real evidence records and 6 relations across
three curated episodes involving shared answers,
claims of reproducing a technique, and ambiguity between independently
similar task sequences. Its contribution is a reproducible tool and an
auditable evidence model. Agent self-reports remain self-reports; it does not
claim independently verified task success or causal goal adoption.

## Why this matters

Public material can outlive the agents that produced it. To assess whether it
influences later agents, researchers need to distinguish a surviving artifact
from a recorded acknowledgement, retained memory, actual downstream action
and further relay. RelayTrace provides the first part of that investigation
and a schema that can later connect richer transcript and memory datasets.

## Two-minute demo walkthrough

1. Open the standalone HTML file and explain the dataset and its coverage.
2. Select the grocery answer-relay episode and inspect the original contribution
   and a later explicit cache acknowledgement.
3. Show the relation's evidence status, source links and timing provenance.
4. Open the technique-reproduction case and distinguish a claimed action from
   an independently verified result.
5. Open the ambiguity case and explain why overlap or shared upstream sources
   cannot establish an ordered transfer.
6. Show local JSON import, the reproducible CLI and the false-positive regression
   tests for copied snapshots and minor page edits.

## Limitations

Public wiki data does not expose exact model contexts, private memory, verified
read receipts or grader outcomes. Handles do not establish agent identity.
Snapshot copying can resemble reuse unless contributions are separated.
The selected episodes are not a representative sample, and missing evidence
is not evidence of non-transmission. AI Village memory analysis is an optional
extension requiring its publisher's manual access approval.

## Materials to enter in the form

- Repository URL: https://github.com/brunuff/Hackthon-relay-trace
- Explanation: use the short description and project detail above.
- Demonstration: standalone `RelayTrace_demo.html` in the repository/release.
- Participant public name: **Bruno; confirm full name for the form**.
- Participant email: **required from Bruno**.
- Additional human team members: **none identified; confirm if applicable**.
- Implementation disclosure: AI-assisted work using four independent
  workstreams for data, interface, requirements and review.

## Official links and deadline

- Register: https://airtable.com/appFBFzD2Cv2rYCG5/pagij1OYTgOK4K0DC/form
- Submit: https://airtable.com/appFBFzD2Cv2rYCG5/shr8KXOLvo3xV9bnZ
- Logistics: https://swarmchasing.com/logistics/
- Deadline: Sunday, October 4, 2026, **8 p.m. America/Toronto**.

The official logistics requires a GitHub repository and participants' names
and emails. The draft is reviewable before any external form submission.
Field names above describe required inputs, not a verified Airtable
form schema.
