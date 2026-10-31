# Foundation admission kernel v1

Implemented 29 October 2026 within M0.3. This is the first physical database slice, not the full 23-entity application migration. It is deliberately isolated under `studio_admission` while the logical-to-physical naming and integration are finalized.

## Artifacts and execution

- `infra/database/migrations/001_admission_kernel.sql`: transactional, one-time empty-schema migration with tenant, actor, membership, project, analysis, plan, approval, consent, run, idempotency and outbox tables.
- `tools/fixtures/m03/admission-transaction-runner.py`: applies the migration in a digest-pinned PostgreSQL container with no network or published ports, uses separate SQL sessions for races, and removes the container in a finally block.
- `docs/quality/admission-transaction-validation.json`: 39 passing checks and verified fixture removal.

Reproduce from the repository root with Python 3 and Docker Linux containers:

```powershell
python tools/fixtures/m03/admission-transaction-runner.py
```

Only this fixture database received the migration. Running local workflow/storage databases were unchanged. The migration intentionally fails if applied twice; a future migration journal must apply each version once. No destructive rollback script is supplied for retained data.

## Transaction behavior

`new_plan` allocates a monotonic version while holding the analysis row lock, replaces the current marker and inserts the new immutable-intent revision in one transaction. The unique partial index permits one current plan per analysis. Two independent sessions produced versions 2 and 3 with one current plan.

`admit` locks the owning analysis, plan, approval, membership and optional consent before creating a run. It rejects missing/stale/revoked approval or inactive membership. Explicit inference scope requires matching tenant/project/actor/source/provider, payload classes contained in the authorized classes, matching redaction and retention disclosure, unexpired consent and no revocation. Empty/null payload classes are rejected. This admission record does not itself perform inference or confer permanent permission for later network calls; execution must recheck current consent before egress.

The actor row serializes idempotency lookup across analyses. Same tenant/actor/operation/key, digest and request body return the original run after current authorization checks. Changed digest or body raises SQLSTATE `P0409`; a future API must map that to HTTP 409. The request body separately binds the implemented scope fields, so reusing a supplied digest with different fields cannot replay. Server-side canonical request hashing for the full application payload remains an integration requirement.

Run, idempotency outcome and one stable `generation.admitted` outbox identity commit together. Concurrent identical admissions returned one resource and one outbox identity. Failed admission and explicit rollback left no new run, key or outbox row. This establishes atomic durable enqueue identity; an external dispatcher still needs retry-safe effect handling and recovery tests. No exactly-once external execution claim is made.

Concurrent approval, membership and consent revocation tests first observed a revocation transaction holding the relevant row, then observed admission blocked by that transaction. Once revocation committed, admission rejected it. Revocation that commits after an admission has already linearized cannot erase that run; execution/export must honor the application's later revocation policy.

## Security and physical-model boundaries

Schema/table/function privileges are revoked from PUBLIC. Functions use a fixed search path and invoker privileges. `admit` explicitly selects PL/pgSQL variable precedence to distinguish parameter names from composite table references. Only a trusted backend may supply tenant/actor identity; no browser receives a database role. Runtime roles and privilege-limited integration are still to be implemented. Table owners can bypass routines, so direct owner DML is not an authorization interface.

The schema is a partial kernel and should not yet be adopted as the production application schema. Missing pieces include graph/candidate ownership, immutable canonical plan payload/policy and candidate binding, full validation/export model, append-only audit, credential-reference storage, safe artifact paths, application identity and least-privilege role wiring, final entity naming, and migration tooling. DB09 is partly covered by digest/terminal-state checks and restrictive references; it is not fully satisfied. DB10 has scoped transactional admission evidence, but actual inference egress remains unimplemented.

Concurrent transactions can still require normal PostgreSQL deadlock/serialization retries; no retrying HTTP/backend layer is implemented here. The fixture uses trusted SQL inputs only, not untrusted string interpolation in an API.

## Decision and gate

ADR-M03-DB01: keep a separately named physical admission slice while completing the full schema, rather than silently promoting the earlier disposable constraint prototype. Consequence: the application must integrate or replace this slice through reviewed migrations; no complete DB01–DB10 claim follows from its passing suite.

H01 is now partially implemented with executable concurrency/consent evidence. It remains open for the full physical model and integration listed above. H02 bootstrap/session, H03 application path/recovery enforcement and H04 complete dependency/image-layer review remain open. M0.3 stays open; the next database slice should address immutable plan/policy/candidate binding and validation/audit constraints before any product admission is exposed.
