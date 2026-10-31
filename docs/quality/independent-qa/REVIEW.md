# Independent QA review

Date: 29 October 2026 (Asia/Calcutta). Verdict: **HOLD / partial foundation verification**.

Reviewed the Software Engineer chat `01a1836a-65f6-7100-8791-c067e0416b78`, current workspace contracts, approved M0.2 baseline, scaffold, fixture code, and M0.3 evidence. This is a working-tree review: there is no isolated implementation commit to compare, and most delivered files are untracked. No product code was changed during QA.

## Reproduced findings

### QA-01 — P2: Analysis can reference a different project's snapshot

Location: `tools/fixtures/m03/database-fixture.sql`, lines 24–26.

The analysis table independently validates `(tenant_id,project_id)` and `(tenant_id,snapshot_id)`. It does not verify that the snapshot belongs to the analysis's project. In a disposable database, inserting another project under tenant 1 and inserting an analysis for that project using snapshot 20 (owned by project 10) both succeeded. This permits incorrect source provenance even when tenant keys match.

Required correction: bind analysis tenant/project/snapshot together through an appropriate composite key or equivalent transactional enforcement. Add both same-project acceptance and same-tenant/different-project rejection tests. Carry this into the physical schema under H01.

### QA-02 — P2: Updates bypass generation approval admission

Location: `tools/fixtures/m03/database-fixture.sql`, generation table and trigger (lines 48–64).

`generation_admission` runs only BEFORE INSERT. After the valid generation 90 is inserted, `UPDATE generation SET plan_hash=repeat('f',64) WHERE id=ident(90)` succeeds. The generation no longer matches the hash approved by approval 80, while retaining its linked validation. Insert-only rejection tests miss this mutation route.

Required correction: make approval-bound generation fields immutable, or validate relevant updates transactionally with appropriate privileges and concurrency tests. Keep mutable execution status separate from immutable admission identity. Add negative update tests under H01. This probe uses the fixture's database role; no product role or service enforcement exists yet.

Both issues are **prototype gaps**, not demonstrated vulnerabilities in a deployed application. The engineer already records incomplete physical semantics under H01; these findings make two missing cases concrete.

## Independently executed checks

| Area | Result and limits |
|---|---|
| Contract integrity | Six manifest hashes match; 24 resource operations and three session operations |
| OpenAPI | Both documents pass full meta-schema validation; all 22 selected instance fixtures agree with expectations (24 check entries total) |
| Client | Strict TypeScript compilation passes using project Node and existing isolated tooling; no HTTP runtime tested |
| Canonicalization | All 11 selected checks pass; nine cover both libraries, unsafe integer and unpaired surrogate rejection are Python-only |
| Database | Original 22 checks pass in a fresh digest-pinned PostgreSQL container; two additional rejection probes fail as described above |
| Services | Running PostgreSQL reports healthy; Temporal is published at 127.0.0.1:7233 and storage at 127.0.0.1:8333; PostgreSQL has no host-published port |
| Cleanup | QA container removed; probe transactions rolled back; existing service stack untouched |

Raw database evidence: `database-probes.json`. Reproduce with Python 3: `python tools/fixtures/m03/independent-qa.py` from the repository root with Docker access. This harness uses the pinned database image already available locally, creates only a unique network-disabled container, and exits nonzero while either rejection probe fails. Container absence is checked after cleanup.

Contract/JCS validation commands regenerated their existing evidence files. No readiness index was regenerated; the independent observations above do not rely on historical report hashes.

## Coverage and acceptance limits

| Requested area | QA disposition |
|---|---|
| Designs | Five source design exports and reconciled token/workflow requirements are present. Web workspace contains only metadata and README. Visual fidelity, responsive behavior, accessibility, navigation and interaction acceptance cannot be executed yet. |
| API contracts | Structural validation and client typechecking pass. No API handlers exist; status codes, ownership, bootstrap, cookies, exact-origin handling, CSRF, logout and expiry have no live enforcement proof. |
| Database | Logical model has 23 entities and DB01–DB10 requirements. Executable SQL is a disposable subset, not application migrations. Provenance and update gaps above, concurrency, consent, idempotent effects and remaining constraints block physical-schema acceptance. |
| Development | API module metadata, reserved web workspace, worker metadata/locks and contract factories exist. Analyzer, generator, application workflows and five-screen end-to-end flow are pending. |
| Infrastructure | Port bindings checked independently. Existing MCP, worker boundary/resource, service persistence and dependency reports were reviewed; their full suites were not rerun in this review. No new dependency advisory scan was performed. |

Keep M0.3 open. Existing H01–H04 remain valid: physical schema/transactions, browser session enforcement, application path/cancellation/recovery, and full dependency/image-layer review. Product functionality is **not ready for QA sign-off**. Passing fixture counts do not establish application functionality. Fix and retest QA-01/QA-02 as part of H01, then verify each remaining hold at its stated implementation boundary.
