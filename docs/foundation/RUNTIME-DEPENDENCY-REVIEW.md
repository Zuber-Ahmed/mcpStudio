# Runtime dependencies and container-image readiness review

Recorded 30 October 2026, Asia/Calcutta. The review is complete; **H04 remains open** because image findings and final application coverage remain unresolved. No dependency upgrade, image adoption, running service restart/data migration, deployment, commit or push was performed.

## Executed package and integrity review

- Both actual isolated npm locks (`contract-tools`, `mcp-fixture`) returned zero npm audit advisories. No audit fix/install was run.
- OSV returned no advisories for the 31 explicit pinned Python package versions at query time. This scope excludes package-manager vendor bundles, which were reviewed separately below.
- The official Node security-wg core database at recorded commit was evaluated against Node 26.13.0: 204 advisory records, no matching unpatched ranges and no unparsed records. Go stdlib/toolchain OSV queries for selected 1.27.3 returned no advisory IDs. These are advisory-range matches, not host OS or imported-symbol reachability assessments.
- Sixteen preserved-lock/wheel checks passed: both installed fixture locks match their recorded copies, and fourteen downloaded worker/service SDK wheels retain their pinned SHA-256 values.

Uninitialized frontend/API workspaces do not constitute installed application dependency locks. Actual future runtime selections require review when adopted. A clean explicit lockfile audit cannot establish that a container's OS packages, embedded Go binaries or pip-vendored modules are clear.

## Image scanning

Docker Scout 1.27.0 could not scan without a Docker Hub login. The review instead installed Trivy 0.76.1 only under ignored project work, verified its official release checksum and downloaded its public advisory database. Scanner provenance includes binary/archive SHA-256 and database timestamps. Sigstore signature verification was not performed. Analysis targeted exact local image IDs with Docker-only resolution; no source repository, `.local` credential directory or user application was scanned/uploaded.

All eight trusted local images completed OS/library vulnerability scanning with raw JSON reports retained, no severity filtering and no suppressions:

| Image | Critical | High | Medium | Low | Unknown | Findings with a reported fix |
|---|---:|---:|---:|---:|---:|---:|
| postgres | 2 | 86 | 140 | 141 | 5 | 61 |
| temporal | 0 | 6 | 15 | 4 | 5 | 29 |
| schema | 1 | 32 | 76 | 20 | 16 | 139 |
| storage | 0 | 1 | 0 | 0 | 3 | 3 |
| python_base | 0 | 49 | 60 | 62 | 1 | 8 |
| worker_fixture | 0 | 49 | 60 | 62 | 1 | 8 |
| service_fixture | 0 | 49 | 60 | 62 | 1 | 8 |
| sandbox_smoke | 2 | 19 | 29 | 51 | 2 | 103 |

Counts are scanner package/advisory occurrences per image, not distinct reachable exploits. Shared layers, repeated binaries, advisory aliases and inherited images repeat findings. Reports include unfixed and unknown-severity records. Successful scan exit codes indicate collection succeeded, not that security readiness passed.

## Corroborated findings and applicability

PostgreSQL includes scanner-reported critical libxml2 and Go-stdlib/gosu entries. Temporal server and admin-tool binaries include reported outdated Go/module dependencies; the admin-tools image also includes a critical Echo advisory in its bundled Temporal CLI. The schema container is a one-shot tool and was confirmed exited successfully, but its image findings are retained. The selected host Go 1.27.3 does not patch embedded older Go binaries in these images.

The Python images include pip 26.2.2 vendor metadata for msgpack 1.1.2, urllib3 2.7.0 and setuptools/pkg_resources 70.3.0. Read-only no-network container inventory confirmed vendor module directories and `pip/_vendor/bom.cdx.json`. The service fixture separately has top-level urllib3 2.8.0; updating that distribution did not update pip's vendored copy. OSV cross-checks returned advisories for those vendor versions. This is not dismissed as a stale SBOM or suppressed merely because top-level distributions are absent. Per-advisory code-path applicability remains to be established; setuptools metadata can describe a broader package than the vendored subset.

