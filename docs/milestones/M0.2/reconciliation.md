# Conflict and risk dispositions

Every disposition is a review proposal, not a passing functional test. `Specified` means a concrete resolution exists here; `Readiness hold` requires evidence before affected implementation/use. Source evidence and original IDs remain in M0.1. No critical finding is closed merely by marking its design specified.

| Source ID | Disposition | Resolution / evidence still needed |
|---|---|---|
| PC01 | Specified | BL01 / M02-D01 Studio supersedes CLI delivery; PRD domain requirements retained |
| PC02 | Specified | BL04 / M02-D02 Studio Go/Python/PostgreSQL stack; Redis deferred |
| PC03 | Specified | BL02/03 / M02-D03 agnostic model, bounded initial plugin coverage |
| PC04 | Readiness hold | BL06 Windows container fixture required before real source/validation |
| PC05 | Specified | BL06/10 read-only snapshot, isolated output, service authorization |
| PC06 | Specified | BL02 / CA03 supported server generation; client/both/none visible outcomes |
| PC07 | Specified | M02-D11 new namespace; historical ADRs unchanged |
| TC01 | Specified | CA03 candidate/recommendation/provenance and override model |
| TC02 | Specified | CA06/07 preview, logs, reports and controlled draft route |
| TC03 | Specified | CA02 local revision optional, immutable digest, scan scope/consent |
| TC04 | Specified | CA04/05 canonical immutable plan and artifact-set digest binding |
| TC05 | Specified | CA05 explicit persistence field alignment; JSON schema/DDL synchronization pending |
| TC06 | Specified | CA07 semantic evidence and nonempty mandatory-check policy |
| TC07 | Specified; readiness hold for auth | CA04/08 transactions, idempotency, revocation; BL08 bootstrap/session proof required |
| TC08 | Specified | CA01 recoverable summaries/run listing; CA08 polling and cancellation deferral |
| G01 | Intake resolved; synchronization pending | All document categories available; README authority order and CA01–CA08 resolve drafts without falsifying provenance |
| G02 | Current scope resolved | M02-D12: user authorized this M0.2; next mini-step explicitly proposed, not historical |
| G03 | Specified | BL12/13 and CA01/07 explicit visual/semantic precedence |
| G04 | Specified | CA01 single state vocabulary and real name/source search; UI verification pending |
| G05 | Functional verification open | BL13 graph acceptance AC03; no source prototype repair claimed |
| G06 | Specified | BL06/09/11 and CA02 no scan write, opt-in/disclosures, local retention |
| G07 | Specified; readiness hold | BL05/07/12 local required services/assets; offline fixture proof pending |
| G08 | Specified | BL02/03, CA02/03 versioned capabilities and explicit unknowns |
| G09 | Specified | BL12 frontmatter tokens canonical; licensed local font/icon packaging verified at foundation |
| G10 | Specified; readiness hold | BL06/08/10 sandbox/auth/secret design; Windows and browser proof pending |
| G11 | Specified | CA01/04/08 real lifecycle, durable admission, idempotency; restart tests pending |
| G12 | Specified | BL14 and CA04 backend version/hash authorization; race tests pending |
| G13 | Readiness hold | BL07 exact MCP/SDK/runtime/client version matrix still must be pinned and checked |
| G14 | Specified | CA07 local policy checks and distinct draft; no mandatory production push |
| G15 | Specified | CA06/07 backend-derived evidence/status and real copy behavior; functional tests pending |

## M0.1 ADR transition

Inventory ADR-001/002 preserved by BL01–BL06. ADR-003/007 mapped to M02-D08; ADR-004 to M02-D06; ADR-005 to M02-D05; ADR-006 to M02-D07; ADR-008 to M02-D03 plus BL07 readiness hold; ADR-009 to M02-D02/D04. None becomes an original accepted ADR retroactively. User approval of this M0.2 package would accept the proposed decision direction, while evidence holds remain explicit prerequisites.
