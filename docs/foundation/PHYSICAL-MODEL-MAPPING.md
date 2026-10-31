# Logical-to-physical model mapping

All 23 logical entities and all declared fields are accounted for using the live migrated fixture catalog. Every implemented entity remains partial; name correspondence is not behavioral completion.

| Logical entity | Physical table | Fields mapped / total | Remaining fields |
|---|---|---|---|
| TENANT | tenant | 2 / 2 |  |
| USER | actor | 2 / 2 |  |
| MEMBERSHIP | membership | 3 / 3 |  |
| PROJECT | project | 6 / 6 |  |
| ANALYSIS_RUN | analysis | 15 / 15 |  |
| GRAPH_NODE | graph_node | 8 / 8 |  |
| GRAPH_EDGE | graph_edge | 8 / 8 |  |
| PLAN | plan | 21 / 21 |  |
| APPROVAL | approval | 9 / 9 |  |
| GENERATION_RUN | run | 11 / 11 |  |
| ARTIFACT | artifact | 8 / 8 |  |
| VALIDATION_RUN | validation | 10 / 10 |  |
| VALIDATION_CHECK | validation_check | 14 / 14 |  |
| AUDIT_EVENT | audit_event | 6 / 6 |  |
| SOURCE_SNAPSHOT | source_snapshot | 7 / 7 |  |
| CANDIDATE | candidate | 17 / 17 |  |
| RECOMMENDATION | recommendation | 12 / 12 |  |
| POLICY | validation_policy | 7 / 7 |  |
| INFERENCE_CONSENT | consent | 11 / 11 |  |
| IDEMPOTENCY_RECORD | idempotency | 10 / 10 |  |
| OUTBOX_EVENT | outbox | 8 / 8 |  |
| FINDING | finding | 8 / 8 |  |
| PLAN_REVOCATION | plan_revocation | 6 / 6 |  |

## Representation and integration differences

- ARTIFACT: Immutable relative portable-path metadata and exact manifest binding exist; actual object bytes, host path resolution/symlink protection and secret-safe publication remain integration work.
- FINDING: Immutable same-generation stable identities and validation-check links exist; worker evidence ingestion/redaction and complete report integration remain incomplete.
- PLAN_REVOCATION: Immutable actor/reason record blocks supported admission/replay/publication/export; HTTP idempotency, cancellation and full lifecycle integration remain incomplete.
- SOURCE_SNAPSHOT: Immutable database identity and scope exist; actual source acquisition/storage byte verification and retention controls remain unimplemented.
- GRAPH_NODE: Scope and nonempty JSON evidence are enforced; analyzer/evidence-content validation and snapshot output sealing remain incomplete.
- GRAPH_EDGE: Same-analysis/tenant endpoints are enforced; analyzer lifecycle output sealing remains incomplete.
- RECOMMENDATION: Immutable scope/version/candidate ownership exists; actual deterministic recommendation computation and full content schema validation remain incomplete.
- PLAN: Full canonical payload and read-only projection validate against original CanonicalPlan/Plan schemas; trusted publisher must enforce JCS/installed plugin schema and secret-reference policy before product exposure.
- POLICY: Each immutable version resource now has a tenant-unique UUID; policy_key groups lineage and exact labels/revisions are unique within it. Canonical references retain the version-row UUID and opaque label. Legacy identity conflicts block migration; actual policy execution remains integration work.
- AUDIT_EVENT: UUID external identity and generated resource ID exist; runtime actor comes from authenticated principal. Administrative/bootstrap actor remains explicitly nullable; complete audit lifecycle/redaction still pending.
- MEMBERSHIP: Explicit operator role plus active state enforces the approved initial single-operator capability; no enterprise role-management UI or broader permission model is added.
- VALIDATION_CHECK: Stable UUID plus private contract projection derives mandatory/finding IDs; actual worker evidence ingestion and complete policy execution still require integration.
- CANDIDATE: All declared security/evidence metadata exists and selected executable fields bind exactly; schema-valid fixture and basic admission prerequisites are tested, not source truth or installed plugin compatibility.
- INFERENCE_CONSENT: Payload classes are text[], not JSON; transaction admission scope exists, actual egress recheck not integrated.
- OUTBOX_EVENT: Durable immutable payload/timestamps and monotonic attempt metadata exist; dispatcher leases, crash recovery and deduplicated external effects remain unimplemented.
- APPROVAL: Exact current plan hash/version and affirmative security confirmation are required; scoped stored Approval validates against OpenAPI. Browser/session and POST idempotency integration remain open.
- IDEMPOTENCY_RECORD: UUID/timestamp and immutable original admission response are persisted for generate; other POST operations and HTTP response/status mapping remain integration work.
- ANALYSIS_RUN: Analyzer version references are a pinned nonempty array; actual source/analyzer lifecycle and snapshot output sealing remain integration work.
- GENERATION_RUN: Generator and plan hash derive from immutable canonical binding; actual generation, verified object publication and recovery still require application integration.
- TENANT: Workspace display name is required; local workspace only, no tenant-management product surface.
- USER: Unique immutable local subject exists; real bootstrap/session credential provisioning remains unimplemented.
- PROJECT: Source/name/timestamps exist and Source/ProjectInput fixture documents validate. Source identity is immutable; actual local/Git acquisition, credential resolution and full workflow/latest-run API projections remain pending.

## Gate and reproduction

`docs/quality/physical-model-mapping.json` contains each source field, target column/type or missing designation and source hashes. `physical-schema-catalog.json` was captured from the disposable database after the migration chain recorded in that catalog. Run `python tools/map-physical-schema.py` to reproduce the mapping; rerun `tools/fixtures/m03/policy-identity-runner.py` to refresh its database catalog first.

No source data dictionary or API contract was changed to fit the partial implementation. H01 remains open. Next physical-model work should complete remaining schema/API semantics, then complete lifecycle, credential-reference and worker/publication integration. Runtime identity/assignment and bound artifact/export tables are supporting physical structures, not extra product screens.
