# PRD intake and reconciliation addendum

Received 28 October 2026 from `C:/Users/ADMIN/mcpStudio/MCP_Integration_Analyzer_Generator_PRD.pdf`. Preserved byte-for-byte in `sources/`. SHA256: `952F22E67B7EE6BD7BD92483F3A85F297F0010C8DAC3C909F2DE82B94FF6DAD7`.

All 12 pages were text-extracted with pypdf and read. This is PRD v1.0, dated 26 October 2026, explicitly marked **proposed baseline / draft for product and engineering review**. It includes a reference architecture, component boundaries, stack proposal, example data records, workflow states, security model and acceptance tests. It does **not** contain a detailed HLD/LLD, database ERD or HTTP OpenAPI specification. Record examples are not database tables; CLI commands are not HTTP endpoints.

This addendum supersedes earlier statements that the PRD was unavailable. Earlier inventory/validation descriptions describe the first inspection; the repository now contains README.md plus this PDF and .git. Other specifications and Git revision remain unverified. The original 18-row matrix is preliminary; the mapping below links the actual FR identifiers without claiming complete reconciliation.

## Conflicts requiring baseline selection

| ID | PRD evidence | Later Studio baseline / design | Required disposition |
|---|---|---|---|
| PC01 | pp.1–2,10–11: CLI-first MVP; desktop/IDE UI future/P2 | Five-screen Studio is current agreed design | Confirm whether this draft is earlier product scope; retain five screens pending decision, do not switch to CLI-first implementation |
| PC02 | p.6: Node.js/TypeScript engine; local JSON/SQLite; Rust/Go later | Chat describes Go API, Python workers, PostgreSQL, Redis, Temporal, S3-compatible storage | Identify superseding architecture or explicitly reconcile stack; do not initialize either stack yet |
| PC03 | pp.1,4,11: initial TypeScript/Node/Next.js; other languages P2 | Current user requires application-agnostic architecture | Distinguish extensible core from initial supported analyzers; do not promise universal support or silently narrow core model |
| PC04 | pp.4,11: macOS/Linux first, Windows later/verified strategy | Supplied workspace is Windows | Agree Windows runtime/sandbox compatibility before local implementation claims |
| PC05 | pp.4–6: no scan-time repo script execution; generated changes isolated and approved | Setup prototype promises manifest write after analysis; Studio offers direct database adapter example | Specify write consent and service boundaries; prevent direct DB access that bypasses domain authorization |
| PC06 | pp.4,11: client integration P1/expansion; none is valid plan mode (pp.5,9) | Studio exposes server/client/both; none not shown | Define availability/gating for client/both and no-integration outcome; do not implement extra mode as approved scope yet |
| PC07 | p.12: suggested ADR-001–006 meanings differ from inventory ADR-001–009 | Inventory numbers are local tracking IDs | Preserve PDF references as PRD Appendix B ADR suggestions; establish namespace/canonical ADR register before adoption |

Local-first, optional consent-controlled inference, evidence over speculation, read-only defaults, sandboxed validation and explicit approval align strongly across sources. Those remain preserved constraints.

## PRD functional requirement crosswalk

API: **unverified for every FR**; PRD provides CLI workflow and example records, not an OpenAPI contract. Persistence concepts below are logical only; no physical entities/relationships verified. Tests are planned, not executed. Existing R/T references resolve in requirements-traceability.md.

