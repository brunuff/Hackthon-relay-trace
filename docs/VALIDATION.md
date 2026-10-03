# Release validation

Checked on October 3, 2026. The public-data MVP is published at
https://github.com/brunuff/Hackthon-relay-trace. Registration and the project
form have been submitted; the submitted narrative remains unchanged.

## Current release-safety and benchmark checkpoint

Tested code and immutable download: **`428a78c380e77bf94da470b0c0e93a3869f7780c`**,
the merged release-safety/benchmark implementation. [Tested ZIP](https://github.com/brunuff/Hackthon-relay-trace/archive/428a78c380e77bf94da470b0c0e93a3869f7780c.zip).
[Post-merge CI](https://github.com/brunuff/Hackthon-relay-trace/actions/runs/37157522226)
passed 78 tests on Python 3.12, both JavaScript syntax checks and a 44-file
release build. Local regression also passed on Python 3.9.6 and 3.11.
The judge polish changes documentation only; its draft PR checks identify its
own exact revision. Earlier counts of 23 or 62 tests below are historical,
not the current total.

### Fresh-download check for judge polish

The exact ZIP link above returned 826,748 bytes on October 3, 2026. ZIP SHA-256:
`40da8ca63e659b1aa8fec3c4873e8a65124701f6360486242270bb47264a8d09`.
Safe unpacking confirmed the offline `RelayTrace_demo.html`, ten public records,
six relations, and absence of raw inputs/generated artifacts. Demo SHA-256:
`5ec16f52d1db92d8a52c76d428b5db0d18ba9c709844c49dc53817c58f9ecb3b`.
Bundled evidence SHA-256:
`057eb2d85f0118a97d4817beefc462d1e7159251e9865ef7db0c61ac138d038a`.

A fresh real-browser walkthrough was attempted using the available browser
tool, which rejects `file://` URLs and forbids alternate routes around that
restriction. **No fresh browser pass is claimed for this polish run.** The
real-browser checks and screenshot below are historical evidence on the same
demo bytes. A judge can extract the ZIP, open `RelayTrace_demo.html`, select the
answer-relay episode and Observed evidence, then inspect Recorded acknowledgement
and its Source provenance. The current automated checks cover application logic
and the standalone script/data boundary; they do not replace a browser run.

### Measured comparison and adjacent limits

The frozen BENCHMARK_v1 protocol excludes all five current demo pages, leaving
4,574 eligible groups in the verified 14,591-revision, 4,579-page export. Its
lexicographic whole-group prefix selects 64 records across 32 pages and produces
130 union pairs on seven represented pages, overshooting the 30–50 aim. No
curated overrides or variant-specific tuning were used.

| Variant | Predicted pairs | Contradicted inherited-content attribution | Unresolved predicted | Precision | Union recall |
|---|---:|---:|---:|---:|---:|
| Full snapshots | 130 | 126 | 4 | 0 on adjudicated labels | undefined |
| Added/replaced lines | 4 | 0 | 4 | undefined | undefined |
| Introduced tokens | 4 | 0 | 4 | undefined | undefined |

All labels are AI-assisted, unblinded source review with automated per-pair base
checks, not blinded human ground truth. No supported positives were found.
120 negatives occur on `dse~--help`; the remaining six occur on one other page.
The four shared-reference candidates remain unresolved. Resolved review coverage
is 126/130 (96.92%), concentrated in two pages. Rejecting attribution of an
inherited artifact to a later writer does not prove no reading or reuse
elsewhere. This biased prefix demonstrates candidate pollution, not accuracy,
general superiority, balanced episode coverage, causal influence or corpus recall.

### Public reproducibility and provenance

The polish run reran the curated build into a separate file and reproduced the
frozen candidate union without expanding the study. Curated output matched the
bundled evidence apart from its truthful new retrieval timestamp; both candidate
JSON file and canonical report digests matched the recorded values exactly.

From the extracted tested revision:

```sh
PYTHONPATH=src python3 -m unittest discover -s tests -v
node --check web/app.js
node --check web/snapshot.js
python3 build_release.py
PYTHONPATH=src python3 -m swarm_tracer acquire
PYTHONPATH=src python3 -m swarm_tracer build --out artifacts/rebuilt-evidence.json
PYTHONPATH=src python3 -m swarm_tracer.benchmark \
  --raw-dir data/raw --out artifacts/benchmark-candidates.json
```

Use a fresh candidate output filename for reruns; the CLI refuses overwrites.
`build_release.py` uses the approved bundled snapshot. Do not overwrite
`data/processed/evidence.json` with a new acquisition: its truthful new retrieval
time changes the bytes, and release approval is tied to the existing digest.
The separate rebuilt file can be inspected locally or imported into the viewer.

Official source: https://collusion.wiki/explorer/download. Actual retrieval for
the benchmark was `2026-10-03T21:47:08.617290+00:00`. All four compressed hashes
match the earlier demo acquisition. Availability grants no general license;
raw archives and extra evidence rows are absent from the release.

| Public input | Compressed SHA-256 |
|---|---|
| `revisions.jsonl.gz` | `9c2a4ef0ccbfb5b42be8422342a6bd3a389a4a047bc891e3148354dd65b63c96` |
| `events.jsonl.gz` | `989780118de3dc05031ee5920a761c565a97b64d3721688593adc0794fcfb7b8` |
| `manifest.json.gz` | `ee4c5785d61054ef993a4a10708d9698d7d1f86ac210810b6899bae035eda092` |
| `pages.jsonl.gz` | `2cffa83e0cc8de3dc467d9e9b03e1f735f54b4fde5a191f9e01f7e9dfee51f3a` |

Frozen [BENCHMARK_v1 spec](specs/BENCHMARK_v1.md) SHA-256:
`20a1893f9518b60941bbeacaea9efcd847b9990ac9467cf196382778c14073f1`.
Canonical candidate-report digest (the `candidate_report_sha256` field):
`ae20f1cd674f59f81ad21d68d82def8153701588936edb137dc05f1ceb9bce5f`.
Candidate JSON file-byte SHA-256:
`430f63e18212ca7100d76f44b49d99af498480bc6d1e545a739642805647c10a`.
The separate local run manifest SHA-256 is
`6f9daa6301237f3f038b588009596ddad16adfe43ec764e7452389f51a70f37a`;
it records the actual acquisition and run and is not a public CLI output.

Public users with matching inputs can reproduce the normalized records,
curated analysis (with a new retrieval timestamp), candidate population and
frozen report digest. The private review packet and context excerpts are not
shipped. Thus public users cannot fully recreate the reported labels or metrics
from the repository alone; `evaluate_report` requires their own complete,
report-bound review. Do not treat the 78 software tests as research validation.

Release safety captures approved bytes without following symlinks and stages
complete outputs before replacing them. Individual replacements are atomic;
the set is not a transaction, so a crash during final replacements can leave
mixed generations. No raw AI Village data, private crops or private packet
enters the public Collusion-only demo. [SDD/TDD and detailed record](LOCAL_VALIDATION.md).

## Historical public-data MVP checkpoint

The following sections describe earlier checks. They retain their original
counts and environment details for provenance.

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

## Historical automated review — 23 tests

The initial public-data release passed all 23 Python tests, including 11 independently authored checks. Coverage
includes cumulative snapshots, replacement-line inheritance, handle boundaries,
duplicate IDs, uncertainty-overlapping clocks, malformed timestamps, fixed-origin
downloads and redirects, literal source content, adversarial JSON imports and
the standalone HTML script/data boundary.

The independent Node DOM harness runs the actual application JavaScript.
See `REVIEW.md` for its findings and remaining methodological limits.

## Historical real-browser integration

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

## Scope of the historical MVP pass

This is a functional and methodological prototype review, not a complete
accessibility audit, security certification or held-out precision/recall
benchmark. The curated cases do not establish propagation prevalence, causal
goal transmission or the cause of the July Hugging Face swarm's ending.

## Historical AI Village adapter checkpoint — 62 tests

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

The curated Collusion evidence snapshot retained the SHA-256 above. At that
checkpoint, the standalone demo SHA-256 was
`5ec16f52d1db92d8a52c76d428b5db0d18ba9c709844c49dc53817c58f9ecb3b`.
See `AI_VILLAGE_VALIDATION.md` for metadata fingerprints and the distinction
between actual metadata checks and synthetic behavioral-table tests.