Alpine's two critical package entries share CVE-2026-31789. The [OpenSSL vendor advisory](https://www.openssl-library.org/news/vulnerabilities-3.5/index.html) classifies it Low and limits it to 32-bit platforms; the scanned image is amd64. That is a documented non-applicability candidate, not an automatic waiver. Raw findings remain unchanged. Other Alpine findings still need review/remediation. This follows the distinction between inventory findings and application-specific risk; no advisory was silently removed.

The [Trivy maintainers' pip SBOM discussion](https://github.com/aquasecurity/trivy/discussions/11031) explains why embedded vendor packages and top-level distributions can coexist; the local inventory is the evidence for this project's images.

## Remediation package

- H04-R01 — Pinned PostgreSQL/Python OS layers: Select maintained rebuilt base digests/OS package fixes; retain selected runtime versions where possible. Rescan and rerun affected runtime/schema/service fixtures before adopting candidates.
- H04-R02 — Temporal server/admin-tools, SeaweedFS and gosu embedded Go dependencies: Obtain upstream rebuilt binaries or reviewed builds with patched Go/modules. Installed host Go does not patch binaries embedded in images. Verify actual compiled versions and rescan; do not hot-edit running services.
- H04-R03 — pip-vendored msgpack/urllib3/pkg_resources metadata in Python base/worker images: Upgrade the complete pip bundle or remove build/package-manager tooling in a verified final runtime stage. A top-level urllib3 upgrade alone does not replace pip._vendor. Retest parser/workflow/storage integration and preserve unsuppressed baseline reports.
- H04-R04 — Alpine sandbox-smoke image: Refresh supported patch digest and rescan. Separately document CVE-2026-31789 architecture/vendor severity applicability; do not equate raw critical package counts to confirmed critical exploits.
- H04-R05 — Final application dependencies and coverage: Review actual frontend/API/worker dependency locks and exact adopted images before product execution. Reserved/uninstalled frontend candidates are not audited application installations; no exploit reachability or full host/Docker/WSL security certification was performed.

Prepare replacement/rebuilt candidates separately, record exact digests and compare unsuppressed reports before adopting them. Keep the selected language/runtime/protocol constraints unless a reviewed compatibility change is necessary. Retest affected runtime/parser/sandbox, PostgreSQL migration/concurrency, Temporal activity/restart and signed S3 persistence fixtures after changes. Do not upgrade a running data service or reinterpret an unfixed finding as accepted risk solely to clear this gate.

## Reproduction and artifacts

`docs/quality/runtime-audit/assessment.json` is the result summary. `image-review.json` links exact image IDs, individual raw reports, package counts, scanner/database identity and report hashes. `triage.json` contains critical entries and tracked remediation tasks. `inventory-corroboration.json`, `vendored-python-review.json`, `npm-review.json`, `core-runtime-review.json` and `lock-integrity.json` state their independent scopes. The explicit Python review remains at `docs/quality/python-dependency-review.json`.

```powershell
python tools/readiness/prepare-runtime-audit.py
python tools/readiness/audit-npm-runtime.py
python tools/fixtures/m03/audit-python-dependencies.py
python tools/readiness/audit-core-and-integrity.py
python tools/readiness/scan-runtime-images.py
python tools/readiness/corroborate-image-inventory.py
```

These repeatable collectors require their recorded network sources plus local Docker access for image scans; they do not log into external accounts, install global tools, run repository scripts from downloaded advisory data or change adopted dependency pins. Database/report timestamps and advisory data must be refreshed for later reviews. Detailed scan scope is described by the [official Trivy image documentation](https://trivy.dev/docs/dev/guide/target/container_image/).

The vendored OSV cross-check and primary-vendor applicability notes are a separate reviewed triage snapshot; refreshing collectors does not itself regenerate/accept that decision record. Individual report changes require refreshing the central evidence index.

## Current approval gate

H04 is now evidence-backed OPEN rather than unscanned: explicit fixture package audits are clear, while OS/embedded/vendored image findings require remediation or documented applicability review. No risk acceptance was granted. H01 integrated data/publisher/plugin/worker/object semantics, H02 browser bootstrap/session and H03 real acquisition/path/cancellation/recovery remain open. All 23 entities/declared fields and SCHEMA-D01 remain reconciled. M0.3 is not complete and no later product milestone starts. Next foundation task: build/evaluate patched runtime-image candidates, rescan and rerun the affected readiness fixtures before adopting a new pin.
