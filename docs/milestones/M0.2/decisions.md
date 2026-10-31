# M0.2 decision records

Namespace `M02-Dxx` avoids collisions with PRD Appendix B and M0.1 inventory ADR numbers. All records: authored 28 October 2026; owner Codex for proposed resolution, product owner for acceptance; **review candidate, approval pending**. User authorized this reconciliation milestone, not each choice before review. Security decisions require implementation evidence later.

| ID | Conflict / source | Alternatives considered | Selected review baseline | Consequence / acceptance evidence |
|---|---|---|---|---|
| M02-D01 | PC01, PRD CLI-first vs current Studio | CLI MVP; Studio MVP | BL01 five-screen Studio | CLI delivery deferred; all flows trace to five screens |
| M02-D02 | PC02, ADR-009, later HLD | Node/SQLite engine; Go/Python/PostgreSQL Studio; run both | BL04 later Studio stack, Redis deferred | Preserve single state authority; service versions and Compose readiness gate required |
| M02-D03 | PC03/PC06, ADR-002/008 | Universal support; TS-only core; extensible core with bounded initial plugins | BL02/03 source-independent core, three TS fixture analyzers; server+stdio generation first | Unsupported client/both/none outcomes explicit; no automatic fallback |
| M02-D04 | PC04, G07/G10 | Native host execution; container-backed workers; defer Windows | BL05/06 container-backed local target with proof before use | Fixture verifies Windows paths and isolation; missing capability blocks execution |
| M02-D05 | PC05, G06, ADR-005 | Analyze-and-write manifest; read-only snapshot with separate output | BL06/09/10 read-only scan, scoped consent and credential references | No source writes on analysis; secrets/egress tests required |
| M02-D06 | TC04/TC07, G12, ADR-004 | UI-only confirmation; hash-bound immutable plan; mutable plan with carried approval | BL14 immutable versioned approval, backend transaction and idempotency | Stale/replayed/cross-plan approvals rejected; amendment defines hash inputs |
| M02-D07 | TC02/TC06, G14/G15, ADR-006 | Single download; validated only; separate controlled draft and approved bundle | BL14 explicit draft policy and immutable validation binding | Draft cannot masquerade as approved; empty/skipped mandatory checks block approval |
| M02-D08 | G03/G04/G05/G09, ADR-007 | PNG text authority; HTML authority; explicit visual/semantic precedence | BL12/13 visual layout+frontmatter tokens, backend-derived states, secure export semantics | Re-render consistent five-screen reference; functionality proven separately |
| M02-D09 | TC01/TC03/TC05/TC08 | Implement old API with UI mocks; add contracts explicitly | contract-amendment.md before client generation | Recommendation, scope/consent, persistence and resume gaps get concrete mappings |
| M02-D10 | TC07 new tenancy/auth design | No auth; enterprise identity UI; bounded local operator bootstrap | BL05/08 one local operator/workspace, tenant-scoped authorization | Browser session/CSRF/secret design and tests gate exposure; no signup/admin features |
| M02-D11 | PC07 conflicting ADR IDs | Reuse original IDs; namespace new decisions | M02 namespace, source ADRs unchanged | No false original-approval provenance |
| M02-D12 | G02 incomplete roadmap | Invent historical M0.2/M0.3; explicitly agree revised mini-steps | Current authorized M0.2; proposed M0.3 synchronization/readiness | Tracker distinguishes historical examples from newly proposed gates |

Protocol/SDK/toolchain versions are an explicit readiness hold (BL07), not an unrecorded choice. Retention disclosure and operator cleanup must be specified before real-source intake (BL11). These holds cannot be cleared by approval of documents alone.
