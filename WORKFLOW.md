# RelayTrace working contract

Goal: ship a reproducible, evidence-linked tracer for information reuse between AI agents for the October 3–4, 2026 AI Swarm Dynamics Hackathon.

The initial release uses the public, redacted Collusion.wiki export. It does not depend on gated AI Village access, does not execute agent-authored content, and does not claim to resolve the Hugging Face swarm's ending.

## Work ownership

| Workstream | Owner | Files |
|---|---|---|
| Acquisition, normalization, extraction | evidence_pipeline | `src/`, `data/`, `tests/test_pipeline.py` |
| Offline evidence explorer | viewer | `web/` |
| Rules, sources, registration research | requirements_research | `docs/RESEARCH.md` |
| Independent methods and safety review | reviewer | `docs/REVIEW.md`, `tests/test_review.py` |
| Integration, packaging, final validation | root | root files, `artifacts/`, integration tests, submission draft |

## Evidence contract

- A post establishes a recorded write.
- An explicit acknowledgement establishes recorded acknowledgement of content or a named contributor.
- Matching artifacts with temporal order suggest a relation, unless a shared upstream source or copied revision could explain the match.
- A handle is not a verified agent identity.
- A statement that something worked is a claim until action/output records corroborate it.
- Missing response or action data means unknown, not failed.
- Observational relation is not a counterfactual causal estimate.

Every inferred edge must preserve its source records, rationale, timestamp uncertainty and provenance. Negative tests must cover snapshot copying, generic shared content, self references and missing timestamps. Synthetic test fixtures stay visibly separate from the real demo.

## Release gates

1. Acquisition provenance recorded and raw inputs hashed.
2. Curated real-data cases reviewed against the original records.
3. Reproducible CLI and standalone HTML demo work offline.
4. Meaningful unit and browser checks pass.
5. Claims, limitations, source attribution and separate data terms documented.
6. Source archive and completed submission draft saved.
7. Resolve public GitHub destination and registration/submission identity before external publication or form submission.

## Extension after initial release

If manually approved AI Village access becomes available, connect messages to memory consolidation and computer actions. Distinguish a chat message that was available from a message demonstrably present in a recipient's context. Exact model-call prompts are excluded from the ordinary dataset.
