# Follow-up QA: executable payloads, metadata and policy identity

Date: 30 October 2026, Asia/Calcutta. Latest completed Software Engineer turn reviewed: `01a188e6-8f80-70f2-83f4-0faee48d0819`. Runtime dependency/image review was in progress and is excluded from this verification.

## Result

**The completed nine-migration fixture passed 120 checks in an independent disposable database run:** the engineer's 118 current-chain checks plus explicit QA-01/QA-02 regressions. Container cleanup succeeded. No existing service database, engineer evidence or product implementation was modified.

An additional field-presence check verified **209 declared fields across all 23 logical entities** against the independently captured catalog. No missing mapped targets were found. Migration hashes remained unchanged during verification. The source-contract integrity check still matches all six manifest hashes, with 24 resource and three session operations.

The passing fixture covers the newly completed slices 007–009: full CanonicalPlan/Candidate/Plan/PolicyReference schema checks; exact candidate/source/configuration/plugin/generator/policy binding; principal/project metadata and scoped roles; current admission/revocation/export races; policy-version resource UUID uniqueness; distinct opaque labels `01` and `1`; and fail-closed legacy identity migration without changing stored bytes. Existing approvals cannot authorize changed bound configuration or pins.

## Defect tracking

- QA-01: same-tenant/different-project snapshot reference remains rejected under migration 009 (SQLSTATE 23503).
- QA-02: admitted generation hash mutation remains rejected under migration 009 (SQLSTATE 23514).
- QA-03: the earlier documented Windows default-encoding reproduction issue remains open. This run explicitly enabled UTF-8; it does not demonstrate that the original default invocation is fixed. Runtime runners still omit an explicit subprocess encoding.
- No new failing database assertion was found in this run.

## Evidence and reproduction

- `nine-migration-inputs.json`: completed turn and runner/helper/migration hashes.
- `nine-migration-validation.json`: 120 passing check entries and cleanup confirmation.
- `nine-migration-catalog.json`: independently captured schema after migrations 001–009.
- `nine-migration-field-verification.json`: 23-entity, 209-field presence result.

From the repository root with the existing isolated Python tooling and Docker Linux engine:

```powershell
python -X utf8 tools/fixtures/m03/qa-policy-verification.py
python -X utf8 tools/fixtures/m03/qa-field-mapping.py
```

The QA wrapper freezes migration source text and redirects the completed integration suite's evidence writes into this directory. This is an independent rerun plus two QA probes, not 120 independently authored tests; counts are not additive with earlier stage-specific suites. Field mapping checks existence, not semantic implementation.

## Acceptance limits

Policy identity reconciliation is verified for this foundation chain. Full M0.3 acceptance remains HOLD: real worker/object bytes and trusted source evidence, installed plugin configuration validation, all-operation idempotency/dispatch recovery, browser bootstrap/session controls, OS path/cancellation/recovery and complete runtime dependency/image review still require their stated evidence. Five-screen visual fidelity and application end-to-end behavior remain unavailable. No milestone transition or product sign-off follows from this fixture result.
