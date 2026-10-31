# Follow-up verification: completed database slices 001–006

Monitored completion: Software Engineer turn `01a188cd-21d3-75f3-99a8-95cbb0f420ea`. The next immutable-payload slice was in progress at inspection and is excluded from this review. Six completed database slices have been delivered since the initial QA review: admission, bound validation/audit, runtime roles, source ownership, artifacts/revocation, and identity/approval/durable metadata.

The independent harness `tools/fixtures/m03/qa-metadata-verification.py` freezes migration source text and records input hashes, reuses the completed integration suite, adds an explicit QA-02 hash-update probe, and redirects all catalog/result writes into this QA directory. The suite runs against a uniquely named, network-disabled, disposable digest-pinned PostgreSQL container. Existing service databases and engineer evidence are not modified.

## New finding QA-03 — P2: documented Windows test invocation needs explicit UTF-8

Running the documented Python invocation with this host's default encoding fails at the U+202E adversarial artifact path. `metadata-chain-runner.py` invokes `subprocess.run(..., text=True)` without an encoding, so input encoding uses Windows' legacy code page. The process raises `UnicodeEncodeError` before the SQL rejection can execute. This reproduced after 68 passing checks, and cleanup succeeded. Evidence: `six-migration-default-encoding-failure.json`.

The failure is in the test harness, not evidence of an accepted unsafe artifact path. Required correction: use `encoding='utf-8'` explicitly for subprocess text input/output in the Windows-supported runners, or document and configure UTF-8 mode consistently. A verification retry uses `python -X utf8 tools/fixtures/m03/qa-metadata-verification.py`; its result is stored separately as `six-migration-validation.json`.

## Prior findings and scope

QA-01 is covered by the new composite tenant/project/source snapshot reference. The independently rerun same-tenant foreign-project snapshot rejection passed before the encoding failure. The old disposable prototype remains historical and unchanged; closure applies to the new migration chain only.

QA-02 now has a generic run identity immutability trigger comparing every field except execution status/completion time. The specific hash-update regression probe passed. QA-01 and QA-02 are resolved for the new six-migration chain; the historical prototype remains unchanged.

## Completed verification outcome

With explicit UTF-8 mode, all 139 checks passed (the engineer's 138 plus one QA hash-mutation rejection). The disposable container was removed. Source inputs are fingerprinted in `six-migration-inputs.json`; raw results are in `six-migration-validation.json`. Approval and Check projections passed the unchanged OpenAPI schemas, scoped runtime privilege tests passed, and the suite exercised source ownership, artifact manifests, concurrent recommendation revisions and revocation blocking export. QA-03 remains open as a reproducibility issue with the documented default Windows invocation.

This is a rerun of the engineer's integration suite plus a QA probe, not a claim that all 138 tests were independently designed or that historical slice counts are additive. Browser API, object-byte verification, actual worker execution, full payload bindings and remaining H01–H04 obligations are outside this completed slice. M0.3 remains open.

