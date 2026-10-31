# Contract amendment CA-01

Status: normative review candidate attached to the received OpenAPI `0.1.0-draft` and logical ERD. It defines the required next revision; **does not claim the archived YAML/ERD already contain these changes**. Paths use the proposed `/v1` base. Existing 15 operationIds remain stable unless explicitly expanded below. No feature code or DDL is supplied.

## CA01 — Project and resume contract (R04/R07, TC08)

Extend Project with `updated_at`, `latest_analysis_id`, `latest_plan_id`, `latest_generation_id`, `latest_validation_id` (nullable UUIDs) and server-derived `workflow_status`. listProjects adds `q` (name or source location), `status`, cursor and bounded limit 1–100, default 25; stable ordering by updated_at descending then id. getProject returns identical summary fields. These are projections, not a second persisted state authority.

Status mapping in order: running/queued work → analyzing/generating/validating by active run; any blocking finding or failed/cancelled required run → blocked; succeeded latest validation matching artifact/policy digest → validated; generated but not validated → generated; current unapproved plan → needs_confirmation; succeeded or partial analysis without current plan → ready_for_review; otherwise created. A partial analysis is inspectable but cannot generate a plan in this release. Nonblocking optional-check failures remain visible separately. Dashboard filters use these exact enum values, not integrated/pending. Refresh recovers workflow links without browser-only IDs. Old runs remain reachable through a bounded `GET /projects/{project_id}/runs` (`listProjectRuns`), returning typed run summaries and cursor; it does not expose workflow engine internals.

## CA02 — Acquisition, scan scope and consent (R05/R06)

Source.kind remains local|git. `location` required; `revision` required for git, optional for local. Acquirer resolves git to immutable commit and snapshots actual permitted local bytes; analysis returns snapshot ID and SHA256 digest. Local HEAD is metadata and does not replace dirty-content digest. Ignore rules, max file count/size, symlink escape denial and source access policy are server enforced.

AnalysisInput adds versioned `scope` (endpoint discovery, protocol/schema discovery, prompt/resource discovery, dependency graph) and `semantic_mode=disabled|consented`. A consent reference is required only for consented mode; server rejects it unless provisioned consent matches provider, project, source digest/payload class and expiry. No inference is performed in disabled mode. Requests may not supply arbitrary plugin executables, credentials, network policy or shell commands.

`GET /capabilities` (`getSupportedCapabilities`) exposes installed plugin IDs/versions, supported application detections, generator modes and transports, configuration schema IDs/versions and availability reasons. It reports capability, not a promise of universal support. Consent/secret/session provisioning are host bootstrap responsibilities documented with a non-browser setup flow for initial release; they are not inferred from arbitrary JSON input.

## CA03 — Candidates and recommendations (R09/R10, TC01)

Add `GET /analyses/{analysis_id}/candidates` (`listCandidates`) with cursor/limit and stable finding IDs. Candidate contains id, graph_node_id, operation_type read|write|unknown, side_effects, sensitivity, required_scopes, input_schema, output_schema, eligibility allowed|blocked|unsupported|unknown, reason codes, evidence references, detector ID/version, provenance deterministic|model|manual and confidence (nullable 0–1 with method; no fabricated score). Any executable candidate requires source evidence; absent evidence blocks eligibility. Model-origin findings never gain an AST-verified badge.

Add `GET /analyses/{analysis_id}/recommendation` (`getRecommendation`): id/version, analysis/source digest, recommended_type server|client|both|none, rationale, candidate_ids, risks, required_reviews and supported_generation boolean/reason. It must work deterministically without a remote model. PlanInput adds recommendation ID/version, developer-selected type and `override_reason` required when selection differs. Unsupported types may be inspected/recommended but cannot be approved for generation. None produces an inspectable no-integration plan with no executable approval/generation path.

Node extends label, provenance, confidence method/value and evidence; edge provenance/evidence is optional but unknown edges cannot be presented as verified. getGraph returns a bounded whole graph and `truncated=false`; if policy size would truncate, return explicit limit diagnostic instead of silently dropping nodes. Matrix view derives from the same edges and filters. Large-graph slicing is deferred; no complete-graph claim when a limit is exceeded.

## CA04 — Immutable plan and idempotency (R11/R12, TC04/TC07)

Persist canonical plan payload: source/snapshot digest, analysis ID and analyzer versions, recommendation reference, selected type/candidate IDs and schemas, generator ID/version, versioned plugin configuration with secret references, transport, policy ID/version and required checks, override reason. Serialize deterministically using a named, pinned canonical JSON algorithm; publish its algorithm/version in plan metadata before interoperability testing. Arrays with set semantics sorted and duplicates rejected; no floating confidence scores in executable hash inputs. Exact canonicalization implementation vectors are a readiness gate.

