# Current project status

## Product delivery status — Exact plan approval slice

Updated 31 October 2026. The application is running locally at `http://127.0.0.1:8080`.

- WORKING: one-use local bootstrap, HttpOnly session cookie, exact-origin/CSRF checks and logout.
- WORKING: Next.js Dashboard and Project Setup served by the Go API.
- WORKING: PostgreSQL-backed project create, list/search and detail through tenant-scoped functions.
- WORKING: read-only canonical local-root acquisition, immutable snapshot digest, deterministic TypeScript/Next.js module/import/route analysis, persisted graph evidence and Architecture Explorer rendering.
- WORKING: evidence-bound MCP route candidate discovery with read/write, sensitivity and eligibility classification, versioned recommendation storage and a generation-locked review UI.
- WORKING: immutable exact-plan construction bound to snapshot, analysis, supported recommendation, selected candidates, generator/configuration metadata and validation policy; explicit approval is bound to the current version and SHA-256 plan hash.
- REMEDIATED — AWAITING INDEPENDENT QA SIGN-OFF: analyzer/discovery v2 excludes comment/string route text, normalizes `src/app` and route groups, excludes `.local` and bounded root `.gitignore` matches, removes path-name authorization/domain inference, and rejects legacy evidence at plan construction. The supplied five independent QA assertions now pass in the engineer rerun; QA's original HOLD remains authoritative until QA re-reviews the changed fingerprints.
- VERIFIED: Go tests, TypeScript and production build pass; migrations 001-013 apply in an isolated database; live bootstrap → analysis → discovery → plan → mismatched-hash rejection → approval → readback → logout passes.
- NEXT: independent QA re-review, then a verified domain-mapping/adjudication workflow. Isolated generation remains locked behind those gates.
- NOT STARTED: generation and Results & Validation product flows.

The concise tracker is `docs/planning/ACTUAL-IMPLEMENTATION-STATUS.md`. The remainder of this file preserves foundation/readiness history. H04 findings remain release work; they no longer prevent development of bounded local application slices.

Updated 30 October 2026, Asia/Calcutta. This file supersedes historical milestone status snapshots.

## Current gate summary — minimal candidate restart and High advisory review completed

Updated 30 October 2026, Asia/Calcutta. Field coverage remains complete (23 entities, zero unmapped); SCHEMA-D01 is closed. Latest schema fixture: 118 checks across migrations 001–009.

The runtime review completed: two npm fixture locks, 31 explicit Python versions and selected Node/Go advisory checks returned no advisories; 16 lock/wheel integrity entries passed. All eight exact local images were scanned and reported high/critical OS, embedded-Go or pip-vendored advisories. Unsuppressed findings and applicability notes are in docs/foundation/RUNTIME-DEPENDENCY-REVIEW.md and docs/quality/runtime-audit/assessment.json.

M0.3 remains OPEN: H01 integrated schema/execution semantics; H02 browser bootstrap/session; H03 actual acquisition/path/worker recovery; H04 unresolved image findings/final adoption coverage. No risk acceptance, adopted pin change or later milestone. Next foundation task: patched runtime-image candidate evaluation, rescans and affected readiness regression checks.

Python tooling-free candidate evaluation: two isolated images preserve all application dependency versions, remove pip/ensurepip/wheel bundles, and pass 59 runtime/boundary/service check entries. Unsuppressed scans using the same database drop each image from 172 to 164 findings, with zero language-package findings but 44 High OS findings remaining. Neither candidate is adopted; service restart/persistence regression remains pending for final replacements. See docs/foundation/PYTHON-RUNTIME-CANDIDATES.md. Next: evaluate patched OS/base-image candidates and embedded-Go/Alpine remediation, then combined-image rescans and affected readiness regressions.

Python OS evaluation completed: official same-version Trixie refresh is unchanged; repository upgrade changes only tzdata and retains 164 findings (44 High). Bookworm candidate reports 243 findings (59 High). Both candidates pass 50 combined runtime/boundary checks. Neither is adopted. See docs/foundation/PYTHON-OS-CANDIDATES.md. Next: package/binary applicability and minimal-runtime design for remaining Python OS findings, plus separate PostgreSQL/embedded-Go/Alpine remediation.

