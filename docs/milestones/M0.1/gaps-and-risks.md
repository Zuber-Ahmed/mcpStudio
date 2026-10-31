# Gaps, conflicts and risks

Owners below are proposed roles, not assigned people. All items OPEN. High = blocks baseline acceptance or critical trust-boundary specification; Medium = resolve before corresponding implementation. No missing specification is silently replaced by an assumption.

| ID | Priority / finding | Risk / affected requirements | Proposed owner | Resolution evidence |
|---|---|---|---|---|
| G01 | High: PRD, architecture, ERD, OpenAPI and foundation absent from inspected sources | Invented requirements/contracts/schema; R01–R17 cannot be fully reconciled | Product + architecture + API/data owners | Versioned source files and repo revision; exact mappings and orphan report |
| G02 | High: full agreed roadmap/M0.2 definition unavailable | Scope jump based on older frontend plan; R18 | Product owner | Accepted mini-step text and explicit M0.1 gate decision |
| G03 | High: S5 PNG PASS/download vs HTML blocked/draft; S1 screenshot vs HTML statuses differ | Wrong approval/export behavior and state vocabulary; R03,R14,R15 | Product + design + security | Canonical state machine, refreshed consistent exports and approved screenshots |
| G04 | Medium: dashboard filter data ready/confirmation/generated vs script integrated/pending; search ignores repository | Filters do nothing meaningful; R04 | Frontend/design | Agreed status enum and behavioral test T04 |
| G05 | High: blank explorer PNG; static graph in HTML; only drawer/hover scripts | Core architecture workflow unproven; R08 | Design + frontend | Browser evidence of graph visibility and interaction; T08 later passes |
| G06 | High: zero retention/persistence/training-egress claims lack policy evidence; manifest write claimed | Misleading privacy promise, undefined writes/retention; R05,R06,R16 | Security + product | Data-flow/retention policy, opt-in semantics, source mutation policy and approved copy |
| G07 | High: local-first decision vs CDN fonts/styles/images and optional enterprise inference wording | Offline failure or unintended external dependency; R01,R06 | Architecture + frontend | Offline dependency inventory, packaged assets and inference-off test evidence |
| G08 | High: sample frameworks, adapters and modes are not capability contracts | Application-specific implementation or unsupported selections; R02,R06,R09,R10,R12 | Architecture + analysis owner | Capability/plugin contracts, unknown/unsupported behavior, fixture portfolio |
| G09 | Medium: DESIGN.md frontmatter/prose/HTML palette and radius divergence; missing remote images | Arbitrary redesign or inaccurate visual baseline; R03 | Design owner | Canonical token map and permitted local assets; five-screen review |
| G10 | High: credential, Git URL/local-path, sandbox and source-write rules unspecified | Secret disclosure, unauthorized file/network access or unsafe repo execution; R05,R16 | Security + API owner | Threat model, auth/secret storage boundary, path/URL validation and sandbox acceptance |
| G11 | High: analysis/generation are timers, no run contract or persisted provenance | False completion, retry/replay inconsistencies; R07,R13 | API + orchestration owner | Job lifecycle, idempotency, cancellation/retry and immutable input model |
| G12 | High: mode-change script does not invalidate checks; generation timer unconditionally re-enables button | Approval bypass; R10–R13,R16 | Security + API owner | Versioned approval state machine, atomic authorization/generation rule, T11/T16 |
| G13 | Medium: sample protocol/schema/runtime claims and transport options have no pinned compatibility decision | Invalid config/code generated; R12 | MCP integration owner | Pinned protocol/SDK/schema matrix and supported transports; no sample accepted as spec |
| G14 | High: mandatory orchestration push policy may imply deployment despite local MVP; draft access policy missing | Cloud dependency or export bypass; R14 | Product + security | Define local sandbox alternative, mandatory vs optional checks and draft permissions; no cloud push required by assumption |
| G15 | Medium: same S5 HTML says rate limiter passed and skipped; hardcoded check counts, compliance labels; Copy Config only feedback | Untrustworthy results; R15 | Validation + frontend owner | Single authoritative result model, reconciled fixtures, real clipboard tests |

No original-spec-to-original-spec conflict can be established until G01 is resolved. The conflicts above are observed within the export or between the export and recovered constraints, not assertions about missing documents.
