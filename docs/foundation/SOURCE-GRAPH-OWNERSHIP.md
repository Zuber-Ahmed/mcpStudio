# Source snapshot, graph and recommendation ownership — slice 4

Implemented 29 October 2026 in `004_source_graph_recommendation.sql`. All four migrations were applied together in a disposable, network-disabled PostgreSQL instance. 48 checks passed and the fixture was removed. Existing local service databases were not migrated.

## Implemented constraints

- Immutable source snapshots bind tenant/project, source SHA-256, resolved revision and storage identity. Analysis requires a matching composite reference, including digest/revision; a snapshot from another tenant/project or changed digest/revision is rejected. Previous analysis references are scoped to the same tenant/project.
- Analysis now has explicit state, terminal completion time, snapshot identity and structured diagnostic/analyzer/scope columns. Source identity is fixed; terminal results cannot be reopened. Allocating a new plan can still increment its analysis version counter.
- Graph nodes/edges require nonblank labels/kinds/provenance and nonempty evidence arrays. Edge endpoints must exist in the same tenant and analysis. Graph records are immutable. Candidate node references use that same composite ownership boundary.
- Immutable recommendations reference succeeded analysis and its exact source digest. Candidate IDs must be unique and same-analysis; executable recommendations require a nonempty eligible set and the supported server type. Explicit `none`, client or both outcomes can remain non-generating records. Recommendation insertion locks the parent analysis and enforces the next contiguous revision; concurrent attempts to publish the same revision commit once.
- Plans require matching analysis snapshot and recommendation ID/version. The canonical payload must repeat those exact references and select only candidates from that recommendation. Existing SHA-256, source, eligibility, policy and transport guards remain in force. The old four-argument `new_plan` fails closed; the six-argument form requires explicit recommendation identity/version.
- New tables/functions are created as the non-login kernel owner, have no backend/worker raw grants and preserve hardened function lookup. Snapshots and recommendations receive transactional audit events. Real backend/worker logins can complete admission, publication, validation and approved-record creation through existing scoped wrappers using the expanded chain.

## Tests and reproduction

```powershell
python tools/fixtures/m03/source-chain-runner.py
python tools/map-physical-schema.py
```

The suite covers cross-tenant/project snapshots, digest/revision mismatch, exact predecessor FK rejection, cross-analysis edge/candidate links, empty evidence, unsupported/ineligible/duplicate recommendation inputs, incomplete analysis, version gaps, concurrent revision conflicts, immutable records, canonical payload scope changes, runtime privilege denial and the full guarded export-record path. The actual migrated catalog is captured before cleanup. Source evidence, commands and object digests are trusted fixture data; no repository scan or real bundle export is performed.

## Migration compatibility

This migration deliberately adds required references without synthetic backfills. Apply to a fresh reviewed foundation database. Any retained data from earlier experimental slices must first be explicitly reconciled; missing snapshot/node/recommendation references cause atomic migration failure. Never apply it blindly to the running Temporal database. Migration journal/provisioning and data-upgrade tooling remain future integration work.

Migrations 001–003 and their reports remain historical slice tests. Earlier fixtures insert fewer required columns and are not a full-chain compatibility suite after 004. The source-chain runner is the current four-migration integration fixture. Use it to refresh `physical-schema-catalog.json`; older runners capture only their earlier schema stage.

## Data-model mapping and remaining boundaries

The refreshed mapping covers all 23 logical entities and every declared field. Absent entities have reduced from seven to 3: ARTIFACT, FINDING, PLAN_REVOCATION. Column presence does not make the resources production complete. Identifier/version representation differences (including audit bigint versus logical UUID and integer versus string policy versions) remain explicit in PHYSICAL-MODEL-MAPPING.md; source contracts were preserved.

The database validates ownership, basic JSON shape and immutable references. It does not verify that snapshot storage bytes match their digest, evidence points to real source, graphs are complete/sealed, eligibility was computed correctly, model provenance is trustworthy, or canonical bytes satisfy the complete executable plan/config/plugin schema. No source acquisition, analyzer, inference call, recommendation engine or new runtime write grants are added. Source retention, scoped consent at actual egress and output sealing still require implementation. Current recommendation transport/mode guards preserve server/stdio generation only.

ADR-M03-DB04: use immutable snapshot identity plus composite tenant/project/analysis references through graphs, candidates, recommendations and plans; lock analysis for recommendation revision publication. Reject implicit backfills and unversioned plan references. Consequence: earlier experimental data/fixtures require an explicit upgrade, and new source/recommendation revisions remain separate records.

H01 remains open for the remaining physical resources, full payload/evidence validation, representation reconciliation and application integration. H02/H03/H04 remain unchanged. Next physical slice: artifact manifest/path constraints, finding ownership and explicit plan-revocation records. M0.3 stays open; no new milestone or product UI/API is started.
