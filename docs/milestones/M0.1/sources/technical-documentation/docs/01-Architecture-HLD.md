# Architecture / High-Level Design
Status: NEW DRAFT. Retained principles are identified below; component responsibilities and topology are proposals.

## 1. Purpose and scope
MCP Integration Studio inspects an explicitly selected source revision, builds an evidence-backed architecture view, recommends integration capabilities, obtains developer approval, generates isolated adapters and validates downloadable artifacts. It preserves an application-agnostic core with versioned analyzer/generator plugins. Support for any particular language is a separately tested plugin capability, not a promise to understand every application.

Five retained screens: Dashboard, Project Setup, Architecture Explorer, MCP Studio, Results & Validation. Stitch is the visual reference; OpenAPI is intended to be the HTTP contract reference. The backend must enforce permissions and approval gates.

## 2. Evidence and baseline boundaries
The recovered conversation describes Next.js/React/TypeScript and a retained Go API, Python workers, PostgreSQL, Redis, Temporal and S3-compatible storage. The recovered PRD instead proposes a CLI-first Node/TypeScript engine with JSON/SQLite persistence. The following Studio topology follows the later conversation as a DRAFT interpretation, pending reconciliation; it does not assert the stack was independently approved. No runtime manifests or implementation were recovered.

## 3. Logical components
- Web UI: five-screen workflow, evidence navigation, plan review, validation results. Generated API client is a proposal; browser state never authorizes generation.
- Go control API: authenticated access, project ownership, revision checks, plan approval, job initiation, artifact download gates and audit events.
- Analysis workers: read-only acquisition, deterministic parsing, capability discovery, evidence extraction and normalized graph construction.
- Planner and policy evaluator: produce a versioned recommendation from normalized findings; explicit unknowns and blocked capabilities remain visible.
- Generator: turns an approved immutable plan into a separate artifact tree; preserves source application authorization and domain-service boundaries.
- Validation runner: executes allowed checks in an isolated environment; records actual execution evidence and mandatory-check disposition.
- PostgreSQL: proposed source of truth for projects, runs, graph, plans, approvals, artifacts, validation and audits.
- Temporal: proposed durable orchestration; workflow retries must not repeat irreversible effects. Database records expose business status, not workflow history internals.
- Object storage: immutable source snapshots, reports, generated bundles and logs. PostgreSQL stores identifiers and hashes, not binaries or credentials.
- Redis: optional ephemeral cache/progress acceleration; never sole authority for approvals or validation gates. MVP necessity remains unresolved.

## 4. Data and control flow
1. User registers a local workspace or repository URL and immutable revision. Credentials are resolved by reference outside persisted source metadata.
2. API validates ownership and acquisition policy; a worker creates a read-only snapshot and records its digest.
3. Analyzer plugins publish graph nodes, edges, capabilities and evidence. Unsupported constructs are marked unknown.
4. Planner produces an immutable plan revision, integration type, selected capabilities, configuration digest, policy version and risk rationale.
5. User reviews the exact plan and confirms security. API records an approval bound to plan content hash and actor.
6. Generation atomically checks this approval and schedules work. Generation writes only to isolated output.
7. Validation records passed, failed, skipped or not_run checks. Only all mandatory checks passed permits a validated bundle download.
8. User reviews output. Download does not merge, deploy, push or modify the original application.

## 5. Trust and security boundaries
Source files, comments, repository instructions, model responses and external server metadata are untrusted data. Analysis must not execute repository scripts. Plugins receive a bounded source view, deadline, memory budget and output schema. Optional model inference requires explicit consent and a documented, redacted payload; deterministic local analysis must remain usable without remote inference.

Authentication mechanism is proposed as bearer access tokens; issuer, audience, identity lifecycle and local bootstrap are unresolved. Every resource lookup is scoped to authenticated tenant and project membership. Tenant IDs are derived by the server, never accepted as authority from request bodies. Composite database keys prevent cross-tenant references; application authorization remains mandatory even if row-level security is later added.

Workers receive no production credentials. Secret references resolve at execution through an approved local secret mechanism; raw tokens must not enter logs, plans or bundles. DB adapters must reuse domain authorization or be blocked; direct database access is not a default escape hatch.

## 6. Local deployment proposal
Local-first is retained: no paid hosting or cloud deployment required for MVP. A proposed Compose environment runs web, API, isolated workers, PostgreSQL, Temporal and local S3-compatible storage; Redis is optional pending need. Bind control ports to loopback by default. Service data volumes have explicit retention and backup procedures. Do not expose a developer stack to an external network by default.

The exact container images, versions, ports, worker sandbox technology and Windows filesystem strategy remain open. A deployment manifest is not included because none was recovered or validated. Future cloud packaging must preserve the same approval, data and egress boundaries.

## 7. Reliability and observability
Use request IDs, run IDs, structured redacted logs and append-only audit records. Reconcile stranded queued/running jobs with workflow status after restart. Persist output digests before marking a job successful. Retries are bounded and classified by transient versus deterministic failure; timeouts never imply pass. Use an outbox or equivalent durable enqueue mechanism to avoid a committed run without scheduled work (new proposal).

Performance targets, concurrency caps, retention periods, backup RPO/RTO and availability SLOs require measured baselines. The PRD's under-five-minute report target and fixture correctness target remain unverified proposals.

## 8. Architecture acceptance
Demonstrate the complete five-screen flow against one immutable revision; reject cross-tenant reads; prove source scripts do not run during scanning; deny generation with stale approval; deny validated download after failed/skipped mandatory checks; verify restart recovery and local operation without remote inference. These are planned acceptance checks, not executed tests.
