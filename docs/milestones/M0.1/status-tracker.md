# Milestone and task tracker

## Current approval record

Latest: M0.2 approved and M0.3 authorized. User subsequently chose contract files only for now. See ../M0.3/STATUS.md for current contract delivery and deferred readiness obligations; historical statements below do not override that record.

M0.2 update: user authorized **Baseline Reconciliation and Decision Freeze** with `ok procced`. Review candidate delivered in ../M0.2/README.md; acceptance pending. No later implementation or target-repository writes performed.

**M0.1 inventory approved by user**, recorded 28 October 2026 (Asia/Calcutta), following the technical intake review. Evidence: user message `approved`. This record supersedes historical approval/status statements below.

Approval accepts the inventory and findings; it does not resolve each draft conflict, prove runtime functionality or select a stack. All requested document categories are now available. The technical crosswalk maps R01–R18 to draft operations/entities; 72 original integrity checks and 128 technical structural checks passed. No runtime tests ran.

PC01–PC07, TC01–TC08, unresolved design gaps and pending ADRs remain open follow-ups. Local-first, application-agnostic architecture and the five-screen baseline remain preserved. No later milestone work has started and no repository files were modified.

**Next gate:** recover or agree the M0.2 mini-step definition and acceptance criteria. If the original is unavailable, proposed scope is baseline reconciliation and decision freeze. That proposal is not a recovered agreement or authorization to initialize tooling.

## Historical inventory status

Overall: **M0.1 inventory available for review; acceptance blocked.** Updated 28 October 2026, Asia/Calcutta. Product approval: **not received**. No later milestone work started.

Latest technical intake: HLD/LLD, logical ERD and OpenAPI are now present as newly authored review drafts. See technical-intake.md for exact R01–R18 operation/entity crosswalk, TC01–TC08 and independent validation. The older missing-input task entries below are historical: M0.1-03 now awaits baseline authority/conflict review, and M0.1-04 has concrete draft links but incomplete contract coverage. No document approval inferred from receipt.

Latest intake: PRD PDF now recovered and read (12 pages). See prd-intake.md for FR-01–FR-12 mapping and PC01–PC07 conflicts. PRD is draft/CLI-first and does not include detailed HLD/LLD, ERD or OpenAPI. Task 03 is partially unblocked; task 04 still needs full reconciliation. Earlier repository inspection describes the folder before the PDF was added.

Statuses: Not started → In progress → Review ready → Approved. Blocked requires a named dependency; file generation alone never means Approved. Owner labels are proposed roles except Codex work performed here.

| Task | Owner | Dependency | Acceptance criterion | Status / evidence |
|---|---|---|---|---|
| M0.1-01 Recover scope and available inputs | Codex | U1/C1 | Source provenance and discovery boundary recorded | Review ready: inventory.md, archived conversation and ZIP |
| M0.1-02 Inspect final five-screen export | Codex | Z1 | All PNG/HTML/design files examined; inconsistencies identified | Review ready: inventory.md, G03–G15 |
| M0.1-03 Reconcile authoritative specifications/foundation | Product + technical owners | G01 | PRD/HLD/LLD/ERD/OpenAPI/repo revisions verified | Blocked: supplied repository working folder has only README.md; Git access denied; specifications not recovered. See repository-inspection.md. |
| M0.1-04 Build requirements traceability | Codex + technical owners | 01,02; final acceptance needs 03 | Requirements map to exact components/endpoints/entities/screens/tests, or explicit justified N/A | Partial: 18 evidence-based rows; exact API/entity mappings blocked by G01 |
| M0.1-05 Inventory decisions and risks | Codex; decisions by owners | 01,02 | Stable gap/ADR IDs, impact and resolution criteria | Review ready: decisions.md, gaps-and-risks.md; decisions unresolved |
| M0.1-06 Validate inventory package | Codex | 01,02,04,05 | Artifact integrity, screen count, cross-reference coverage and limitations recorded | Review ready: validation.md and validation-results.json |
| M0.1-07 Reconcile conflicts and sign off M0.1 | Product/design/security/architecture owners | 03–06, G02–G15 | Canonical sources, exact traceability, resolved critical gaps, accepted residual risks, explicit user approval | Blocked; approval not requested as if baseline were complete |
| M0.2 | Unassigned | 07 plus recovered M0.2 definition | To be taken from accepted roadmap | Not started; locked |

## Gate checklist

- [x] Preserve M0.1-only boundary and both user architectural constraints.
- [x] Archive available evidence and inspect all five screen exports.
- [x] Produce matrix, decision inventory, gap/risk register and tracker.
- [x] Validate document structure and source integrity; record static findings.
- [ ] Receive and pin P1/A1/D1/O1/F1 (or explicit owner disposition for an intentionally nonexistent foundation).
- [ ] Reconcile every PRD requirement and reverse-map every API operation/entity; replace TBD cells.
- [ ] Resolve canonical screen/state/token conflicts and security/privacy/gate definitions; obtain graph evidence or agree how its pending verification affects acceptance.
- [ ] Recover accepted M0.2 scope and approve M0.1 baseline explicitly.

Next intake needed: authoritative spec files or links, repository folder/remote plus intended revision, accepted mini-step roadmap, and identification of the canonical Stitch representation where PNG and HTML disagree. This requests missing inputs; it does not request permission to start later work.
