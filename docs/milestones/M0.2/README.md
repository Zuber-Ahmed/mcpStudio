# M0.2 — Baseline Reconciliation and Decision Freeze

Prepared 28 October 2026, Asia/Calcutta. Scope authorized by the user's `ok procced`. **Approved by user** in the subsequent message `ok please approved please procced further`, which also authorized M0.3 Contract Synchronization and Foundation Readiness. Historical candidate/pending labels in this package describe its review state before that approval. Evidence/readiness holds remain prerequisites; approval does not assert runtime functionality.

This milestone produces a concrete baseline for review. It does not initialize an application or claim implemented security, working screens or protocol compatibility. No files in `C:/Users/ADMIN/mcpStudio` were modified.

## Review package

- [Baseline](baseline.md): product surface, scope, stack, visual precedence and operational boundaries.
- [Decision records](decisions.md): explicit alternatives, choices, consequences and acceptance evidence.
- [Contract amendment](contract-amendment.md): normative changes required to the received API and ERD drafts before implementation.
- [Reconciliation register](reconciliation.md): disposition of every PC01–PC07, TC01–TC08 and G01–G15.
- [Acceptance and tracker](acceptance-and-tracker.md): measurable checks, dependencies, remaining gates and next step.
- [Validation report](validation-results.json): reproducible documentation checks from validate.py; not runtime tests.

## Authority and freeze boundary

Priority: current user constraints and milestone approvals → this baseline after approval → unchanged received technical drafts plus this amendment → original PRD where consistent → Stitch visual layout and canonical tokens. The original PRD is preserved, not rewritten as if it always specified Studio. The received technical drafts remain archived under M0.1/sources/technical-documentation; this milestone never edits evidence copies.

The amendment is a reviewable design contract, not a replacement OpenAPI file or executable SQL. It explicitly identifies fields/routes and semantic invariants that the next contract synchronization task must incorporate. Until synchronization and semantic checks pass, generating clients or building product features against the old draft is gated. No ambiguous supersession of the old 15-operation contract is intended.

## Approval requested

Approve this baseline and amendment as the design direction for the local Studio MVP. After approval, the next proposed mini-step is **M0.3 — Contract Synchronization and Foundation Readiness**: produce the amended OpenAPI/ERD, validate them, pin tool/protocol versions and prove the Windows container prerequisites. This next scope revises the earlier example that combined monorepo/tooling work; it is a proposal, not a recovered historical agreement. Application initialization follows readiness evidence, not document existence alone.
