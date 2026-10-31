# Policy-version resource identity — foundation slice 9

Migration `009_policy_version_identity.sql` closes SCHEMA-D01 by applying the agreed DB01 tenant-unique entity identity rule. The current nine-migration suite passed 118 checks, including current role/concurrency regressions and a separate legacy preflight fixture. Both databases lived in one disposable, network-disabled container, which was removed. Running service databases were not changed.

## Identity model

- `validation_policy.id` identifies one immutable version resource and is UNIQUE with tenant_id.
- `policy_key` is the stable lineage key within a tenant.
- Exact opaque `version_label` values are unique within that lineage; `01` and `1` remain different versions.
- The existing internal integer revision is also unique within the lineage. It remains a private relational key, not the public label.
- The existing composite foreign keys are retained as additional consistency checks. Plans and validations resolve the exact version-row UUID and immutable label; a lineage-style UUID cannot impersonate a different version.

Policy content bytes remain immutable and hash-bound. Changed policy content requires another version-row UUID/label and a new canonical plan/approval. No old approval or canonical payload is rewritten to fit the normalized identity. This resolves the physical identity conflict without changing the OpenAPI/data dictionary or accepting a DB01 exception.

## Executed validation

The suite applies migrations 001–009 fresh, publishes distinct policy-version UUIDs sharing one lineage, and rejects duplicate UUIDs, duplicate lineage labels and duplicate internal revisions. It preserves exact labels in scoped Plan/validation projections and confirms previously stored canonical bytes are unchanged. Same UUIDs/labels in a different tenant remain independently scoped. Full canonical contract validation, role boundaries, current concurrent admission/revocation/export and metadata checks are included in the current fixture.

The legacy preflight test creates a minimal duplicate-identity policy table in a second disposable database. Migration 009 explicitly rejects it before adding constraints. Tests compare stored IDs, revisions, labels and exact content bytes before/after the failure and verify no partial unique constraints remain. This tests the conflict preflight; it does not implement or simulate a production upgrade/reapproval workflow.

```powershell
python tools/fixtures/m03/policy-identity-runner.py
python tools/map-physical-schema.py
```

The runner captures the current migrated catalog before cleanup. Earlier suites and reports remain historical schema-stage evidence; their counts are not additive complete coverage. The current acceptance review is `docs/quality/schema-acceptance-review.json`.

## Upgrade and operational boundary

Migration 009 never assigns replacement IDs to retained approvals or edits frozen canonical bytes. If an existing experimental database reused a policy UUID across versions, the preflight blocks the transaction. Its operator must prepare an explicit reviewed reconciliation/republication/reapproval strategy and retain old evidence; no automatic mass rewrite or destructive rollback is provided. Apply only through a reviewed application migration process, never to Temporal's database.

No product policy editor, role-management UI, model call or new database privilege was introduced. The current application remains fixture-only. Credentials, browser sessions, installed plugin validation, worker/object truth and dispatch recovery remain outside this identity change.

## Decision and gate

ADR-M03-DB09: use a distinct immutable policy-version resource UUID and a separate stable policy_key, with tenant-scoped uniqueness for identity/labels/internal revisions. Retain composite FKs for defense in depth. This follows DB01 directly and preserves exact labels and canonical references; the provisional shared-version UUID representation is superseded.

SCHEMA-D01 is CLOSED. All 23 logical entities remain represented with zero unmapped dictionary fields. H01 still includes integrated data/publisher/plugin/worker/object semantics; H02 browser bootstrap/session, H03 actual path/cancellation/recovery and H04 complete dependency/image review remain OPEN. M0.3 is not marked complete and no later milestone starts. Next foundation work: runtime dependency/image readiness review, then reconcile remaining integrated security/execution acceptance holds before the M0.3 approval gate.
