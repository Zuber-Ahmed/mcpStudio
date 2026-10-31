# mcpStudio

Local-first, application-agnostic MCP Integration Studio.

## Running application

The first four bounded capabilities are live: local session bootstrap, PostgreSQL-backed project registration, read-only Architecture Explorer analysis, evidence-bound MCP candidate review, and exact plan security approval. Generation remains locked.

```powershell
.\tools\Start-MCPStudio.ps1
```

Open `http://127.0.0.1:8080` and use `.local/api/bootstrap-code.txt`. See `docs/planning/ACTUAL-IMPLEMENTATION-STATUS.md` for the product tracker.

## Foundation

- apps/web: Next.js implementation of Dashboard, Project Setup, Architecture Explorer, candidate review and exact-plan approval.
- apps/api: Go local-session, project registry, deterministic source analysis, conservative candidate discovery and exact-plan approval API.
- apps/workers: Python worker metadata for later durable/sandboxed execution; the current bounded analyzer runs in the loopback Go API without executing source code.
- packages/contracts: synchronized HTTP/session contracts and logical data model.
- docs/milestones: preserved M0.1 inventory, M0.2 approved baseline and M0.3 evidence.
- docs/planning/STATUS.md: current status; historical milestone snapshots remain unchanged.

Run `node tools/check-contracts.cjs` for contract-copy integrity and `powershell -NoProfile -File tools/check-prerequisites.ps1` for basic host discovery. These do not prove application functionality or worker sandbox isolation.

Selected application toolchain is Node 26.13.0/npm 11.20.0, Go 1.27.3 and Python 3.14.10. See docs/foundation/version-pins.json for candidate pins and readiness limits. Do not use the host's older toolchain as evidence of runtime compatibility. Required local services and dependency lockfiles are still readiness work; Redis remains deferred.

Supplied PRD and MCPStudio-Technical-Documentation are retained unchanged. Git acquisition, generation, result validation, production deployment and source-repository writes are not implemented yet.
