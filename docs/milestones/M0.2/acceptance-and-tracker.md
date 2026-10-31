# Acceptance criteria and milestone tracker

Status: M0.2 review ready; approval pending. Owner: Codex for documentation; user for baseline acceptance. Dependencies: approved M0.1 inventory and received draft documents. Scope: reconcile/design/freeze candidate only.

| Task | Deliverable / acceptance | Result |
|---|---|---|
| M0.2-01 | State source authority, current scope and preserved constraints | README.md, baseline.md |
| M0.2-02 | Explicit resolution for every PC/TC/G finding, preserving evidence holds | reconciliation.md: 30 source IDs |
| M0.2-03 | Decisions include alternatives, selection, consequences and owner/status | decisions.md: M02-D01–D12 |
| M0.2-04 | Name concrete API/data/security amendments, no unrelated product surfaces | contract-amendment.md: CA01–CA08 |
| M0.2-05 | Define measurable acceptance and readiness gates | AC01–AC10 below |
| M0.2-06 | Validate cross-references and original source integrity | validate.py / validation-results.json |
| M0.2-07 | User accepts reconciled baseline | Pending; not inferred from authorization to do M0.2 |

## Planned acceptance evidence

These are requirements for future checks, not executed tests. Map to original T01–T18 and PRD FR/NFRs. Resource bounds below are fixture policy defaults subject to measured adjustment with recorded decision; they are not benchmark claims.

| ID | Coverage | Pass criterion |
|---|---|---|
| AC01 | R01/R02/R05/R06; FR01–03; T01/02/05/06 | Three pinned fixture repos parse offline with inference disabled; no source-script execution, no source mutation, all known routes classified as found/excluded/unknown with source references. Each repeated scan produces same normalized output apart from run IDs/times. |
| AC02 | R09/R10/R16; FR04/05/10; T09/10/16 | Every executable recommendation cites existing source digest/location; unknown auth or sensitivity blocks eligibility; no model finding marked deterministic; all mode/unsupported/none outcomes visible. No egress without valid consent. |
| AC03 | R03/R04/R08; T03/04/08 | Five canonical screen snapshots at 1440×900; no blank graph on nonempty fixture, fit/zoom/filter/node inspector and text matrix agree; dashboard search/status filters and keyboard navigation work. Text labels identify states without color; controls labeled; WCAG AA contrast target checked. |
| AC04 | R11/R12/R16; FR08/09; T11/12/16 | Direct API tests reject stale/cross-plan/revoked approval, changed config/source/policy, unsupported mode and unauthorized actor; concurrent/retried identical requests admit one run; changed body with same key returns 409. |
| AC05 | R13/R16; FR06/08; T13/16 | Generated fixture calls existing mock service, preserves identity/tenant, validates I/O, maps errors; no direct DB bypass; paths reject absolute/traversal/symlink/collision; input repo hashes unchanged. Writes remain disabled. |
| AC06 | R14/R15; FR07/11; T14/15 | Empty/missing/skipped/not_run/failed mandatory checks and changed artifact/policy digest deny approved bundle. Actual command/exit/times/logs persisted for executions. Draft is labeled/audited and cannot change approval. Logs/previews/reports redact fixture secrets. |
| AC07 | R01/R07/R16; T01/07/16 | Restart API/orchestrator after admission and during publication: runs recover without duplicate outputs, immutable artifact digest verified before success; failed upload never yields successful generation. Windows host container fixture proves mount bounds, denied egress and forced timeout cleanup. |
| AC08 | R12/R17; T12/17 | Pin protocol+SDK+runtime+client versions; generated stdio fixture lists and invokes tools using selected compatible client. Revised OpenAPI passes full validator, client generation and semantic negative fixtures; DDL tests prove same-tenant/same-analysis/same-plan constraints. No transport claim based only on labels. |
| AC09 | PRD performance/reliability NFRs | Define fixed fixture commits, machine specification and cold/warm runs. Measure report latency (PRD target <5 min) and compilation/fixture correctness (proposed ≥90%). Record actuals and failures, not synthetic success. Scan input cap initially 10,000 files, 1 MiB/file; exceeding cap gives explicit partial/blocked diagnostics. Worker validation cap initially 2 CPU, 2 GiB, 5 min per check; policy pinned and tested. |
| AC10 | R18; quality/ownership | Source/contract/decision revisions and approvals recorded; no merged/generated production changes, deployment or installation beyond authorized mini-step. Reports identify planned versus executed tests and remaining holds. |

## Next approval gate

Review README, baseline and contract amendment, then approve M0.2 or identify changes. Approval freezes design intent, not functional completion. Proposed next M0.3 produces synchronized OpenAPI/ERD, bootstrap/threat model, exact dependency/protocol pins and environment readiness proof. No application initialization before that check. M0.3 execution and repository writes are not assumed authorized by this M0.2 request.

Current environment limitation: target repository is outside this chat's writable roots. It has been read only. Before repository changes, use it as the chat workspace or otherwise obtain valid environment access; do not bypass denied writes. This does not prevent delivering the present documents in outputs/.
