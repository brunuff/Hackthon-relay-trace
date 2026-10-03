# Local validation record — 2026-10-03

Current implemented checkpoint: 78 tests; merged at
`428a78c380e77bf94da470b0c0e93a3869f7780c`. The baseline, initial green runs
and unavailable-input status below are historical checkpoints. The follow-up
sections record recovered inputs, measured results, review fixes and publication.
See [current release validation](VALIDATION.md#current-release-safety-and-benchmark-checkpoint)
for the tested download and public reproducibility limits.

Baseline: `bce0b0ae560d9f48df1689e2d0fc86be45f9ae71`.
Specs frozen before tests and implementation: `RELEASE_SAFETY_v1` and
`BENCHMARK_v1` in `docs/specs/`. Local authorization covers SDD/TDD and release
rehearsal; all changes remain uncommitted for Bruno review. No push, PR, merge,
deployment, submission, paid model call or external message occurred.

## Environment and baseline

An empty Mac task workspace received an isolated clone of the exact baseline;
no existing checkout or working changes were modified. The clone contains no
AGENTS.md, `.agents`, `.codex`, or repository skills. Read WORKFLOW.md and
AI_VILLAGE_PILOT.md. Inspected the exposed local skill directory; no relevant
repository development skill was present. No Downloads access, AI Village
record access, copying, or dataset duplication occurred.

Runtime: system Python 3.9.6 on the connected Mac mini (README recommends 3.10+;
checks also pass on this older runtime). Baseline command:
`PYTHONPATH=src python3 -m unittest discover -s tests`: 62 tests, pass.

## Red evidence

The first new-suite run failed: missing benchmark module (one loader error)
and missing release allowlist (four errors). To verify behavioral failures,
loaded `git show HEAD:build_release.py` as the baseline module and ran the new
release acceptance tests against it, supplying only the expected path list
for fixture setup. Three assertions failed:

- Baseline ZIP contained `secret.json`, `docs/private-packet.json`, and
  `web/crop.json` planted with synthetic restricted markers.
- Baseline accepted the synthetic AI Village snapshot instead of rejecting it.
- Baseline accepted a symlinked approved source file instead of rejecting it.

No real private data was used as a fixture. Logs are stored in the parent
local workspace: `red-tests.log`, `red-behavior.log`, `baseline_build_release.py`.

## Green evidence

Commands:

```sh
PYTHONPATH=src python3 -m unittest discover -s tests -p test_release.py -v
PYTHONPATH=src python3 -m unittest discover -s tests -p test_benchmark.py -v
PYTHONPATH=src python3 -m unittest discover -s tests -v
python3 build_release.py
git diff --check
git check-ignore data/processed/restricted.json private/packet.json data/raw/ai-village/example.json
```

Release: six tests pass, including exact ZIP membership, unexpected synthetic
private-file exclusion, restricted/spoofed/empty snapshot rejection with all
existing output bytes unchanged, provenance rejection, missing/symlinked
approved-file refusal, script escaping and empty-data defense.
Benchmark: six synthetic tests pass, covering demo split leakage, deterministic
union, extraction variants, arithmetic, unresolved handling and invalid labels,
plus report-hash binding, duplicate/missing reviews and complete-union review.
Full regression: 72 tests pass. Diff whitespace check passes. Ignore checks
confirm non-demo processed JSON, private packets and raw AI Village paths are
ignored. Ignore rules can be bypassed by force-adding files; release inclusion
is independently controlled by the explicit allowlist.

Local rehearsal: 43 exact archive members. Approved snapshot SHA-256:
`057eb2d85f0118a97d4817beefc462d1e7159251e9865ef7db0c61ac138d038a`.
Demo SHA-256:
`5ec16f52d1db92d8a52c76d428b5db0d18ba9c709844c49dc53817c58f9ecb3b`.
The public evidence JSON, standalone demo and web snapshot remain byte-identical
to baseline. Archive/manifest live in ignored `artifacts/`; source archive is a
local rehearsal, not a published release. Hash of the final archive is in
`artifacts/release_manifest.json`; it changes when local source/docs change.
Logs in the parent workspace: `green-release.log`, `green-benchmark.log`,
`green-tests.log`, `release-rehearsal.json`.

## Research coverage and limits

A bounded search of the local Codex task directories (maximum depth five)
found no `revisions.jsonl.gz` and no other RelayTrace checkout. The delegated
source thread is cloud-backed, so its raw export is not available as a Mac
file. No unrelated personal contents or Downloads were searched.

Command attempted:
`PYTHONPATH=src python3 -m swarm_tracer.benchmark --raw-dir data/raw --out artifacts/benchmark-candidates.json`.
It refused to run because `data/raw/acquisition.json` is absent. No report or
labels were produced. Actual held-out research coverage: **0 reviewed pairs,
0 verified held-out groups; all three variants unmeasured**. Synthetic unit
test success is software validation only. No precision, recall, superiority or
causal finding is claimed. The 30–50-pair/five-group aim remains unassessed.

Bruno review decisions: approve the local source changes and exact allowlist;
provide the full eligible public Collusion export and acquisition provenance
(or separately authorize reacquisition), then review the frozen union with
explicit label origins. No publication is authorized. Any future snapshot or
allowlist expansion needs review; availability alone is not public eligibility.

## Follow-up: public inputs recovered and independent review addressed

The earlier input blocker is resolved. Under the delegated public-download
approval, ran `PYTHONPATH=src python3 -m swarm_tracer acquire --raw-dir data/raw`.
Official source: https://collusion.wiki/explorer/download. Acquisition recorded
`2026-10-03T21:47:08.617290+00:00`; all four compressed hashes match the
baseline. Decompressed file hashes also match the official page's checksums.
Only the four documented fixed files were retrieved (about 3.95 MB compressed);
no bulk ZIP, Downloads scan, AI Village data or extra source files were used.
The official page provides redacted public downloads without authentication or
a new terms-acceptance gate. No general dataset license is stated. Public
availability does not grant redistribution rights; the additional source rows
and review excerpts stay local in ignored directories.

Frozen BENCHMARK_v1 selection ran unchanged. One performance fix avoids
renormalizing the entire corpus for every whole-group prefix; it changes no
population, extraction, matching, ordering or stopping rule. Full source:
14,591 revisions across 4,579 pages. Five demo pages excluded; 4,574 eligible
pages remain. The first 32 eligible groups contain 64 records. The union has
130 candidate pairs across seven represented pages. The 30–50 aim is exceeded
by the whole-group stopping rule and is reported honestly, not resampled.
Candidate report hash: `ae20f1cd674f59f81ad21d68d82def8153701588936edb137dc05f1ceb9bce5f`.

AI-assisted, unblinded source review of the complete union:

| Variant | Predicted pairs | Contradicted new-attribution pairs | Unresolved predicted | Precision | Union recall |
|---|---:|---:|---:|---:|---:|
| Full snapshots | 130 | 126 | 4 | 0 | undefined |
| Added/replaced lines | 4 | 0 | 4 | undefined | undefined |
| Introduced tokens | 4 | 0 | 4 | undefined | undefined |

No supported positives were found. Of 130 reviewed pairs, 126 reject the
specific attribution of inherited full-body artifacts to a later writer:
120 are on `dse~--help`, and six on `dse~Agent013OpenSECMDJSPairsUnique`.
For every such pair, scripted checks confirm all shared full-body artifacts
already exist in the target's preceding raw diff-base body; source review
confirmed later edits add no shared artifact. This does not prove no reading
or reuse elsewhere. The other four pairs share public DataUSA/SEC reference
links with plausible shared-upstream explanations and remain unresolved.
All 130 origins are AI-assisted (with automated per-pair checks), zero human
adjudications. Resolved coverage is 126/130 (96.92%), concentrated in two pages.

These results show candidate pollution from inherited content in this prefix,
not a general performance validation. There are no positive examples to
estimate recall, and line/token precision has no resolved denominator. Seven
represented pages do not establish balanced episode coverage; the lexicographic
prefix is highly biased toward probe/link pages. No superiority, transmission,
causal, prevalence or corpus-recall claim follows. A broader, prospectively
specified positive-containing review and human adjudication remain decisions
for Bruno; do not tune this run to produce a favorable outcome.

Private local records in ignored `artifacts/`: `benchmark-candidates.json`,
`benchmark-review.json`, `benchmark-metrics.json`,
`benchmark-review-context.json`, and `benchmark-run.json`. The complete review
is bound to the frozen report hash; missing/duplicate/extra labels fail closed.

Independent review findings were reproduced red in
`red-review-release.log` (three assertion failures) and
`red-review-benchmark.log` (missing save API). An additional behavioral replay
of the old benchmark `exists`/`write_text` implementation fails the dangling
symlink acceptance test (`red-review-benchmark-behavior.log`). Fixes:

- Capture approved files once through descriptor-relative, no-symlink regular
  opens; validate and archive those exact bytes. A swap to synthetic restricted
  evidence and a private-file symlink after preflight cannot enter the archive.
- Render/ZIP/manifest generation and all temporary-file staging finish before
  existing outputs are replaced. Injected render, ZIP and staged-write failures
  preserve prior viewer/demo/archive/manifest bytes and clean temporary files.
- Benchmark report creation validates every parent component and uses exclusive
  no-symlink creation. Existing files, dangling links, symlinked parents and a
  concurrent creator are rejected without overwriting the winning report.

Atomicity limit: replacements are individually atomic, not a multi-file
transaction. A crash or replacement failure in the final sequence can leave
mixed generations. Directory descriptors prevent a parent symlink swap from
redirecting writes; this is not a defense against a hostile process with full
write access to the same repository. Original source content approval and
policy updates still require review.

Final regression: **78 tests pass on Python 3.9.6 and Python 3.11**.
Focused release: ten tests pass; focused benchmark: eight tests pass.
`git diff --check` passes. Rehearsal now has **44 exact members** (the added
safe I/O module); standalone demo, viewer snapshot and public evidence remain
byte-identical to baseline. No push, PR, merge, deployment, submission, new
terms acceptance, paid calls or external messages occurred. A small private
review bundle includes the patch, specs, this record, test logs and aggregate
metrics/provenance, excluding dataset rows and source archives.

## User-supplied ZIP corroboration

User supplied `full-wiki-logs.zip`. Materialized locally and recorded as
**USER-SUPPLIED**, with local verification-completion time
`2026-10-03T21:57:59.237075+00:00`; this is not asserted to be the original
retrieval time or upload time. ZIP size 4,228,605 bytes; SHA-256:
`eb68aa12d26bf189d8bfc4ce47f4d8af66ae5ba7ebbadd429738297a3cbb25ae`.

Inspected six exact members without extracting or executing them. Checks
refuse absolute/traversal/backslash paths, symlinks, encryption, duplicate
members, excessive member/total expansion and compression ratios; CRC and all
five supplied SHA256SUMS pass. Maximum allowed expansion was 128 MiB total,
64 MiB per member and 1000:1 ratio; actual total about 54.6 MB. Four data files
match the independently downloaded official bytes exactly; `labels.jsonl`
also matches the official page's expanded-file checksum. Revisions count is
14,591. This corroborates the public export, but does not establish original
source acquisition provenance from the ZIP alone. No expanded dataset copies
were persisted, and no extra labels data entered the frozen benchmark.
Detailed byte hashes and member safety results remain local in
`artifacts/user-supplied-source-validation.json`.

The review patch was also checked with `git apply --check` against a temporary
archive of the exact baseline tree and applies cleanly. The private Library
review bundle contains source changes, specs, validation and supporting logs/
aggregate provenance only, with no raw records, review excerpts or input ZIP.


## Publication authorization — 2026-10-03

After independent re-review, Bruno explicitly approved committing the reviewed
changes, pushing a new branch and opening a draft PR at 22:04 UTC. This
supersedes the earlier local-only restriction; earlier passages record the
pre-publication checkpoints. Publication scope includes reviewed code, specs,
test maps and safe aggregate results/provenance. Raw public inputs, AI Village
records, crops, private packets, local review excerpts and generated archives
remain excluded. No merge, auto-merge, deployment or submission is authorized.
