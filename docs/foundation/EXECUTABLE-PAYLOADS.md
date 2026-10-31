# Immutable executable payloads and policy labels — foundation slice 7

Migration `007_executable_payloads.sql`, `tools/plan_payload.py` and the current seven-migration fixture were implemented within M0.3. 59 checks passed; disposable PostgreSQL was removed. Running service databases were unchanged and original API/data dictionary files were preserved.

## Bound payloads

The earlier reduced fixture envelope is replaced by the unchanged OpenAPI CanonicalPlan shape: source/snapshot/analysis identity, analyzer pins, recommendation/version, selected type, executable candidates, generator, plugin/schema/configuration values, stdio transport, policy reference and explicit nullable override reason. The current supported path is server/stdio with no type override. Other outcomes remain inspectable recommendation data; no unsupported execution capability is enabled.

Candidate rows now carry all declared operation/side-effect/sensitivity/scope, I/O schema, eligibility/reason, evidence, detector, provenance and confidence metadata plus a domain-service reference. Allowed candidates require read-only/no-side-effect metadata, known sensitivity, deterministic provenance and nonempty same-source evidence. Model/write/unknown-sensitivity, duplicate scopes and eligibility disagreements are denied. A full stored Candidate fixture validates against the original schema.

Canonical executable candidate descriptors must exactly match the selected immutable row's I/O schemas, scopes and domain-service reference. They must remain within the pinned recommendation. Confidence/provenance scores do not enter executable candidate descriptors. A complete plan pins analyzer versions to the analysis record and binds all configuration/plugin/schema/generator references in its SHA-256. Updating immutable candidate/policy/plan rows is not an upgrade path.

## Canonical boundary

`tools/plan_payload.py` normalizes UUIDs/digests and specifically set-valued candidate IDs, analyzer IDs, scope names and required-check names. It rejects duplicate set identities. Ordered configuration arrays remain ordered. The unchanged full CanonicalPlan schema is validated before the pinned RFC 8785 library serializes it. The strict JSON decoder rejects duplicate object keys and nonfinite constants; serialization rejects unsafe integers, malformed Unicode and nonfinite floats. Tests include those negative cases and stable set versus ordered-array behavior.

This is a foundation helper using the isolated pinned authoring tools, not a deployed publisher/API. A real service must use a strict JSON input boundary and the canonical helper before submitting bytes. PostgreSQL checks exact bytes/hash, immutable references and selected metadata, but is not itself an RFC 8785 canonicalizer. An owner bypassing the trusted boundary could submit noncanonical but semantically equal JSON; no full database-only canonicality claim is made.

## Exact policy versions

Policies now store nonempty opaque `version_label`, policy key, schema version and immutable canonical content. SHA-256 content hashes derive from the exact stored bytes. Content must match the stored identity/label/check list. Labels `01` and `1` remain distinct; numeric-looking labels are never coerced to another version. An integer revision remains a private relational FK key and is not the public version. Plan and validation projections resolve the exact label through the immutable policy binding.

The private plan projection derives configuration, candidate IDs, generator, rationale/risks and lifecycle state from canonical binding/recommendation/approval/revocation authorities. The scoped backend Plan document validates against the unchanged schema in draft and approved states. Required nested `override_reason: null` remains present; absent optional outer fields are omitted without recursively stripping required nested nulls. Foreign tenants, workers and raw view access are denied.

Generations derive and retain their exact generator reference from the approved canonical plan. The fixture completes artifact publication, validation and an approved export record through scoped roles, then publishes changed configuration/plugin/schema/generator/policy plans and verifies the old approval cannot authorize them.

## Reproduction and evidence

```powershell
python tools/fixtures/m03/payload-chain-runner.py
python tools/map-physical-schema.py
```

The current suite applies migrations 001–007 to a fresh network-disabled database, validates CanonicalPlan, Candidate, Plan and PolicyReference using the original OpenAPI and exercises scoped admission/publication/export with trusted fixture metadata. It captures the actual migrated catalog before cleanup. It is a focused current integration suite, not the sum of earlier slice counts. Earlier runners remain historical fixtures of their earlier schemas.

The migration requires complete payload/policy/candidate provenance; it does not backfill old reduced envelopes or invent analyzer pins. Retained experimental data must be explicitly reconciled using a reviewed upgrade before application. Do not apply to Temporal's database. Production migration journaling and provisioning are still pending.

## Remaining gate

Installed plugin compatibility, plugin-specific Configuration.values schema validation, real detector/source truth, credential-reference/secret-redaction policy, actual generator/command execution, object bytes, cancellation/recovery and HTTP/session protection are not established by structural metadata or fixture validation. Confidence/evidence values are trusted fixture data; no source analyzer, inference call or generator plugin was implemented. Runtime disclosure through these database functions must remain behind the eventual approved session/auth boundary.

The field inventory now has 7 unmapped declared fields: principal/tenant/project display and source metadata, membership role and timestamps. All other dictionary fields have physical columns or explicitly mapped immutable projections, but that is not complete semantic/API readiness. Array-backed fields serialize to JSON arrays; private integer policy revisions remain separate from public exact string labels. The earlier policy-version representation mismatch is superseded by these tested label projections.

ADR-M03-DB07: store exact canonical executable payloads and opaque policy version labels, retain internal relational revision keys privately, and derive public projections rather than duplicate mutable plan state. Consequence: publisher/serializer and plugin validation remain mandatory trust boundaries, and old reduced envelopes fail closed after migration.

H01 remains open for final metadata and full schema/application semantics. H02 bootstrap/session, H03 actual path/worker recovery and H04 dependency/image review remain open. Local-first, application-agnostic core and the five approved screens are unchanged. Next foundation slice: reconcile the seven remaining principal/project metadata fields, then consolidate physical-schema acceptance and remaining runtime/security holds before any product milestone approval.
