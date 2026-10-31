# Actual implementation status

Updated 31 October 2026. This is the short product-delivery tracker. Foundation/security evidence remains in `docs/planning/STATUS.md`.

| Slice | Status | Working behavior |
|---|---|---|
| Local application shell | IMPLEMENTED | Go API serves the built Next.js UI on loopback. |
| Local session | IMPLEMENTED — DEVELOPMENT | One-use 256-bit bootstrap, exact origin, HttpOnly SameSite=Strict cookie, idle/absolute expiry, CSRF and logout. Bootstrap currently uses an ACL-inherited local file; OS credential-store integration remains before release. |
| Dashboard | IMPLEMENTED | Loads and searches real projects from PostgreSQL; no fabricated metrics. |
| Project Setup | IMPLEMENTED — REGISTRATION | Creates local/Git project metadata with contract validation and tenant-scoped database functions. Local sources can proceed to analysis; Git acquisition remains inactive. |
| Architecture Explorer | IMPLEMENTED — LOCAL TYPESCRIPT/NEXT | Resolves the registered canonical root, rejects links/escapes, applies file budgets, creates immutable digests, deterministically detects modules/imports/Next routes, persists graph evidence and renders it. Repository scripts are never executed. |
| MCP Studio | IMPLEMENTED — REVIEW + EXACT APPROVAL BOUNDARY | Discovers syntax-backed routes as review-only candidates. Route names do not confer authorization, sensitivity or domain mapping. Exact-plan construction rejects unresolved and legacy analyzer/detector evidence; approval remains available only for a separately verified mapped candidate. Generation remains unavailable. |
| Results & Validation | NOT STARTED | No mock pass/download state. |

## Run locally

From PowerShell in the repository:

```powershell
.\tools\Start-MCPStudio.ps1
```

Open `http://127.0.0.1:8080`, then paste the one-time code stored at `.local/api/bootstrap-code.txt`.

## Next implementation slice

Independent QA re-review of analyzer/discovery v2, followed by an explicit verified domain-mapping/adjudication workflow. Isolated generation remains behind both gates and must not begin from path-name inference.

## Current boundaries

- Architecture analysis supports registered local folders only; Git acquisition is not represented as implemented.
- Supported snapshot files are TypeScript, JavaScript and JSON. `.git`, dependency, build and coverage directories are ignored.
- Each file is limited to 2 MiB; a snapshot is limited to 5,000 files and 25 MiB.
- Symbolic links, junction escapes and non-regular files fail closed. No repository command or package script is executed.
- Candidate discovery treats all reads as unknown and writes as blocked pending domain, authorization, sensitivity and schema review. Health/status names are not authority.
- Comment and string contents are masked before route-export matching. `src/app` and route-group URL conventions are normalized; `.local` and configured root `.gitignore` exclusions are applied before source reads.
- Analyzer v1 and candidate-detector v1 evidence cannot enter a new plan. Existing historical records remain retained but are not executable authority.
- Approval requires the exact current plan version and SHA-256 hash plus an explicit security confirmation. A mismatched hash is rejected.
- Approval does not trigger generation; `/v1/generations` is intentionally absent.
