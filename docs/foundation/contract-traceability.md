# Approved amendment → synchronized artifact → validation mapping

M0.2 approved by the user; this revision materializes its design amendment as review contracts. The user then chose contract files only; runtime proof and dependency installation remain deferred. Schema/local model checks are distinct from production enforcement.

| Amendment | Operations / schemas | Data model / semantic rule | Check evidence and remaining obligation |
|---|---|---|---|
| CA01 | listProjects q/status/cursor/limit; Project summaries; listProjectRuns | PROJECT projection; ANALYSIS_RUN/GENERATION_RUN/VALIDATION_RUN; latest effective lineage | Operation/parameter structure checked; live sorting/filtering/status/resume tests pending |
| CA02 | Source git/local oneOf; AnalysisInput scope/consent; getSupportedCapabilities | SOURCE_SNAPSHOT, INFERENCE_CONSENT, analyzer_versions; SEM-CONSENT | Local optional revision, Git missing revision, raw secret/command and consent boundary fixtures checked; real acquisition/egress proof pending |
| CA03 | listCandidates/getRecommendation; Candidate/Recommendation/Node/Confidence | CANDIDATE, RECOMMENDATION, GRAPH_NODE; SEM-CANDIDATE/PLAN | References/model fields checked; actual parser provenance/risk/recommendation fixtures pending |
| CA04 | Plan.canonical_payload; Approval versions/revocation; POST Idempotency-Key; revokePlanApproval | PLAN, APPROVAL, PLAN_REVOCATION, IDEMPOTENCY_RECORD, OUTBOX_EVENT; SEM-IDEMPOTENCY/APPROVAL/GENERATION | Confirmation schema checked; limited cross-language canonical vectors agree; full JCS, concurrency and stale approval admission tests pending |
| CA05 | CanonicalPlan, Generation/Validation digests, Check evidence | 23-entity dictionary and DB01–DB10; canonical payload/manifest rules | ERD/dictionary names and fields checked; no physical migration or FK/check/transaction tests run |
| CA06 | getArtifactContent/getValidationLogs/getGenerationReport; derived Artifact status | ARTIFACT/FINDING/VALIDATION_CHECK and policy references | Bounded parameters/references checked; actual redaction/preview/report generation and clipboard behavior not implemented |
| CA07 | Check conditional evidence; PolicyReference nonempty; downloadBundle/downloadDraftBundle acknowledgement | artifact_set_digest/policy binding; SEM-VALIDATION/EXPORT/DRAFT | Positive/negative export-gate reference scenarios and check schemas run; no API authorization/security execution claimed |
| CA08 | Resource cookie or bearer schemes, CSRF header, structured errors; 3 separate local session routes | Threat model; SEM-AUTH/BOOTSTRAP; polling/cancellation distinction | Secret/nonce request-shape fixtures checked; host OS store, Origin, CSRF, replay, expiry/logout tests pending |

## Contract boundary decisions

- Resource API: 24 operations. Separate bootstrap API: 3 operations. No source-script execution, deployment, merge, marketplace, cloud provisioning or tenant-admin endpoint added.
- OpenAPI version remains 3.0.3. JSON-compatible YAML preserves strict parsing; conditional behavior uses oneOf/allOf/not where supported and named semantic rules for cross-record conditions.
- Physical ERD enforcement is intentionally not inferred from logical arrows. Dictionary supplies field mappings and DB01–DB10 requirements to be translated and tested with migrations in a later authorized implementation step.
- Candidate pins are exact choices sourced from official project metadata, not dependency lockfiles or evidence of compatibility. Redis remains deferred, optional semantic inference unavailable until provisioned, and only server+stdio generation is executable initially.
- Source archives are unchanged. Updated contracts live only in this deliverable folder, ready to move into the project workspace when requested and access permits.

## Deferred evidence register

| ID | Item | Reason / current disposition |
|---|---|---|
| RD01 | Full OpenAPI meta-schema validator | Dependency download DNS failure; local checker is a limited substitute for design iteration only |
| RD02 | Generated TS client and typecheck | Generator package unavailable; cannot claim a generated client |
| RD03 | Full RFC 8785 implementation/vectors | Dependency unavailable; only restricted ASCII/integer byte/hash agreement checked |
| RD04 | Windows/Linux container isolation proof | Docker not found; user chose contracts only |
| RD05 | Database DDL/tenant/hash/transaction enforcement | No database/engine running; logical model only |
| RD06 | Pinned MCP client/server stdio compatibility | SDK not retrieved/run; wire protocol selection not interoperability proof |
| RD07 | Container digests, SDK/parser/frontend transitive lockfile/audit | Registry/engine/package resolution still required |
| RD08 | Real browser local-session/bootstrap security | Separate contract provided; implementation tests not run |
| RD09 | Target repository writes | Outside writable roots; deferred by user direction |

No new milestone is needed to clear these holds. Resume M0.3 readiness when the user enables environment work; no request to install or initialize is pending while contract-only preference remains in force.
