# Release validation

Checked on October 3, 2026. The public-data MVP is published at
https://github.com/brunuff/Hackthon-relay-trace. Registration and the project
form have been submitted; the submitted narrative remains unchanged.

## Real evidence snapshot

- 14,591 publisher revisions normalized from the public redacted export.
- 10 selected evidence records, 8 handle labels, 5 source pages.
- 3 episodes and 6 inspectable relations: 3 observed textual attributions,
  2 inferred associations and 1 unknown association.
- No independently verified read receipts, causal uptake or task outcomes.
- Kentucky cache acknowledgement: 89 seconds between publisher timestamps,
  with a summed publisher uncertainty of ±2 seconds.

The curated snapshot was regenerated through the CLI from the acquired inputs.
Its bytes matched the initial snapshot exactly. SHA-256:
`057eb2d85f0118a97d4817beefc462d1e7159251e9865ef7db0c61ac138d038a`.

## Automated review

The initial public-data release passed all 23 Python tests, including 11 independently authored checks. Coverage
includes cumulative snapshots, replacement-line inheritance, handle boundaries,
duplicate IDs, uncertainty-overlapping clocks, malformed timestamps, fixed-origin
downloads and redirects, literal source content, adversarial JSON imports and
the standalone HTML script/data boundary.

The independent Node DOM harness runs the actual application JavaScript.
See `REVIEW.md` for its findings and remaining methodological limits.

## Real-browser integration

Eight real-browser checks passed using Chrome Headless Shell 154.0.8037.92 and
Playwright. The environment initially lacked a browser, and the default
Playwright browser download failed. A browser obtained from Google's official
Chrome for Testing distribution resolved that dependency.

The checks verified:

1. Offline initialization of the real snapshot.
2. Episode/status filtering and the 89 ±2 second evidence display.
3. Undirected presentation of unresolved associations.
4. Record browsing and exact phrase search.
5. Responsive layout at a 390px mobile viewport, with no horizontal overflow.
6. Literal rendering of imported HTML/script payloads, exclusion of unsafe
   script links, and no guessed date for an invalid timestamp.
7. Malformed JSON produces an error while retaining the prior valid dataset.
8. No page errors and no HTTP requests during the offline test sequence.

Desktop and mobile screenshots were inspected for legibility and layout. The
screenshots in `images/` show the reviewed demo, not synthetic findings.

To rerun optional real-browser checks with Playwright installed:

```sh
python3 build_release.py
node tests/browser_smoke.cjs artifacts/RelayTrace_demo.html
```

The runtime-specific `RELAYTRACE_PLAYWRIGHT_MODULE` and
`RELAYTRACE_BROWSER_PATH` environment variables can select an existing module
and browser. Core Python/Node harness tests require no Playwright installation.

## Scope of this pass

This is a functional and methodological prototype review, not a complete
accessibility audit, security certification or held-out precision/recall
benchmark. The curated cases do not establish propagation prevalence, causal
goal transmission or the cause of the July Hugging Face swarm's ending.

## AI Village adapter checkpoint

The schema-grounded local importer adds 21 synthetic tests; the memory-crop
helper adds seven boundary/transfer checks, and the literal citation audit adds
11 source-span checks. All 62 repository
tests pass. A CLI import of the actual supplied manifest and agent table
loads 46 agent metadata entries and emits zero behavioral records or relations.
The real chat table, an initial 146-row memory crop and two additional crops
containing 28 and nine rows are validated privately. All 183 crop rows import
with UUID attribution and zero automatically inferred relations. The full
memory file is not available in this workspace; producer-reported full-file
fingerprints and global boundary completeness remain unverified here. Actual
session and turn rows remain pending.

The regenerated demo passes nine real-browser checks with no page errors or
HTTP requests. The added check verifies that a source documentation URL does
not label restricted research data public. The source archive contains no
raw AI Village input, supplied schema/changelog/example, or local AI Village
processed output, and has no duplicate entries.

The curated Collusion evidence snapshot retains the SHA-256 above. The current
standalone demo SHA-256 is
`5ec16f52d1db92d8a52c76d428b5db0d18ba9c709844c49dc53817c58f9ecb3b`.
See `AI_VILLAGE_VALIDATION.md` for metadata fingerprints and the distinction
between actual metadata checks and synthetic behavioral-table tests.
