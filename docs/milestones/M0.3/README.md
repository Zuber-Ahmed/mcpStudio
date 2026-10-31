# M0.3 — Contract Synchronization and Foundation Readiness

Authorized after user approved M0.2 and requested proceeding further. Recorded 28 October 2026, Asia/Calcutta. **Contract artifacts produced; readiness gate remains open.** No application initialized and no target-repository files modified.

Latest user direction: **continue with contract files only for now**. Installation, local service startup and repository initialization are deferred at the user's preference. The contract work below is delivered; deferred readiness obligations remain in this same milestone and are not converted to passing results.

## Concrete artifacts

- specs/openapi.yaml: synchronized 0.2.0-review resource API, 24 operations and 43 schemas; original 15 operationIds retained.
- specs/bootstrap.openapi.yaml: separate 3-operation local-session exchange/read/logout contract with exact-origin, nonce and CSRF rules; no implemented login claim.
- specs/database-erd.mmd and specs/data-dictionary.json: 23 logical entities, 32 relationships, 10 physical/transaction constraint requirements; not applied migrations.
- semantic-rules.md: cross-resource approval/export rules, bootstrap/session design, sandbox boundary and pinned canonicalization algorithm.
- threat-model.md and contract-traceability.md: trust-boundary controls, verification obligations and amendment-to-artifact mapping.
- operation-inventory.json: exact operation inventory for generated-client/coverage work.
- version-pins.json: source-verified exact candidate pins and explicit unresolved dependency/image entries; not a tested lockfile.
- validation-results.json and contract-fixtures.json: structural and positive/negative contract-design evidence; no live API/database/MCP proof.
- preflight.ps1 / preflight-results.json: repeatable read-only host prerequisite discovery.
- build_contracts.py: reproducibly writes amended contracts from preserved source drafts; never modifies evidence.

## Current readiness outcome

Docker is not available in PATH or the conventional Docker Desktop executable location checked. Go and PostgreSQL CLI are absent from PATH. WSL executable is present but distribution/engine/sandbox behavior has not been proven. Installed Node observed as 25.2.1, which differs from selected 26.13.0. Bundled Python 3.12.14 was used for authoring/checks, not claimed as selected worker runtime. No services were started and no production/source repositories were executed.

Downloading the full OpenAPI validator/canonicalizer into the scratch folder failed with DNS resolution errors for pypi.org; the environment disables sandbox approval prompts. No alternate install path was used to bypass that restriction. Consequently full OpenAPI meta-schema validation, generated client typechecking, full RFC 8785 library tests, database constraint execution and MCP interoperability remain **not run**. The local checker is explicitly limited; its passing result cannot clear these holds.

The supplied repository is outside this chat's writable roots. Current artifacts are reviewable in outputs/M0.3. Open `C:/Users/ADMIN/mcpStudio` as the project workspace before repository writes. User approval of this milestone does not change environment permissions.

## Remaining gate — concrete prerequisites

1. Enable a working Linux container engine/Compose on the Windows host and expose its executable; prove denied egress, bounded mounts/resources and timeout cleanup using a fixture.
2. Use the supplied repository as the writable project workspace. Preserve existing docs/history; no destructive initialization.
3. Permit ordinary dependency resolution in the proper workspace; retrieve full validator/client generator/canonicalizer, create immutable lockfiles and resolve container image digests.
4. Run full contract/schema validation, client generation/typecheck, JCS vectors, DDL negative constraints and MCP stdio discovery/invocation against pinned versions. Execute host bootstrap exchange/session security tests before browser exposure.

The contract-design portion is ready for review; M0.3 is **not complete** while these required checks remain open. Continue this same milestone when prerequisites are available. Do not request a new milestone approval to bypass missing evidence.

## Reproduction

Use a Python 3 runtime: `python build_contracts.py`, then `python validate.py`. This validates contract design with the limited local checker. `preflight.ps1` records host tooling only, not sandbox proof. Full validator/client commands must be pinned and recorded once dependency retrieval is available; they have not been represented by placeholder successes.

Source verification links and exact choices are in version-pins.json. Versions were selected from official project release/package metadata; suitability/security and combined compatibility remain test obligations. The selected stdio framing is defined in the [official MCP specification](https://modelcontextprotocol.io/specification/2026-07-28/basic/transports/stdio); canonicalization refers to [RFC 8785](https://www.rfc-editor.org/rfc/rfc8785). No dependency is loaded from a source-repository README or model-generated shell instruction.
