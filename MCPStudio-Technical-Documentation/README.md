# MCP Integration Studio - technical documentation
Prepared 28 October 2026. Review edition 0.1.

Start with MCPStudio-Technical-Documentation.pdf, then docs/01-Architecture-HLD.md and docs/02-LLD.md. Editable database and HTTP contracts are in specs/database-erd.mmd and specs/openapi.yaml. The PDF includes a readable ERD relationship list and complete HTTP operation/schema reference; the editable files are authoritative for this newly proposed contract.

## Status and provenance
No original openapi.yaml or database-erd.mmd was recovered. These filenames in specs/ contain NEW DRAFTS, not recovered or approved specifications. HLD, LLD, database design and HTTP contract are newly authored proposals grounded in available conversation and inventory evidence. They are not proof of implementation or architecture approval.

Preserved original: sources/PRD-v1.0-original-draft.pdf (26 October 2026), which itself says proposed baseline/draft. Other sources are earlier inventory outputs, not original accepted ADRs. No original accepted HLD/LLD or full architectural decision record was available.

## Layout
- docs/: HLD, LLD, database narrative, API guide and decision/provenance register.
- specs/: editable Mermaid ERD and OpenAPI 3.0.3 YAML draft.
- sources/: unchanged recovered PRD and inventory evidence.
- quality/: validation report, machine validation results and SHA256 manifest.

Review the unresolved baseline conflicts before implementation. This package delivers documentation; M0.1 and subsequent engineering milestones remain unapproved/incomplete.
