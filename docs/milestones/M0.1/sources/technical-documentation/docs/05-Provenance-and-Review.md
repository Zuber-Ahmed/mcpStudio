# Provenance, reconciliation and review register

## Recovered evidence
Conversation: MCPStudio, 6adf8000-7004-83ed-b840-4aee7adb5739. Retrieved 28 October 2026: available turns include implementation kickoff, mini-step proposal, documentation requests and proposed frontend stack. Retrieval returned no older cursor or attachments; this does not establish that older files never existed.

Agent message 9095aeb7-8bc7-4be5-9484-d2fedd1beeb6 describes proposed frontend tooling and retained backend stack; ecf760d1-f32b-4ff4-98f4-eedd5eee5eba preserves local-first, five screens and application-agnostic principles; 7e698c70-06bb-4882-ab44-48fe50e8cc2d distinguishes proposed roadmap from implementation.

Recovered from sibling chat output M0.1: PRD original PDF, decisions.md, inventory.md, prd-intake.md and source-conversation.json if available. Copies preserve bytes; manifest records SHA256. The PRD is explicitly a draft. Inventory ADR IDs are local tracking references, not original accepted ADRs. Earlier chat 'Assemble MCPStudio specifications' found Library candidates but did not recover the claimed enterprise scaffold or detailed specifications. Its description of a candidate is not evidence of its contents or approval.

## Bounded search result
Filename searches in Documents/Codex and Documents found no original openapi.yaml or database-erd.mmd. Checked C:/Users/ADMIN/mcpStudio: README, Git metadata and PRD only at top level. Relevant Downloads candidates were a demo video and Stitch workspace ZIP, not the backend scaffold. The prior inventory reports connected Drive searches returned no relevant inputs. Library originals and uninspected Git branches/history remain possible sources; this package does not claim exhaustive account-wide recovery.

## Authorship register
- Original PRD PDF: existing source, itself draft, unchanged.
- Inventory/decisions/intake/conversation: existing secondary evidence, unchanged copies.
- HLD, LLD, database narrative, Mermaid ERD, OpenAPI YAML/API guide: newly authored in this task, review drafts.
- PDF, validation and manifests: newly generated packaging/evidence, not architecture approval.

## Decisions still requiring review
R01: Reconcile CLI-first Node/SQLite PRD against five-screen Studio Go/Python/PostgreSQL narrative. Do not silently replace either as approved.
R02: Ratify concrete stack, local topology, required versus optional Redis/Temporal and Windows sandbox support.
R03: Define initial analyzer support matrix while preserving application-agnostic extension contracts.
R04: Pin MCP protocol, SDK and transport compatibility; old UI examples are not interoperability evidence.
R05: Ratify plan hash canonicalization, invalidation set, revocation and concurrency behavior.
R06: Select identity issuer/bootstrap, tenant membership roles, secrets mechanism and optional inference consent/egress policy.
R07: Approve physical schema/migrations, JSON contracts, data lifecycle and audit retention.
R08: Review all proposed endpoints, asynchronous job semantics, error taxonomy, graph limits and omitted UI capabilities.
R09: Define mandatory validation checks, draft versus validated export rights and sandbox/network/install policy.
R10: Resolve Stitch status/token conflicts; retain five screens. Define measured acceptance targets and evidence required for milestone approval.

Review owner for each item: product/architecture/security as appropriate, not yet assigned. Approval/date: pending. This documentation task does not close M0.1 or authorize implementation milestones.
