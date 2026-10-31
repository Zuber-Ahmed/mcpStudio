# Identity, approval and durable metadata reconciliation — slice 6

Migration `006_identity_approval_metadata.sql` was applied with migrations 001–005 in disposable PostgreSQL. All 138 combined checks passed; the container was removed. No running service database was migrated. Original OpenAPI/data dictionary contracts were preserved.

## Reconciled records

- Audit events now use UUID identities. The old bigint identity remains a separate ordering sequence, not the public ID. Resource IDs derive from immutable event keys. Runtime actor attribution derives from authenticated PostgreSQL session identity/administrative principal mapping; owner/bootstrap operations remain explicitly unattributed (`NULL`) rather than falsely assigned to an operator.
- Validation checks now have immutable UUID identities while retaining their scoped name uniqueness. A private projection derives mandatory status from the pinned policy and finding IDs from same-generation links. The scoped backend function returns the existing OpenAPI Check shape, strips absent execution fields and omits internal identifiers. Queued and executed results both passed the existing OAS 3.0 validator, including format checks.
- Approvals now persist exact plan version, affirmative security confirmation and approved timestamp. The scoped backend approval function checks current plan/binding/hash/version/rights and explicit revocation. Wrong hashes/versions and false/null confirmation are rejected. A stored scoped Approval response passed the unchanged OpenAPI schema.
- Generations persist creation time and the server-derived immutable plan hash. Predecessor references are scoped to tenant/plan/actor; self references are rejected. Validation predecessors remain within the same tenant/generation and cannot self-reference.
- Generate idempotency records now carry UUID, timestamp, admission outcome state and an immutable original response. The original queued admission result survives later generation completion; it is not rewritten into a different replay result.
- Outbox records now contain a server-derived immutable run/plan/actor/request-digest payload, creation timestamp, nonnegative monotonic attempt count and irreversible dispatch timestamp. Runtime backend/worker roles cannot mark delivery directly. The suite exercises those metadata invariants; it does not implement a dispatcher or prove external effects.

All scoped functions use the non-login owner and hardened lookup order. No runtime table/view access was granted. Raw contract views, foreign-tenant reads and worker use of backend approval/projection functions remain denied.

## Reproduction

```powershell
python tools/fixtures/m03/metadata-chain-runner.py
python tools/map-physical-schema.py
```

The current runner applies all six migrations and repeats the previous ownership, path/manifest, role and revocation tests before metadata-specific checks. It validates actual stored/scoped response documents using `openapi-schema-validator` and the unchanged Approval/Check schemas. It captures the migrated column catalog before removing the fixture. Earlier slice reports remain stage-specific and their counts are not additive end-to-end coverage.

## Migration safety and limits

The migration requires explicit plan/security and outcome provenance. It deliberately does not invent confirmed approvals, missing historical manifest bytes or source payloads. Apply first to a fresh reviewed application database; retained experimental data needs an explicit upgrade/reconciliation plan. Existing audit UUIDs introduced during a reviewed upgrade must preserve their separate ordering and prior immutable record content. Do not apply these migrations to Temporal's database. Migration journaling, production credentials/TLS, browser authentication and deployment remain outside this slice.

The new database approval function is not an HTTP endpoint and does not itself implement POST request-idempotency/session protection. Check JSON output demonstrates data-contract compatibility, not actual command execution, secret redaction or full API behavior. Administrative audit actors remain nullable; complete audit attribution policy is still a gate requirement. Replay response storage covers generation admission only; other operation scopes and durable HTTP statuses still require integration. Dispatch counters/timestamps are storage constraints, not recovery or exactly-once delivery proof.

## Remaining gaps

The refreshed field inventory has 33 unmapped declared fields across the 23 entities. All entities are represented, and approval/audit/check/idempotency/outbox field coverage has improved. However physical presence is not semantic completion. The full plan/config/plugin/generator envelope and candidate security/evidence metadata are still incomplete. Principal/project metadata and policy content/version representation are also pending; policy version remains an internal integer versus the logical string contract, and array/JSON projections require explicit serialization. No defaults were added to pretend those decisions were resolved.

ADR-M03-DB06: separate stable UUID resource identity from ordering, derive check mandatory/finding fields from immutable relational authorities, persist original admission outcomes, and require explicit security/version confirmation instead of backfilled approval intent. Consequence: strict upgrade reconciliation and a reviewed application serializer remain necessary.

H01 remains open for the remaining physical/semantic fields and worker/object/API integration. H02 bootstrap/session, H03 real host paths/cancellation/recovery and H04 dependency/image-layer review remain open. Local-first/application-agnostic decisions and five approved screens remain unchanged. Next foundation slice: complete immutable plan/candidate/policy payload design and reconcile exact policy version/serialization before product API exposure.
