# Input and design inventory

## Source register

| ID | Input | Inspection result | Authority and limitation |
|---|---|---|---|
| U1 | Current user request, 28 October 2026 | Read | M0.1 scope; preserve local-first and application-agnostic decisions |
| C1 | MCPStudio conversation `6adf8000-7004-83ed-b840-4aee7adb5739` | Five turns retrieved; no older cursor | Historical requirements and proposed stack; not source specifications |
| Z1 | final_mcp_studio_workspace.zip | Recovered from attachment path, copied and extracted | Five HTML + five PNG + one DESIGN.md; exact source archived |
| P1 | PRD PDF v1.0, dated 26 October 2026 | Added to supplied repository; all 12 pages text-extracted and read | Document labels itself proposed baseline/draft. CLI/TypeScript MVP and Node/local persistence conflict with later Studio narrative; see prd-intake.md. |
| A1 | HLD/LLD and original ADRs | New HLD/LLD drafts received in technical-documentation/docs | Original accepted ADRs still unavailable; inspect technical-intake.md for current reconciliation |
| D1 | Database ERD/schema/migrations | New Mermaid logical ERD and narrative received: 14 entities | Draft only; no executable schema/migrations or constraint verification |
| O1 | OpenAPI document | New OpenAPI 3.0.3 draft received: 15 operations, 23 schemas | Exact draft links recorded in technical-intake.md; not approved or implemented |
| F1 | Existing application foundation | User supplied `C:/Users/ADMIN/mcpStudio`; working folder inspected: only README.md and .git | README contains only `# mcpStudio`; no application/spec files found. Git commands denied by environment, so revision/history/branches unverified. See repository-inspection.md. |
| R1 | Agreed full mini-step roadmap | Only partial prose recovered | M0.1 explicit; M0.3 example and older M1–M5 proposals are not an accepted complete roadmap |

Discovery: initial task directory held only empty `outputs/` and `work/`. Filename searches under `C:/Users/ADMIN/Documents/Codex` found no pre-existing MCP/Stitch/PRD/OpenAPI candidates or AGENTS.md. A later manifest search found no package.json, go.mod, pyproject.toml, ERD or OpenAPI foundation candidates. `list_projects` returned an empty project list. Connected Drive searches for `MCP` and `Integration Studio` returned no relevant project inputs; unrelated results were not read. This is a bounded availability finding, not a claim that files do not exist elsewhere on the computer or account.

Conversation anchors (agent message IDs):

- C1.scope: `ecf760d1-f32b-4ff4-98f4-eedd5eee5eba` — M0.1 and approval before M0.2.
- C1.plan: `7e698c70-06bb-4882-ab44-48fe50e8cc2d` — traceability, tasks, evidence and milestone gates.
- C1.stack: `9095aeb7-8bc7-4be5-9484-d2fedd1beeb6` — proposed frontend stack, retained backend stack and principles.
- C1.review: `de51c90b-591b-429c-bfa2-53e5dfedd9dd` — visual baseline with graph and approval conditions still open.

## Five-screen register

Paths below are relative to `sources/stitch/`. All five supplied PNGs were visually inspected; all HTML scripts and visible text were statically inspected. No browser interaction was executed.

| ID | Screen / directory | Verified design content | Functional or consistency gap |
|---|---|---|---|
| S1 | Dashboard / dashboard | Project table, search, filters, New Project, sidebar | PNG has Integrated/Adapter Required; HTML has Ready for Review/Needs Confirmation/Adapter Generated. Script branches only on integrated/pending; search reads name only despite repository-search placeholder. Row click highlights without navigation. |
| S2 | Project Setup / project_setup | Git/local source, revision, password token input, advanced scope, processing explanation | Analyze uses a 1200ms timer only. No real validation/import/worker. Privacy claims and `.mcp/manifest.json` source write need specification. |
| S3 | Architecture Explorer / architecture_explorer | PNG has blank graph area; HTML contains positioned nodes, SVG edges, provenance labels, layer and zoom/fit controls, inspector | Script handles drawer toggle and target hover only. No implemented zoom, fit, filtering, matrix switching or node-click inspection found. Initial collapsed drawer disagrees with `isCollapsed=false`. Runtime graph visibility remains unverified. |
| S4 | MCP Studio / mcp_studio | Recommendation/rationale, server/client/both modes, two security checkboxes, adapter config, transport and collapsed JSON preview | `setMode` changes styling and preview only; no confirmation invalidation. `triggerGenerate` uses a 700ms timer and re-enables button; no approval/version/authorization check. No backend contract. |
| S5 | Results & Validation / results_validation | HTML distinguishes approved export lock, draft download, per-artifact status and skipped mandatory checks | PNG instead shows BUILD PASS and Download Bundle. Static HTML reports conflicting rate-limit outcomes. Preview files are hardcoded; download/gate enforcement not implemented. Copy Config changes feedback without clipboard write. |

## Shared visual/system inventory

DESIGN.md specifies Geist/Inter/JetBrains Mono, compact panes, hairline dividers and blue primary action. Its frontmatter uses blue-tinted surfaces and primary `#004ac6`; prose specifies neutral surfaces and primary `#2563eb`. Radius values also differ between frontmatter, prose and HTML. Preserve the five-screen structure; select canonical tokens only after conflict resolution.

HTML depends on Google Fonts, Tailwind CDN and remote image URLs. Supplied PNGs show missing logo/profile imagery and typography inconsistencies. An offline local build must package permitted assets and styles; current export does not prove offline readiness.

Examples such as Express, FastAPI, PostgreSQL, Claude, customer endpoints and TypeScript adapters are sample content, not a supported-application whitelist or Studio schema. No extra Settings screen or command palette is added to the five-screen baseline solely because navigation/design prose mentions it.
