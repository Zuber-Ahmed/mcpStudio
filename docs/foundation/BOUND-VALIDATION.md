# Bound plans, validation and audit — foundation slice 2

Implemented 29 October 2026. `002_bound_validation.sql` follows `001_admission_kernel.sql` and extends the isolated `studio_admission` physical model. Both migrations were applied together in a fresh disposable PostgreSQL container; 59 checks passed. Running local workflow/storage databases were not changed.

## Implemented behavior

- Immutable policy versions require nonempty, unique, nonblank mandatory check names.
- Immutable candidate records carry an analysis scope, eligibility flag and source reference. Binding rejects foreign, duplicate, empty or ineligible selections and derives selected-candidate links from the bound bytes.
- Immutable plan payload bytes must hash to the plan revision hash and match analysis, source digest, policy ID/version, server mode and stdio transport. Plan revision identity and source identity cannot be edited; publishing a new revision still updates the current marker under the parent lock.
- Generation admission requires a bound plan. Admitted run identity is fixed, and terminal generations cannot be reopened.
- Immutable artifact-set publication identities pin validation to exact run/digest. Validation requires succeeded generation and the plan's exact immutable policy version. Queuing seeds every mandatory check as `not_run` with a reason.
- Passed/failed executions require command, tool version, exit code, ordered timestamps and log reference. Passing requires exit zero; a failed assertion may have exit zero but requires a reason. Skipped/not-run records require a reason and no execution metadata. Check identity is fixed, deletion is denied and finalized checks cannot be rewritten.
- Approved export records require a current plan, nonrevoked matching approval, current actor membership, succeeded generation, normally completed validation, matching artifact digest, and all required checks passed. Skipped/not-run/missing passes, failed assertions and failed/cancelled execution states cannot meet the gate. Export rechecks authorization under row locks and waits behind concurrent approval revocation.
- Audit events are inserted transactionally for binding, generation state, approval state, validation state and approved export. UPDATE, DELETE and TRUNCATE are denied on audit records; export records are retained. Rolling back an export also rolls back its audit event.

No draft export path is added by this slice. No bundle is generated, downloaded, executed or deployed.

## Canonicalization boundary

The fixture serializes a normalized envelope using the already-pinned `rfc8785` library and computes SHA-256 before publishing it. PostgreSQL checks SHA-256 against the exact stored bytes and checks embedded ownership/policy fields. PostgreSQL JSONB parsing is **not** an RFC 8785 canonicalizer: it does not establish JCS ordering, duplicate-key rejection or full application schema correctness. A trusted application publisher must normalize IDs/set arrays, reject duplicates and malformed Unicode, validate plugin/config schemas, and compute canonical bytes and hash server-side before invoking these routines. The test envelope is a focused physical-binding fixture, not the complete production plan resource.

The current candidate eligibility flag/source reference are trusted stored inputs. This slice does not implement deterministic analysis, evidence validation or plugin eligibility evaluation. Policy checks are immutable names pinned by version; a complete executable policy and plugin/config/version payload still need application integration. Optional-check policy semantics remain to be designed explicitly before production use.

## Evidence and trust limits

`tools/fixtures/m03/bound-validation-runner.py` runs the complete slice with no network or published ports. It covers positive approval, hash/scope/candidate mismatches, policy mutation, mandatory-check enforcement, frozen evidence/audit, rollback and an independent-session export/revocation race. `docs/quality/bound-validation-results.json` records the exact results and verified fixture removal.

```powershell
python tools/fixtures/m03/bound-validation-runner.py
```

Python authoring tools require the existing isolated `work/python-tools` environment; Docker uses the recorded PostgreSQL digest. The original admission-only suite remains a migration-001 regression fixture. It does not represent migration-002 compatibility because 002 intentionally requires bound payloads and makes approval revocation irreversible.

Execution evidence is trusted fixture data here. A database record cannot establish that a command actually ran or object bytes actually match a digest. Worker evidence ingestion and object publication must perform those checks before insertion. Current runtime roles remain unprovisioned; schema/table/function/sequence access is revoked from PUBLIC, and only a trusted backend should receive narrowly scoped privileges. A database owner can disable triggers, so append-only triggers do not provide administrator-proof tamper resistance. No secrets or command/log bodies are copied into audit metadata, but this slice does not provide a complete application secret-redaction system or complete actor-attributed audit lifecycle.

## Traceability and remaining gate

| Requirement | New evidence | Remaining boundary |
|---|---|---|
| DB03/DB05, SEM-PLAN | Frozen revision/source bytes and same-analysis eligible candidate links | Full recommendation, plugin/config/security-review schema and application publisher |
| DB04, SEM-APPROVAL/EXPORT | Current plan/actor/approval rechecked at export, including concurrent revocation | Runtime roles and complete approval/revocation lifecycle |
| DB06/DB07, SEM-VALIDATION | Immutable artifact/policy binding and nonempty mandatory execution checks | Verified object publication and actual worker evidence ingestion |
| DB09 | Terminal states, retained approval/run/validation/export records and append-only audit triggers | Safe artifact paths, credential references, full lifecycle audit/redaction and migration tooling |

ADR-M03-DB02: persist exact canonical bytes plus immutable policy version and publication identity; do not reconstruct executable payload from mutable projections. Consequence: changing bytes, candidates or checks requires a new revision/run rather than editing approved history. Keep `completed` validation distinct from successful mandatory checks; the export gate must evaluate each pinned check.

H01 is materially advanced but remains open for the complete logical-to-physical model, full payload validation and privilege-limited backend integration. H02 browser bootstrap/session, H03 path/cancellation/recovery and H04 image/dependency review remain open. M0.3 is not marked complete. Next foundation step: introduce and test least-privilege backend/worker database access and finish the remaining physical-model mapping before any product API is exposed.
