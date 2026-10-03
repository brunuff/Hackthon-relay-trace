# Extraction benchmark protocol v1

Frozen 2026-10-03 before tests/implementation or measurement. Baseline: bce0b0ae560d9f48df1689e2d0fc86be45f9ae71.

Compare full cumulative bodies, added/replaced lines, and introduced-token extraction using the same `generate_edges` rules/artifact definitions, 86400-second window, normalized record population and timestamp uncertainty. Do not apply curated episode relations. Freeze input hashes and protocol in the candidate report. Exclude every page containing a current demo episode revision and reject a demo revision assigned to a different held-out page. Retain full corpus bases for normalization before applying the held-out population.

Rank eligible held-out page groups lexicographically. Include whole groups until their union of candidates reaches 30 (target 30–50 pairs, at least five groups); report actual coverage without forcing a quota. A pair belongs to its unordered endpoint IDs, including cross-page matches. Keep frequency filtering fixed across variants by using artifact frequencies from full bodies for the same population. Review the union, not just one method's candidates. All proposed pairs start unresolved. Label supported/contradicted/unresolved with rationale, reviewer and origin (`automated`, `AI-assisted`, `human`). No automated label is human adjudication. Freeze the candidate report hash before review; changed inputs require a new report.

Metrics: TP=supported predicted, FP=contradicted predicted, FN=supported unpredicted among adjudicated union. Precision=TP/(TP+FP), recall=TP/(TP+FN); zero denominator is null. Unresolved pairs never become negatives; report unresolved predicted and adjudicated coverage. Union recall is not corpus recall. Do not report causal transfer, tuning success or superiority without actual evidence.

Acceptance → `tests/test_benchmark.py`:

| Acceptance | Test |
|---|---|
| Demo page/revision leakage refused | `test_split_leakage` |
| Identical input permutation gives identical report; no curated overrides | `test_deterministic_union` |
| Three extraction variants preserve fixed population | `test_variants` |
| Known arithmetic and unresolved exclusion/null denominators | `test_metrics` |
| Invalid/duplicate/extra/misrepresented labels rejected | `test_invalid_labels` |

Eligible full public source revisions plus verified acquisition hashes are required for measurement. The ten-event curated demo cannot supply held-out validation. Synthetic tests establish software behavior only. No paid model calls, fabricated labels or AI Village data.
