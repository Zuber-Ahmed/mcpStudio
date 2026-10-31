# Technical documentation intake — 28 October 2026

## Current availability and authority

All requested document categories are now present in the user-supplied folder: original PRD PDF; architecture/HLD; LLD; database narrative and Mermaid ERD; OpenAPI and guide. The final five-screen Stitch export is already archived here. Copies of the new package are preserved under `sources/technical-documentation/`. The editable Markdown, Mermaid and OpenAPI files were inspected directly; the companion compiled PDF was not used as a separate source of claims.

The new package README, provenance register and API info consistently say **NEW DRAFT**, review edition 0.1, not recovered original/accepted specifications. Receipt does not imply approval. This distinction comes from the documents themselves. The old PRD remains a proposed CLI-first baseline. Local-first and application-agnostic constraints remain binding; exact stack and initial supported analyzers require reconciliation.

This report supersedes earlier missing-file statements for A1/D1/O1. G01 is now **partially resolved: documents available; authority, completeness and conflicts pending**. F1 remains a documentation-only working folder; no runtime foundation was found in the filename scan. Original historical Git inspection was denied; not retried here. No project files were modified and no dependencies installed.

## Concrete draft contract inventory

OpenAPI 3.0.3, version `0.1.0-draft`: 15 operations, 23 schemas. Proposed base `http://localhost:8080/v1`; not a running service. Paths below exclude that proposed `/v1` base. Mermaid defines 14 logical entities and 18 relationships, not executable constraints or migrations.

### Requirement → architecture → operation → entity → screen → test

The following updates the original matrix's TBD linkage cells against the **new draft**, not an implemented backend. Original R01–R18 and T01–T18 remain stable. Original PRD FR crosswalk is in prd-intake.md. All test entries remain planned; N/A denotes an infrastructure/process requirement with no dedicated resource operation.

| Requirement | HLD/LLD responsibility | Exact draft operationId / method + path | ERD entities | Screens | Tests / remaining gap |
|---|---|---|---|---|---|
| R01 | Local topology/API/workers/storage | N/A dedicated endpoint; all operations local-capable by proposal | All persistent entities | S1–S5 | T01; Compose, images/versions/Windows sandbox still absent |
| R02 | Versioned analyzer/generator plugins | startAnalysis POST /analyses; getGraph GET /analyses/{analysis_id}/graph; createPlan POST /plans | ANALYSIS_RUN, GRAPH_NODE, GRAPH_EDGE, PLAN | S2–S5 | T02; plugin support/capability schema absent |
| R03 | Web UI shell | N/A dedicated visual endpoint | N/A | S1–S5 | T03; canonical Stitch tokens/screens unresolved |
| R04 | Dashboard/project API | listProjects GET /projects; getProject GET /projects/{project_id} | PROJECT | S1 | T04; no project status, last activity or latest-run links; no search/status filter query |
| R05 | Acquirer/project API | createProject POST /projects | PROJECT; source JSON | S2 | T05; Source requires revision for local too; secret provisioning missing |
| R06 | Analyzer/optional inference | startAnalysis POST /analyses; getAnalysis GET /analyses/{analysis_id} | ANALYSIS_RUN, GRAPH_NODE | S2,S3 | T06; request only project_id, no processing scope/consent configuration |
| R07 | Orchestrator/run API | startAnalysis POST /analyses; getAnalysis GET /analyses/{analysis_id}; getGeneration GET /generations/{generation_id}; getValidation GET /validations/{validation_id} | ANALYSIS_RUN, GENERATION_RUN, VALIDATION_RUN | S1–S3 | T07; polling statuses available; progress/retry/cancellation API absent |
| R08 | Graph/inspector | getGraph GET /analyses/{analysis_id}/graph | GRAPH_NODE, GRAPH_EDGE | S3 | T08; slicing, matrix semantics and node-specific retrieval absent; UI graph still unverified |
| R09 | Evidence model/policy | getGraph GET /analyses/{analysis_id}/graph; getPlan GET /plans/{plan_id} | GRAPH_NODE.evidence; PLAN | S3,S4 | T09; Evidence has location/detector but no provenance/confidence/risk schema; empty evidence allowed |
| R10 | Planner/policy | createPlan POST /plans; getPlan GET /plans/{plan_id} | PLAN, GRAPH_NODE (capability IDs) | S4 | T10; client/both/none policy pending; no recommended-vs-selected type, structured candidates, override reason |
| R11 | Go approval/generation transaction | approvePlan POST /plans/{plan_id}/approvals; startGeneration POST /generations | PLAN, APPROVAL, GENERATION_RUN, AUDIT_EVENT | S4,S5 | T11; version/hash bound; canonical hashing, revocation and expanded invalidation pending |
| R12 | Config validator/plugin | createPlan POST /plans; getPlan GET /plans/{plan_id} | PLAN.configuration | S4,S5 | T12; arbitrary Configuration object requires missing versioned plugin schemas; supported adapter/transport discovery absent |
| R13 | Generator/object publication | startGeneration POST /generations; getGeneration GET /generations/{generation_id}; listArtifacts GET /artifacts | GENERATION_RUN, ARTIFACT, PLAN, APPROVAL | S4,S5 | T13; artifact list metadata available; no artifact-content/preview endpoint |
| R14 | Runner/export authorization | startValidation POST /validations; getValidation GET /validations/{validation_id}; downloadBundle GET /generations/{generation_id}/bundle | VALIDATION_RUN, VALIDATION_CHECK, GENERATION_RUN, ARTIFACT | S5 | T14; only validated bundle supported, draft-download policy/API absent |
| R15 | Results/reporting | getValidation GET /validations/{validation_id}; listArtifacts GET /artifacts | VALIDATION_RUN, VALIDATION_CHECK, ARTIFACT | S5 | T15; no check log content, per-file status, report export or preview access; evidence fields optional |
| R16 | Authentication/tenant authorization/sandbox | All 15 operations; global bearerAuth | TENANT, USER, MEMBERSHIP, AUDIT_EVENT and tenant keys throughout | S2–S5 | T16; bootstrap/roles/secrets/sandbox decisions pending; ERD constraints narrative only |
| R17 | Shared HTTP contract/generated client | All 15 operations in specs/openapi.yaml | API resources mapped above; no migrations | S1–S5 | T17; structural checks only, no full meta-schema/client generation/runtime conformance |
| R18 | Engineering tracker | N/A | N/A | N/A | T18; M0.2 definition and approval gate remain pending |