Worker path review maps 164 findings across 40 installed packages; 44 High entries correspond to 8 advisories. Eleven fixture checks pass; 85 native dependency queries expose one existing Tkinter/Tcl/Tk gap (84 resolve). Required libuuid is loaded, so source-package-wide removal is unsuitable. Proposed minimal-runtime design excludes administrative tooling while preserving verified libraries and provenance; no image adoption or waiver. Next: isolated minimal-runtime build and dependency/tool-absence/TLS/DNS/service validation. See docs/foundation/WORKER-MINIMAL-RUNTIME-DESIGN.md.

Minimal worker/service candidate built: 50 checks pass, 82 retained Python native libraries load, original application pins preserved. Controlled TLS, CA, DNS/NSS, locale/timezone and actual Temporal/S3 tests pass. OS scan coverage is verified (87 original Debian records, 14 Python distributions); 164 findings remain conservatively visible, including 44 High. No adoption or waiver; service restart regression remains pending. See docs/foundation/MINIMAL-RUNTIME-CANDIDATE.md. Next: final-file advisory applicability and isolated restart/persistence evidence before adoption.

Minimal candidate restart review: 11 service and 7 isolation/restart/cleanup checks pass in an internal-only disposable stack; original stack snapshots unchanged and temporary credentials/resources removed. Eight High advisories (44 raw rows) have scoped affected-component exclusion evidence on the exact final candidate. The other 120 rows and separate server/image findings remain open; no adoption, suppression or waiver. Next: remaining advisory review and PostgreSQL/embedded-Go/Alpine remediation. See docs/foundation/MINIMAL-RUNTIME-RESTART-REVIEW.md.

Progress notes below describe their original stages; this summary and the latest evidence index are authoritative.

## Approved and delivered

- M0.1 requirements/design inventory and M0.2 reconciliation baseline: user approved.
- Foundation scaffold installed in C:/Users/ADMIN/mcpStudio; supplied PRD/technical documents preserved.
- Full OpenAPI meta-schema validation and 22 instance fixtures passed; API client declarations and factories generated and typechecked.
- Eleven selected cross-language canonicalization checks passed.
- Project Node 26.13.0/npm 11.20.0, Go 1.27.3 and Docker/Compose verified. Trusted no-network/read-only container smoke fixture passed.
- PostgreSQL 17.11 disposable constraint prototype: 22 checks passed, container removed. This is not the application's production schema.
- Official MCP client/server 2.4.0 stdio fixture: 8 checks passed, explicitly pinned to protocol 2026-07-28. Fixture audit clean after patched Zod pin; not product authorization proof.
- Worker runtime: Python 3.14.10 Linux image, Temporal SDK 1.35.0 and TypeScript parser packages verified. Seven wheel hashes checked against PyPI; 11 runtime/parser/sandbox-preparation checks passed. Lockfile and image digest recorded.

- Local workflow/storage services: 11 check entries passed, including Temporal activity execution, authenticated S3 round trip, invalid credentials denied, restart persistence and unique fixture cleanup. Digest-pinned services remain running with verified localhost bindings. See docs/foundation/LOCAL-SERVICES.md and docs/quality/local-service-validation.json.

## Final readiness review

Final review completed: 14 additional Docker boundary/resource/deadline checks passed. OpenAPI/JCS/client typecheck and source hash checks passed again. OSV returned no advisories for 31 unique exact Python package versions at query time.

M0.3 remains OPEN with four explicit holds: full physical-schema/concurrency/consent proof (H01), browser bootstrap/session enforcement (H02), application path/cancellation/recovery enforcement (H03), and complete dependency/image-layer review (H04). See docs/foundation/M0.3-READINESS-REVIEW.md and docs/quality/final-readiness-review.json. Earlier environment blockers are resolved; no remaining hold is represented as a passing fixture or silently deferred.

Next: close the physical-schema/transaction-test and dependency review holds within foundation scope. Any implementation needed for H02/H03 must have its scope/gate reconciled before progressing to product functionality. No new milestone has started.