Any change to these inputs creates a new plan revision and invalidates prior approval for new work. Plan revision sequence is per analysis, with only one current plan per analysis; creation/approval serialize transactionally. Already completed artifacts remain historical and clearly bound to the old plan; old approval cannot authorize new generation. APPROVAL stores actor, exact plan ID/version/hash, security review and revocation state. Membership/rights are checked again when scheduling generation/download.

All asynchronous start operations and plan/approval creates accept `Idempotency-Key`. Store tenant+actor+operation+key, canonical request digest, response resource ID and completion state. Same key+same body returns original outcome; same key+different body → 409. Crash/retry must not duplicate workflow admission. Durable outbox is an operational table or equivalently proven mechanism; never rely on Redis for authority.

## CA05 — Persistence alignment (TC04/TC05)

Add versioned immutable `snapshot_reference`, analyzer/plugin/generator versions and required policy record references. GRAPH_NODE gains label/provenance/confidence metadata; candidate and recommendation are versioned records linked to analysis. PLAN gains canonical payload, capability/candidate IDs, rationale, risks, recommendation and override references. JSON payloads must have pinned schemas; do not scatter unvalidated blobs across tables.

GENERATION_RUN records plan hash, generator version and final artifact_set_digest; ARTIFACT retains path/hash/size/storage key. Artifact-set digest hashes a canonically ordered manifest of immutable relative paths, byte digests and sizes. VALIDATION_RUN records the exact artifact_set_digest and policy ID/version. VALIDATION_CHECK stores command, tool version, exit code, start/completion, log reference, skip/not-run reason and stable finding IDs. Add durable consent, idempotency/outbox records as operational requirements. Tenant-scoped composite references and same-plan approval constraints remain required DDL checks, not guaranteed by Mermaid arrows.

## CA06 — Preview, findings and reports (R13/R15, TC02)

Add `GET /artifacts/{artifact_id}/content` (`getArtifactContent`): authorized text preview, media type, digest, encoding, truncated flag, bounded offset/limit; no local filesystem/storage key leakage. Default max preview 256 KiB; binary data uses explicit unsupported-preview response. Copy uses actual returned text and reports clipboard failure. listArtifacts adds derived status draft|blocked|validated|approved and finding/check references; it never implies that one approved file approves a bundle.

Add `GET /validations/{validation_id}/logs` (`getValidationLogs`) for bounded redacted logs and `GET /generations/{generation_id}/report` (`getGenerationReport`) with json|markdown|pdf format. Report includes stable finding IDs and real command evidence. PDF is generated at reporting time and shares the same source record/version; no fabricated success labels. Missing evidence is a finding, not an empty success report.

## CA07 — Validation and download gates (R14, TC06)

Executed passed/failed checks require actual command, tool version, exit code, timestamps and stored redacted log reference. Skipped/not_run requires explicit reason; absent execution fields remain null, never forged. A policy with zero mandatory checks is invalid. A validation cannot succeed until every pinned mandatory check exists, passed, runner completed normally, artifacts match, and generation succeeded. Missing/skipped/not_run/failed mandatory check denies approved bundle, even if HTTP schema structurally permits the record.

Initial mandatory categories: generated-code compilation/schema validation, MCP discovery/invocation contract, authorization and malformed-input negative tests, secret scan, domain-service context propagation and sandbox policy enforcement. Particular tool versions/commands are pinned by fixture/runtime policy; unavailable offline tools result in blocked export, not automatic exemption. A production deployment/push is not a mandatory local MVP check.

Keep downloadBundle as the approved path. Add `GET /generations/{generation_id}/draft-bundle` (`downloadDraftBundle`), authorized local operator only and explicit draft acknowledgement. Only finalized immutable generated files are downloadable; no partially written output or secrets. Manifest/report says DRAFT / NOT APPROVED and records missing checks, digests and policy. Draft download creates an audit event and cannot alter validation/approval state. No push/deploy/merge endpoint.

## CA08 — Auth, cancellation and errors

Retain server-derived tenant/project authorization across all operations; browser bootstrap/session contract must be written before exposure (BL08). Response 401 missing/invalid authentication; 404 inaccessible resource under a consistent anti-enumeration policy; 403 known forbidden action; 409 stale/conflicting/idempotency/gate state; 422 semantic invalidity; 429 limits. Errors include code/message/request_id and structured safe reason codes where useful.

Polling is the initial progress mechanism; real-time events and user cancellation controls are deferred. Internal cancelled state may represent operator/shutdown outcomes and does not imply a cancellation endpoint. Job retries are bounded orchestrator behavior; user retry creates a fresh run with explicit previous_run_id. Plan approval revocation is a backend operation `POST /plans/{plan_id}/revocations` (`revokePlanApproval`), restricted to current operator, invalidating future admission; it does not silently kill an in-progress job. Retrospective artifact/gate revocation must block future approved exports under current policy while preserving audit evidence.
