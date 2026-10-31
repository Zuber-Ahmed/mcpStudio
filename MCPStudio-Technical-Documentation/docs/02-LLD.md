# Low-Level Design
Status: NEW DRAFT. Interfaces, states, constraints and failure behavior below require review.

## 1. Module contracts
Acquirer.resolve(source, revision, access_reference) returns Snapshot(id, digest, immutable_root). It canonicalizes local roots, rejects traversal/symlink escapes and applies ignore/size limits. Acquisition of remote repositories is distinct from analysis and subject to egress policy.

Analyzer.analyze(snapshot, plugin_version, budget) returns graph, candidates, evidence and diagnostics. Each evidence reference carries source path, source digest, line interval and detector version. Missing evidence cannot be promoted to certainty. Plugin failure produces a partial run with explicit diagnostics; it never invents capabilities.

Planner.build(analysis_run, integration_type, capability_ids, config, policy_version) returns immutable Plan(version, content_hash, rationale, risks). Recommended type and developer-selected type are separate data. A new plan version is created for every material change.

Generator.generate(plan, approval, snapshot) returns immutable artifact metadata. It receives only verified references and permitted configuration. Candidate tools must retain input/output schema, authorization context and domain-service mapping. A dangerous or unsupported mapping blocks generation.

Validator.validate(generation_run, policy_version) returns named CheckResult records with status, mandatory flag, command/tool version, exit code, start/end times and log reference. Compile, schema, authorization and protocol checks are policy-driven; skipped or not_run is never passed.

## 2. Business states
Analysis: queued -> running -> succeeded | partial | failed | cancelled. Only succeeded analysis may create a plan in this draft; partial output remains inspectable. Allowing reviewed partial analysis is an explicit future decision.

Plan: draft -> approved -> superseded. Editing creates a new version; old approvals never carry forward. Revocation and regeneration policy is open; this draft treats superseded plans as ineligible for new work.

Generation: queued -> running -> succeeded | failed | cancelled. It produces artifacts but does not imply validation success.

Validation: queued -> running -> succeeded | failed | cancelled. Individual checks: passed | failed | skipped | not_run. Validation succeeds only if every mandatory check exists and passed and the runner finished normally. Required-check list must come from a pinned policy, preventing success from an empty check list.

These are proposed internal/API states. They do not claim the conflicting Stitch labels or PRD's combined state sequence are already reconciled.

## 3. Approval and generation transaction
BEGIN; load tenant-scoped plan FOR UPDATE; require approved status, current plan version, matching source/config/policy hashes and exact approval hash; authorize current actor; insert generation run and outbox event; append audit event; COMMIT. The outbox dispatcher starts one durable workflow keyed by generation ID. Unique constraints prevent duplicate dispatch effects. Network retries after uncertain commits require client readback; request-idempotency storage is not specified in this draft.

Plan hash is SHA256 over a canonical serialization of source digest, analysis/plugin versions, selected integration type, capabilities, schemas, config with secret references, policy version and generator version. Exact canonicalization format must be pinned before interoperability testing. The confirmation UI sends the server-issued hash and plan version; the server recomputes/compares it.

Changing integration type must invalidate confirmation per recovered requirements. This draft proposes also invalidating on source, capability, adapter, transport, configuration, policy or generator changes. The expanded set is NEW and needs ratification.

## 4. Persistence and boundaries
Store each business row under tenant_id; use composite foreign keys (tenant_id, resource_id). Resource IDs are UUIDs. Each project has many analysis runs; every plan belongs to one analysis run; every generation references one plan and one approval; artifacts belong to a generation; validations belong to a generation and a pinned policy. See database narrative for cardinalities and enforcement gaps.

Object writes use temporary keys followed by digest verification and publication of immutable metadata. A failed upload cannot mark a run succeeded. Downloads proxy through the API after tenant authorization and validation checks; do not return permanent public object URLs.

## 5. API implementation behavior
Authenticate before resource existence disclosure. Return 401 for missing/invalid authentication, 403 for known forbidden operations, 404 for absent or inaccessible resources according to a consistent anti-enumeration policy, 409 for stale plan/approval/state conflicts, 422 for semantically invalid requests and 429 for limits. Error bodies contain code, message and request_id without secrets or raw stack traces.

List operations use opaque cursor pagination with a bounded limit. Only project lists and artifact lists are exposed in this draft; a dashboard summary endpoint, graph query pagination, cancellation and event streaming remain extensions. The current graph response is bounded by analysis policy; large-graph slicing is unresolved.

## 6. Isolation and filesystem controls
Read source snapshots only. Generate in a separate output root; normalize every emitted path, reject absolute paths, traversal, symlinks and collisions. Validation runs with explicit CPU/memory/time limits, a temporary workspace, restricted network and approved commands. Source writes, dependency installs, production calls and package publication are separate actions requiring defined policy and consent.

## 7. Failure recovery
Worker crash: orchestration retries bounded deterministic activities with stable run IDs. Policy/schema failure: preserve diagnostics, mark failed, require user correction. Storage failure: retain pending status and retry publication. Cancellation is modeled but no cancellation endpoint is included yet. A later implementation must specify cooperative cancellation and cleanup before exposing it.

## 8. Planned test matrix
- Unit: canonical plan hashes; path handling; schema mapping; mandatory-check gate with empty, skipped and failed checks.
- Integration: tenant-scoped composite references; approval/generation race; object metadata publication; duplicate dispatch; workflow restart.
- End-to-end: create project, analyze fixture, inspect evidence, create/revise/approve plan, generate, validate and download.
- Security: cross-tenant resource IDs, stale approval replay, source prompt injection, malicious repository script, secret leakage and unauthorized domain invocation.
- Compatibility: pin MCP version/SDK/transport and exercise generated artifacts against a selected client; no compatibility claim is made here.