| PRD ID / priority / page | Architecture responsibility / logical data | Screen mapping | Existing inventory linkage | Additional acceptance coverage needed |
|---|---|---|---|---|
| FR-01 P0 p.4 | Scanner / source inventory and ignore policy | S2 | R05,R16; T05,T16 | Explicit root, ignore rules, monorepo detection; zero repo script execution |
| FR-02 P0 p.4 | Scanner/detectors / project graph and evidence | S3 | R02,R08,R09; T02,T08,T09 | Manifest/framework versions, boundaries, auth signals and unknowns |
| FR-03 P0 p.4 | Framework analyzers / routes, exports, service calls | S3 | R02,R08; T02,T08 | Fixture ground truth for Next.js, Express/Fastify, OpenAPI, TS exports; selected support scope pending PC03 |
| FR-04 P0 p.4 | Policy engine / candidate, risk, scope, sensitivity | S3,S4 | R09,R10,R16; T09,T10,T16 | Verify read/write, side effects, sensitivity, schema quality and unknown-policy blocking |
| FR-05 P0 p.4 | Planner/reporter / versioned plan, rationale, topology | S4 | R10; T10 | Server/client/both/none, resources/prompts and excluded candidates; PC06 |
| FR-06 P0 p.4 | Generator/runtime / generated patch and schemas | S4,S5 | R12,R13; T12,T13 | Typed tool I/O, runtime validation, domain service reuse, error mapping and logging hooks |
| FR-07 P0 p.4 | Sandbox runner / validation record | S5 | R14,R15,R16; T14,T15,T16 | Capture actual command, exit code, timestamps, tool version and logs; skipped/not_run never passed |
| FR-08 P0 p.4 | Worktree/filesystem boundary / patch, approval | S5; diff review UI details missing | R13,R16; T13,T16 | Separate destination, collision detection, no overwrite/merge/push/deploy/production mutation without approval |
| FR-09 P1 p.4 | Client connector/policy / server allowlist and tool policy | S4,S5 | R10,R12,R16; T10,T12,T16 | Discovery/invocation, server-side AI runtime, allowlist and identity; PC06 priority unresolved |
| FR-10 P1 p.4 | Optional provider adapter / consent, redaction, evidence | S2,S3,S4 | R06,R09; T06,T09 | Explicit user-controlled egress, cited suggestions treated as untrusted |
| FR-11 P1 p.4 | Reporter / stable finding IDs and reports | S5; report export UI unspecified | R15 partial; T15 partial | JSON plus Markdown/PDF reports and stable IDs; artifact bundle export alone is insufficient |
| FR-12 P2 p.4 | Future extensions / contracts pending | No current screen commitment | R02 only as extensibility constraint | IDE UI, CI mode, marketplace, more languages and multi-repo are deferred; not current implementation authorization |

## Additional PRD requirements and acceptance targets

- p.3/p.12: three reference repositories; 100% recommended-tool source citations; 90% fixture generation correctness and under-five-minute initial report are proposed benchmark targets requiring defined corpus/hardware, not guarantees.
- p.4 NFRs: deterministic/idempotent behavior, graceful partial analysis, actionable errors, incremental scanning/cache, bounded resources, dependency pinning, retention controls, no hidden telemetry and versioned extension interfaces. These need explicit new matrix rows and measurable acceptance thresholds during reconciliation.
- pp.5,7,9–10: reuse existing domain services and user/tenant context; elevated review for writes/admin/financial/bulk export; reject malformed inputs, unauthorized/cross-tenant requests; no production credentials in workers. Add direct negative-test coverage, not just UI checks.
- pp.8–9: CREATED → SCANNED → PLANNED → AWAITING_APPROVAL → GENERATED → VALIDATING → READY_FOR_REVIEW/BLOCKED; failures explicit with retry guidance. Reconcile with design status vocabulary, separate plan approval and validation gates.
- p.11: keyboard workflows, readable contrast, diagram text alternatives, screen-reader labels and non-color statuses require defined five-screen acceptance checks.
- pp.9,12: override reasons, SDK/OS/version support, licensing, output ownership, sandbox/network/dependency-install policy remain decisions requiring owners and approval.

## Validation status and next gate

PDF presence, hash and 12-page text extraction verified. Page 6 was rendered with bundled Poppler and visually inspected to verify the component/stack tables; full-document visual layout validation was not performed. No application/runtime tests ran. The initial 72-check validator remains limited to the original inventory and Stitch sources; it does not validate these PRD requirements or resolve PC01–PC07. PyMuPDF was unavailable (`fitz` missing); Poppler provided the rendering fallback.

M0.1 remains open. Confirm which PRD revision/architecture supersedes conflicts, recover detailed architecture/ERD/OpenAPI if they exist, expand the matrix with NFR/security/accessibility/metrics and exact contract mappings, then seek baseline approval. Do not treat this older draft as permission to replace the current local-first, application-agnostic five-screen Studio decisions.
