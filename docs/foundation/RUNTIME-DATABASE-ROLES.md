# Scoped database runtime roles — foundation slice 3

Implemented 29 October 2026. Migration `003_runtime_roles.sql` creates private ownership and narrowly granted runtime entry points after migrations 001/002. The combined real-login fixture passed 56 checks and removed its disposable database/container. Running service databases and host login accounts were unchanged.

| Capability | Access |
|---|---|
| studio_kernel_owner | NOLOGIN, non-superuser owner of private schema, tables, sequences/domain and functions; never granted to runtime principals |
| studio_backend | NOLOGIN group; execute backend_submit, backend_run_status, backend_validate and backend_export only |
| studio_worker | NOLOGIN group; execute worker_publish, worker_check and worker_finish_validation only |
| PUBLIC / ordinary login | No access to kernel schema/data/functions |

Runtime groups have no raw table/sequence privileges, CREATE, owner membership or elevated role flags. Definer functions run under the non-login owner with fixed `pg_catalog, studio_admission, pg_temp` lookup order. All existing kernel functions receive the same hardened search path. Future functions created by the designated owner default to private EXECUTE globally; future migration authors must still explicitly review grants and search paths.

## Identity and assignments

Administrative `runtime_principal` records bind authenticated PostgreSQL `session_user` to one tenant/actor/capability and enabled state. Functions recheck current active membership. Identity is not taken from a supplied tenant ID, caller search path, custom session variable or current role. Backend entry points accept resource IDs and resolve tenant/actor internally.

An administrative `worker_assignment` additionally binds a worker login to one tenant/run and enabled state. Workers cannot create/enable their own assignments, access an unassigned run or invoke backend functions. Evidence functions resolve validation to its tenant-scoped run before checking assignment. Disabled principal/membership/assignment is denied on the next transaction. Row locks hold those checks stable within a transaction; orchestration must handle normal PostgreSQL deadlock/serialization retry outcomes safely.

This is a scoped local-operator database boundary, not browser authentication. A future connection pool must preserve the authenticated principal binding and must not multiplex unrelated actors through one mapped login. No untrusted client receives database credentials. Group roles are intentionally NOLOGIN; credentials and actual principal provisioning require an administrative deployment step, not a password embedded in this migration.

## Guarded workflow

The fixture authenticates separate backend, foreign-tenant, worker, unassigned, unmapped and ordinary logins using isolated container-local PostgreSQL authentication. It proves authorized admission/replay, status lookup, assigned publication, validation/check evidence, finalization and approved export work through wrappers. Direct reads/writes/audit inserts/truncation/DDL/internal functions/owner switching, foreign resources, spoofed tenant settings and temporary shadow tables are denied or ineffective.

Worker publication trusts a verified artifact digest supplied by the assigned worker; it cannot prove object bytes. Worker check ingestion trusts that assigned worker's execution evidence. No command is launched by these database functions. Actual object-byte verification, worker execution, failure/cancellation handling, lease/attempt identity and recovery still require integration before product use. The current backend admission wrapper exposes local generation only; it does not enable an inference-provider path or bypass consent.

## Migration and reproduction

```powershell
python tools/fixtures/m03/runtime-role-runner.py
python tools/map-physical-schema.py
```

The fixture requires the selected Docker Linux engine/image and existing isolated Python canonicalizer tools. It uses no published ports or network. Fixture LOGIN roles are created only inside that disposable cluster, so this run does not test production passwords/TLS or provision host accounts. Actual service databases have not received these migrations.

Migration 003 is an administrative, one-time operation in a dedicated application cluster. Role names are cluster-wide; existing name conflicts fail the migration rather than silently adopting an unknown role. Apply through a future reviewed migration journal with appropriate admin privileges; do not run as a runtime group or apply blindly to the Temporal service database. No destructive down migration is provided.

## Physical-model inventory and gate

The role fixture captures `information_schema.columns` after all three migrations in `physical-schema-catalog.json`. The mapping accounts for all 23 logical entities and every declared field as mapped or missing, with source hashes. 7 logical entities are absent: GRAPH_NODE, GRAPH_EDGE, ARTIFACT, SOURCE_SNAPSHOT, RECOMMENDATION, FINDING, PLAN_REVOCATION. Every other logical resource is still partial; type/name correspondence is not semantic/API completion. See PHYSICAL-MODEL-MAPPING.md for remaining fields and identifier/type mismatches.

ADR-M03-DB03: separate non-login ownership from backend/worker capability groups, expose only scoped definer functions and bind identities to authenticated login/administrative assignments. Alternatives rejected: grant tables to runtime (bypasses routines), rely on mutable custom tenant settings (spoofable), or grant the owner role (escalates privileges). Consequence: provisioning/pooling/worker dispatch must explicitly preserve this boundary, and new operations require reviewed narrow entry points.

H01 now has executable runtime privilege evidence and a complete gap inventory, but remains open for the remaining physical entities/fields and application integration. H02 browser bootstrap/session, H03 paths/cancellation/recovery and H04 full dependency/image review remain open. No five-screen product implementation, network inference, deployment, commit or push occurred. Local-first and application-agnostic decisions remain unchanged.

Next physical-schema slice: implement the missing source snapshot, graph and recommendation ownership chain and reconcile identifier/version representations before connecting a product API.