Reverse mapping: every operation is linked above. All 14 entities are covered: PROJECT; ANALYSIS_RUN; GRAPH_NODE/EDGE; PLAN; APPROVAL; GENERATION_RUN; ARTIFACT; VALIDATION_RUN/CHECK plus TENANT/USER/MEMBERSHIP/AUDIT_EVENT for security. Broad security linkage does not establish an accepted tenant feature scope. All five screens map to operations or identified gaps. No API/table implementation is claimed.

## Additional consistency findings

| ID | Priority | Finding and consequence | Resolution / proposed owner |
|---|---|---|---|
| TC01 | High | HLD planner promises versioned recommendation/capabilities; API graph nodes lack operation classification, risk, confidence, schema, scopes and eligibility. PlanInput requires caller-selected integration type; no recommendation endpoint/field distinguishes AI choice. PRD FR-04/05 and S4 are not fully supplied by contract. | Define candidate/recommendation model and override rationale; product + API + analysis |
| TC02 | High | S5 requires code preview, actual copy, draft download and artifact statuses; current API exposes metadata plus gated ZIP only. PRD FR-11 reports/stable findings also not represented. | Define explicit access/policy contracts or approved deferral; product + security + API |
| TC03 | High | S2 advanced analysis scope/privacy consent has no request representation. Source.revision required for local; intake expects optional local revision. | Define immutable snapshot acquisition and consent/config boundary; API + security |
| TC04 | High | Approval/generation links are described, but Mermaid PLAN omits capability selection; source/analysis/plugin/generator/hash inputs not fully persisted. Validation metadata has no explicit artifact-set digest. | Specify immutable canonical inputs and artifact-set validation binding; data + security |
| TC05 | Medium | API Node.label required but GRAPH_NODE lacks label; Plan.rationale/risks/capability_ids absent in PLAN; Check command/tool/times absent from VALIDATION_CHECK despite LLD evidence promises. | Expand logical model or document immutable storage keys/JSON mappings; data + API |
| TC06 | High | Check command/exit code/times/log reference optional for passed/failed; schema permits succeeded validation with empty checks. Narrative says pinned required checks must pass. Schema alone cannot prove valid evidence. | Define cross-field semantic validation and negative fixtures; validation + API |
| TC07 | High | Superseding older plans is specified on create, but semantics for multiple selections/concurrent approvals and identity bootstrap, membership roles, revocation remain pending. New multi-tenant design is a proposal. | Ratify auth/state/concurrency ADRs and local bootstrap, idempotency behavior; architecture + security |
| TC08 | Medium | Lifecycle cancellation exists without endpoint; run IDs must be remembered because no run/plan listings or project latest-run links. Dashboard cannot recover full status after reload using Project alone. | Define retrieval/resume flow, status aggregation and cancellation disposition; frontend + API |

PC01–PC07 from PRD intake and G03–G15 from design review remain open unless explicitly resolved by an accepted decision. The new documents offer proposed resolutions for several, but provide no approval evidence. ADR-004–009 can now cite these drafts; their status remains pending rather than accepted.

## Gate and validation

Independent structural checks are saved in technical-validation-results.json and reproducible with validate-technical.py. Checks parse the JSON-compatible YAML, resolve local references, check operation IDs/path parameters, count entities/relationships and test supplied SHA256 manifest entries. They do not prove OpenAPI semantic completeness, database enforcement, MCP compatibility, screen behavior or runtime implementation. No application tests executed.

Next M0.1 gate: review draft authority and CLI/Studio/stack conflicts; decide TC01–TC08 and earlier critical gaps; pin canonical specs/ADRs and M0.2 definition; then approve the reconciled baseline explicitly. No project initialization or later milestone has started.