No product screens, API implementations, application analyzers, generated production adapters, deployment, commit or push performed. Local-first, five-screen Studio and application-agnostic core decisions remain preserved. Inspect docs/quality reports for the exact scope of each passing check.

## Physical admission implementation update

Foundation admission migration and independent-session transaction suite implemented: 39 checks passed, disposable database removed. See docs/foundation/ADMISSION-KERNEL.md. This closes the absence of concurrency/consent admission evidence, but H01 remains open for the complete physical schema, immutable payload/policy/candidate binding, validation/audit constraints and runtime integration. No running service database was migrated. Plan/policy/candidate and validation/audit slice is now implemented; see the subsequent update below.

## Physical binding/validation implementation update

Migration 002 and its combined 001+002 suite passed 59 checks, including export/revocation concurrency and transactional audit retention. See docs/foundation/BOUND-VALIDATION.md. H01 remains partially open for full physical mapping, canonical publisher/worker/object integration and least-privilege runtime roles. Backend/worker privilege boundaries and model mapping are now delivered; see the subsequent update. Local-first/application-agnostic decisions and the five approved screens are unchanged; no product API is exposed.

## Runtime database roles and physical-model mapping

Migration 003 introduces scoped backend/worker wrappers and non-login ownership. 56 real-login privilege/integration checks passed; fixture removed. Every field across 23 logical entities is mapped or explicitly missing using the actual migrated catalog; 7 entities are absent and all implemented resources remain partial. See docs/foundation/RUNTIME-DATABASE-ROLES.md and PHYSICAL-MODEL-MAPPING.md. H01 remains open for missing schema and integration; H02/H03/H04 unchanged. Source snapshot, graph and recommendation ownership chain is now delivered; representation reconciliation remains explicit in the updated mapping.

## Source/graph/recommendation ownership update

Migration 004 and the four-migration integration suite passed 48 checks; disposable fixture removed. Immutable snapshot identity, same-analysis graph/candidate links, versioned recommendations and plan references are enforced, including a real-role guarded export-record smoke test. See docs/foundation/SOURCE-GRAPH-OWNERSHIP.md. All 23 entities are mapped; absent resources now: ARTIFACT, FINDING, PLAN_REVOCATION. H01 and M0.3 remain open. Artifact manifest/path, findings and explicit revocation slice is now delivered; see the subsequent update.

## Artifact/finding/plan-revocation update

Migration 005 and the current five-migration suite passed 101 checks; disposable fixture removed. Exact artifact manifest binding, portable relative paths/case collisions, same-generation finding links and explicit plan revocation are enforced. All 23 logical entities have physical representations, with remaining field/type/semantic gaps still explicit. See docs/foundation/ARTIFACTS-FINDINGS-REVOCATION.md. M0.3 remains open. Identity/approval/durable metadata and scoped Check/Approval contract validation are now delivered; remaining payload/version and integration gaps are tracked below.

## Identity/approval/durable metadata update

Migration 006 and the six-migration suite passed 138 checks, including validation of actual Approval and queued/executed Check documents against unchanged OpenAPI. UUID audit/check identities, explicit approval intent, generation hashes, predecessor scopes and durable idempotency/outbox metadata are implemented. See docs/foundation/IDENTITY-APPROVAL-METADATA.md. 33 declared fields remain unmapped, with further type/semantic gaps explicit. M0.3 stays open. Immutable full payload and opaque policy version bindings are now delivered; remaining metadata and runtime holds are tracked below.

## Executable payload and policy-label update

Migration 007 and the focused seven-migration suite passed 59 checks. Full CanonicalPlan/Candidate/Plan/PolicyReference documents validate against unchanged OpenAPI; exact opaque policy labels and configuration/plugin/schema/generator approval bindings are tested. See docs/foundation/EXECUTABLE-PAYLOADS.md. 7 dictionary fields remain unmapped, with semantic/runtime controls still explicitly open. Principal/project metadata and the field-inventory acceptance review are now delivered; see the current gate summary. M0.3 remains open.
