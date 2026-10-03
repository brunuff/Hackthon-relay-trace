# Release validation

Checked on October 3, 2026. The public-data MVP is published at
https://github.com/brunuff/Hackthon-relay-trace. External registration and form
submission remain separate steps requiring participant details.

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

All 23 Python tests pass, including 11 independently authored checks. Coverage
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
