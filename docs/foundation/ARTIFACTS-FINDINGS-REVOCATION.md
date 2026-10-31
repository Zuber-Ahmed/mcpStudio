# Artifact manifests, findings and plan revocation — foundation slice 5

Implemented 29 October 2026 in `005_artifacts_findings_revocations.sql`. The current five-migration suite passed 101 checks, then removed its isolated PostgreSQL container. Running workflow/storage databases were unchanged.

## Artifact records and publication

Artifact metadata is immutable and scoped to a tenant/generation. Relative paths use `/` and a restricted ASCII alphabet: letters, digits, `_-.@()+` and separators, at most 240 characters. Empty/absolute/drive/UNC paths, backslashes, dot/traversal/empty segments, percent escapes, spaces, trailing dots and Windows reserved device names are rejected. Case-folded uniqueness prevents Windows case collisions within one generation. Sizes must be nonnegative and hashes lowercase SHA-256. Storage keys are opaque nonblank object references, not host paths.

`worker_artifact` requires current identity, membership and an enabled assignment. It locks the run and permits inserts only before generation is terminal. Publication locks the plan/run, checks explicit revocation and inserts an immutable artifact-set manifest. The supplied manifest must be nonempty and exactly match all artifact `{path, sha256, size_bytes}` descriptors in ASCII path order; its exact bytes must hash to the published digest. Descriptor changes, missing rows, order changes and hash mismatches fail atomically, leaving no succeeded generation or published set. Artifacts cannot be appended after publication.

The new three-argument `worker_publish(run,digest,manifest_bytes)` is required. The digest-only form now fails closed. Manifest bytes in the fixture come from the pinned RFC 8785 library; PostgreSQL verifies their hash and JSON content, not complete RFC canonicality/duplicate-key semantics. A trusted server publisher must still normalize and validate canonical input. These database functions cannot establish that stored object bytes match a metadata hash; actual worker/object verification remains required before invoking publication.

The path rule is deliberately narrower than arbitrary Unicode/Windows filenames. ADR-M03-DB05 records this portable foundation policy; widening it requires normalization/collision tests. This is syntactic database validation, not host filesystem containment: canonical roots, symlink/mount/reparse escapes, extraction safety and cancellation cleanup remain H03 obligations.

## Finding ownership

Immutable findings have same-tenant generation references and stable keys unique within that generation. Severity follows the existing API values `info`, `warning`, `blocking`. Validation-check/finding links must match both the validation's generation and the finding's generation; cross-run links are rejected. Finalized validation cannot gain new finding links.

This slice implements storage/ownership only. Runtime roles cannot directly forge finding rows; a dedicated guarded worker ingestion path is still pending. A severity label does not itself replace the pinned mandatory-check verdict. Actual finding computation, redaction, assertion-to-check mapping and complete immutable report/bundle binding remain integration requirements. The fixture does not claim real source analysis or command execution.

## Explicit plan revocation

`backend_revoke_plan` derives tenant/actor from the authenticated runtime principal and records a nonblank reason. Parent analysis/plan locks serialize revocation with supported admission/publication/export. Revocation records and audit entries commit together and cannot be edited/deleted. Workers and foreign-tenant backends cannot revoke the plan.

Supported admission checks the revocation even before idempotent replay, so a previously accepted key cannot return an executable admission after revocation. New admission, assigned worker publication and approved-export record creation are denied. The concurrency test observes revocation holding its transaction lock, observes export blocked behind it, then verifies export fails once revocation commits. Already-running external work is not cancelled by a database row: orchestration cancellation, execution-time egress checks and dispatch recovery remain H03/integration work. Existing approval revocation remains independently enforced.

The database wrapper is not an HTTP endpoint. The eventual revoke POST still needs the standard request-idempotency/error-mapping/session contract. Multiple retained revocation records are permitted by the logical one-to-many audit relationship; no unrevocation path is introduced.

## Reproduction and compatibility

```powershell
python tools/fixtures/m03/artifact-chain-runner.py
python tools/map-physical-schema.py
```

The current runner applies migrations 001–005 to a fresh, network-disabled PostgreSQL instance, includes the prior ownership/role smoke path, and captures its actual column catalog before cleanup. Trusted in-memory artifact byte fixtures supply expected hashes/sizes; no object store or host source repository is mounted by the database test. Individual older suites remain historical tests of their earlier schema stages and do not include the newer required fields/publication signature.

Migration 005 adds required manifest bytes without inventing historical provenance. Existing experimental artifact sets must be explicitly reconciled before applying it; migration validation fails rather than silently fabricating bytes. Use a reviewed application migration journal and dedicated cluster. Do not apply these migrations to Temporal's database. Administrative provisioning/upgrade tooling remains pending.

## Model/gate update

All 23 logical entities now have physical representations and every source field remains mapped or explicitly missing in PHYSICAL-MODEL-MAPPING.md. **Zero absent entities does not mean a complete schema**: identifier/version type differences, logical fields, full policy/config/secret validation, audit actor attribution, worker/object/API integration and lifecycle/recovery remain open. H01 stays partial; H02 browser security, H03 paths/recovery and H04 complete dependency/image review remain open. Local-first, application-agnostic core and five approved screens are unchanged.

Next foundation work: reconcile the remaining physical fields and identifier/version representations with the contract, then exercise the complete schema and privilege model through the application boundary. No product screen/API, deployment, commit or push was added in this slice.
