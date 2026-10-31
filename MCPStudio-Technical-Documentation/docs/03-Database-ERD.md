# Database ERD and persistence design
Status: NEW DRAFT PostgreSQL logical model; not recovered schema or executable migration.

## Entities and relationships
Tenant owns Projects and Memberships; User has Memberships in Tenants. Project has AnalysisRuns; AnalysisRun has GraphNodes, GraphEdges and Plans. Plan has Approvals and GenerationRuns. Approval authorizes GenerationRuns. GenerationRun has Artifacts and ValidationRuns. ValidationRun has ValidationChecks. Tenant has AuditEvents.

Each child belongs to exactly one parent. A parent may have zero or many children. Generation references exactly one plan and one approval; approval must refer to that same plan. Graph edges connect two nodes in the same analysis run. Tenant ownership is inherited and stored explicitly for enforcement.

## Key and constraint policy
All entities except membership have UUID primary keys; membership uses (tenant_id,user_id). Tenant-owned rows additionally expose UNIQUE(tenant_id,id). Every parent reference uses (tenant_id,parent_id) foreign keys. Graph edges require composite references (tenant_id,analysis_run_id,from_node_id/to_node_id) to the corresponding node keys. Generation's (tenant_id,plan_id,approval_id) must reference an approval key covering those columns, preventing approval from another plan. These constraints are narrative requirements; the Mermaid file illustrates the logical model, not complete DDL.

Plan UNIQUE(tenant_id,analysis_run_id,version). Version is a positive integer; content_hash is a 64-character SHA256 hex string. Approval stores actor, plan hash and timestamp. Authorization must compare approval hash with immutable plan content; a foreign key alone cannot enforce it. A user may be removed from membership while historic approvals remain as audit evidence; current rights are checked again before generation.

Run/artifact timestamps are UTC. ValidationCheck UNIQUE(tenant_id,validation_run_id,name); mandatory-check names come from pinned policy, not user input. Terminal state transitions require completed_at. Artifact paths are relative; content digest, media type, byte count and storage key are required. Graph/evidence JSON is versioned and schema-validated before persistence.

## Indexes and transaction choices
Proposed indexes: projects(tenant_id,created_at,id), analysis_runs(tenant_id,project_id,created_at), plans(tenant_id,analysis_run_id,version), generation_runs(tenant_id,plan_id), artifacts(tenant_id,generation_run_id), validations(tenant_id,generation_run_id,created_at), audit_events(tenant_id,created_at). Index graph lookups by analysis run and endpoints. Benchmark JSON indexing before adding broad GIN indexes.

Use optimistic version checks for plan approval and row locking for generation admission. Outbox delivery needs an additional operational table or workflow-equivalent durable mechanism; it is deliberately not represented as a product entity in this ERD. No migration or performance verification is supplied.

## Data lifecycle
No cascade deletion of approvals, validations or audits is proposed. Project deletion is not exposed by the draft API. Retention periods, tenant erasure, user anonymization, source snapshot lifetime, artifact expiry, encrypted backup and restore procedures need explicit decisions. Avoid retaining source contents in graph JSON; store source evidence references and optional minimized snippets subject to policy. Secrets never belong in these tables.

## Model/API mapping
Project -> Project; AnalysisRun plus graph -> Analysis/Graph; Plan -> Plan; Approval -> Approval; GenerationRun -> Generation; Artifact -> Artifact; ValidationRun and ValidationCheck -> Validation/Check. Tenant/User/Membership/AuditEvent are internal entities; identity/admin endpoints are outside this draft. Source/config/policy hashes tie these records to the same immutable input.
