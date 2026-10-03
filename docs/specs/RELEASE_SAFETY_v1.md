# Release safety spec v1

Frozen 2026-10-03 before tests/implementation. Baseline: bce0b0ae560d9f48df1689e2d0fc86be45f9ae71 (62 tests pass).

Only explicitly listed reviewed source files and the approved Collusion demo snapshot may enter a release. An exact snapshot-byte digest anchors approval; claimed public metadata alone cannot grant eligibility. Validate that digest, Collusion dataset identity, public acquisition mode, source-file URLs/hashes, and event provenance before any output mutation. Changing public evidence requires separate review and an explicit approval-manifest update. Restricted AI Village inputs, crops, audit outputs and private packets never qualify. File symlinks or missing approved files fail closed. Arbitrary files in arbitrary directories cannot expand the allowlist. Ignore non-demo processed outputs in Git as a second guard, not a rights determination.

Acceptance → tests (`tests/test_release.py`):

| Acceptance | Test |
|---|---|
| Synthetic restricted files in unexpected directories excluded; exact archive members | `test_exact_allowlist_excludes_surprise_files` |
| Restricted/spoofed/modified snapshots rejected before writes | `test_rejected_snapshot_preserves_outputs` |
| Provenance validation independent of byte approval | `test_provenance_validation` |
| Missing or symlinked approved inputs rejected before writes | `test_invalid_allowlist_input_preserves_outputs` |
| Script escaping and empty-data refusal preserved | existing escaping/empty tests |

Release rehearsal is local only. No public rights claim follows from availability. Evidence receipt/causal flags remain unchanged.

## Review amendment v1.1 — 2026-10-03

Independent review identified input-reopen races and partial output writes.
Additional acceptance tests were recorded red before the fixes:
`test_swapped_inputs_are_never_reopened`,
`test_render_failure_preserves_prior_outputs`, and
`test_archive_failure_preserves_prior_outputs`. Capture approved bytes using
regular-file opens that refuse every symlink component; validate and use only
those bytes. Render the demo, build the ZIP and serialize the manifest before
staging every output, then replace each file. Also check staged-write failure
with `test_staging_failure_preserves_prior_outputs`.

Each replacement is atomic; the set of replacements is not a filesystem
transaction. A failure during final replacements can leave mixed generations;
rendering, ZIP construction and staging failures preserve existing outputs.
Pinned parent-directory descriptors prevent symlink swaps redirecting writes.
