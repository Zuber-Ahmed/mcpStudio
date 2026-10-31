# Principal/project metadata and schema acceptance — slice 8

Recorded 29 October 2026. Migration 008 adds the seven remaining metadata fields. The current eight-migration suite passed 104 checks and removed its network-disabled PostgreSQL fixture. No running workflow/storage database was migrated.

All 23 logical entities and every declared dictionary field now have an explicit physical column or immutable projection. **Unmapped fields: 0.** This closes field-inventory coverage, not complete schema semantics or the M0.3 gate.

## Implemented metadata and boundaries

Tenant names and unique immutable actor subjects are required. Membership explicitly uses the approved initial `operator` role plus active state; unsupported administrative roles are rejected. Authenticated runtime identity must still match its enabled principal record, tenant/actor and active operator membership. No signup, tenant administration, broader role-management interface or bootstrap credentials were added.

Projects now carry nonblank bounded name, structured Source metadata, server-maintained timestamps and immutable tenant/source/creation identity. Metadata rename is tested through administrative SQL as a storage invariant; no new rename API is introduced. The scoped backend metadata reader denies foreign tenants, workers and deactivated operators, while raw table writes remain unavailable to runtime roles.

Source accepts the existing local/Git fields, requires a Git revision, rejects unknown fields, empty/nonstring values, URL userinfo and obvious credential query parameters. Opaque credential references remain metadata. Source and ProjectInput documents pass the unchanged OpenAPI schemas. No local path or remote URL is acquired or executed. These structural/obvious-secret checks are not complete URL parsing, SSRF protection, secret redaction, OS secret-store resolution or host-root authorization. Encoded/novel secret-bearing input still needs the real intake policy. The metadata reader does not claim the full Project workflow/latest-run response is implemented.

Schema review identified candidate UUID reuse across analyses within a tenant. Migration 008 adds `UNIQUE(tenant_id,id)` and the current fixture verifies reuse fails. No duplicate experimental identity is silently merged.

## Current acceptance regression

The suite applies migrations 001–008 to a fresh database, repeats the full canonical payload/approval/artifact/validation path with actual restricted logins, then validates metadata and current-schema race behavior. Simultaneous identical admissions return one run and one outbox identity. A real revocation transaction is observed holding its lock; admission and export are observed waiting behind it and are rejected after commit. Revocation blocks assigned unfinished publication and leaves that run queued. Exact opaque policy labels survive validation binding.

```powershell
python tools/fixtures/m03/schema-acceptance-runner.py
python tools/map-physical-schema.py
```

The current catalog and dictionary hashes support `physical-model-mapping.json`; `schema-acceptance-review.json` consolidates DB01–DB10. Earlier slice reports remain stage-specific evidence and their check counts are not additive current end-to-end coverage. The fixtures use trusted evidence/command/object metadata and do not prove execution of a product analyzer, worker, API or generator.

## DB01–DB10 review

| Requirement | Foundation evidence | Still required |
|---|---|---|
| DB01: Tenant-scoped identities | Runtime scope/tenant keys and tenant-unique candidate UUID enforced; all fields mapped. | Versioned policy uses repeated stable id plus internal revision. Reconcile this explicitly with literal UNIQUE(tenant_id,id) entity rule before full acceptance. |
| DB02: Same-analysis graph/candidate ownership | Composite graph endpoint and candidate-node FKs; earlier negative fixtures and current linked pipeline. | Actual analyzer/evidence content and immutable analysis-output sealing remain integration work. |
| DB03: Monotonic plan versions | Analysis locks, uniqueness/current-plan index and sequential publication; earlier concurrency fixture. | Complete current-schema crash/retry/recovery publication coverage remains required. |
| DB04: Approval and current rights | Exact plan/hash/version/security confirmation, active operator, explicit revocation; current real-role concurrent admission/export race passed. | HTTP identity/session and all-operation idempotency/security lifecycle remain unimplemented. |
| DB05: Pinned source/recommendation/candidate/configuration | Full canonical payload/source/recommendation and selected security metadata bound and schema validated. | Installed plugin/configuration-specific schema and real source/detector/generator truth need application integration. |
| DB06: Validation artifact and policy binding | Exact stored manifest/digest and immutable exact policy-label reference; scoped positive pipeline. | Actual object bytes, worker command/evidence integrity and publication recovery are not proven by fixture records. |
| DB07: Mandatory checks and evidence rules | Nonempty/unique required checks, real metadata shape, frozen finalized records; scoped Check documents validate. | Actual policy execution, optional-check semantics and secret-safe logs/findings require integrated tests. |
| DB08: Idempotency and durable dispatch | Current concurrent requests return one run/outbox identity; original admission outcome/payload immutable. | Generation-only implementation; dispatcher leases/recovery/effect deduplication and every other POST remain open. |
| DB09: Retention, safe paths and secret boundaries | Retained immutable rows, UUID audit, terminal times, portable relative paths and no raw runtime grants. | OS credential references/secret redaction, administrator attribution policy, real root/symlink checks and cleanup still required. |
| DB10: Scoped consent | Earlier admission consent/expiry/revocation fixture; initial backend wrapper enables no inference. | No real inference provider/egress path or consent-enabled scan exists; execution-time provider/payload consent proof remains open. |

## Design issue and next gate

SCHEMA-D01 remains open: policy versions currently share a stable policy UUID and use a private integer revision, with exact opaque public labels. This supports immutable policy references but does not literally expose UNIQUE(tenant_id,id) for each policy-version row as DB01 specifies. Field presence and successful projections cannot resolve that identity rule. Next foundation work should normalize policy-version row identity while preserving exact canonical references, or present an explicit baseline reconciliation for approval. No exception is inferred here.

H01 remains partial for that identity issue and integrated data semantics. H02 requires implemented browser bootstrap/session controls; H03 requires actual acquisition/path, worker cancellation and recovery proof; H04 requires complete runtime dependency/image review. All four holds remain open. No milestone transition or infrastructure-only waiver is asserted.

ADR-M03-DB08: retain an explicit single local operator role and immutable project source identity; do not populate missing metadata or identity from invented defaults. Retained experimental data needs a reviewed reconciliation before applying this required-field migration. Use a dedicated application database and migration journal, never Temporal's database. Production provisioning/upgrade tooling remains pending.

Local-first/application-agnostic decisions and the five approved screens are preserved. No real repositories, production credentials, product UI/API, deployments, commits or pushes were introduced. The next approval gate remains M0.3 readiness after required tests and design issues close or are explicitly dispositioned by the user.

## Subsequent resolution of SCHEMA-D01

SCHEMA-D01 is now CLOSED by migration 009. Each immutable policy-version row has a tenant-unique UUID; policy_key groups lineage, and opaque labels/internal ordinals have separate lineage uniqueness. Earlier open-issue text records the original review. POLICY-VERSION-IDENTITY.md and the updated machine acceptance review are authoritative for the resolution. Runtime/security acceptance holds remain open.
