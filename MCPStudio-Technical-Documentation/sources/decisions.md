# Architecture decision inventory

These are inventory ADRs, not substitutes for the unavailable original ADRs. Current constraints are preserved; implementation details remain pending.

| ADR | Status | Decision / context | Consequence and verification |
|---|---|---|---|
| ADR-001 | Preserved user constraint | Local-first: local MVP development/testing requires no paid hosting or cloud deployment. Optional remote inference must remain an explicit optional capability. | Do not provision cloud services in M0.1. Reconcile local service topology and egress policy with architecture; T01/T06. |
| ADR-002 | Preserved user constraint | Application-agnostic MCP architecture. Source app/framework examples do not determine core model or supported set. | Preserve capability/plugin separation as mapping target; actual interface and support matrix pending A1/P1. T02/T09. |
| ADR-003 | Recovered baseline; source reconciliation pending | Five-screen minimalist design; Stitch is visual reference and OpenAPI is contract reference; backend enforces security. | Do not redesign or infer real backend from HTML. Resolve Z1 internal conflicts and recover O1. T03/T17. |
| ADR-004 | Required; pending | Define versioned plan approval: which type, adapter, config, transport, source or policy changes invalidate approval? Bind actor, input revision, plan version and generation atomically. | Historical requirement explicitly covers integration-type change and backend version validation. Broader invalidation is a decision to ratify, not silently accepted scope. T11/T12. |
| ADR-005 | Required; pending | Define deterministic local parsing vs optional inference boundary, allowed payloads, retention, secret handling and manifest/source writes. | Must support privacy copy with evidence; no automatic source modification inferred from prototype. T05/T06/T16. |
| ADR-006 | Required; pending | Define validation result model, mandatory check policy, bundle gate, draft permissions and local sandbox verification. | Export decision must use exact artifact/policy version; distinguish per-file approval from bundle approval. T14/T15. |
| ADR-007 | Required; pending | Reconcile canonical screenshot/HTML revisions, design tokens and project/run status vocabulary. | Preserve five screens while removing ambiguity; no code changes before approved canonical baseline. T03/T04/T08. |
| ADR-008 | Required; pending | Pin MCP protocol/schema/SDK/transport compatibility and application capability model. | Exported 2024 labels, runtime versions and command examples remain examples until validated against chosen authoritative specification. T02/T10/T12. |
| ADR-009 | Required; pending | Verify existing stack/foundation and local service topology before adopting proposed frontend tooling. | C1.stack is proposal/retention narrative, not a manifest. Avoid unnecessary services or reinitialization over an existing repo. T01/T17. |

Each pending ADR needs an owner, source references, alternatives considered, decision, consequences and approver/date before being marked accepted. No new technology selection was made here.
