# Tooling-free Python runtime candidate evaluation

Recorded 30 October 2026. H04-R03 has a tested candidate remedy; H04 and M0.3 remain OPEN. Neither candidate is adopted. Approved version pins, baseline image tags and running service configuration remain unchanged.

## Implementation

`tools/readiness/evaluate-python-runtime-candidates.py` checks that each input image ID matches the previous audit, assigns a verified local build-input alias, then builds offline using that local input. It removes pip, its vendored modules and metadata, ensurepip (including its bootstrap wheel), and the worker/service wheel archives. A fresh final stage copies the cleaned filesystem, preserving the baseline environment, non-root user, command and working directory. Final layer IDs do not overlap the original image layers; this avoids retaining the removed tooling in inherited final-image layers. Build inputs/cache still retain the originals locally for reproducibility; they are not claimed to have been erased.

This is a candidate packaging experiment, not an adopted production Dockerfile. Application distribution names/versions remain exactly equal to the baseline inventory excluding pip. Both candidates run as UID 65534. No runtime package installation is supported; future dependencies must enter a controlled build stage. This change does not make source execution safe or replace H03 controls.

## Results

| Per-image findings | Baseline | Candidate |
|---|---:|---:|
| Critical | 0 | 0 |
| High | 49 | 44 |
| Medium | 60 | 58 |
| Low | 62 | 61 |
| Unknown | 1 | 1 |
| Total | 172 | 164 |

Both worker and service candidates have these counts. Trivy reported zero remaining language-package findings; all 164 remaining findings per image are OS-package findings. These are package/advisory occurrences, not confirmed reachable exploits. Scans use the same advisory database as the baseline, exact candidate IDs, OS/library scanning and no filters or suppressions. Shared OS findings must not be summed into a distinct vulnerability count.

59 functional/boundary check entries passed: 11 parser/runtime/Temporal sandbox checks and 14 isolation/resource/deadline/cleanup checks for each candidate, plus 9 service-client checks. The service regression exercised real Temporal activity execution, authenticated S3 writes/reads, invalid credentials, digest/metadata verification, fresh-process readback and deletion of the unique test object. Test containers were removed. Completed fixture workflow history remains under normal local service retention. No services were restarted, so restart/recovery is explicitly NOT claimed by this candidate run; `restart_phase_complete` remains false.

The existing boundary runner now accepts `--image` and `--evidence-dir`, preserving its original defaults. Candidate reports stay separate from the original readiness evidence.

## Reproduction and evidence

Run `python tools/readiness/evaluate-python-runtime-candidates.py` from the repository after the original readiness images, Trivy/database and local service fixtures exist. The runner saves inventory, raw scans, generated Dockerfiles and runtime/service/boundary reports under `docs/quality/runtime-candidates/python-tooling-free/`. It uses the existing ignored local fixture env file without printing credentials. The central readiness index hashes the evidence and collector source. A scan-database refresh requires a refreshed baseline for a fair comparison.

The first build attempt exposed that BuildKit interpreted a bare `sha256:...` FROM as a registry tag. The runner now resolves the verified local image through an ID-derived local alias. No downloaded replacement image was used.

## Next gate

Retain these as evaluated candidates while H04-R01 addresses the remaining Python/PostgreSQL OS layers and H04-R02/R04 address embedded Go and Alpine findings. Rerun exact-image scans and impacted runtime, database, service persistence/restart and boundary checks on the combined final candidates before adoption. No risk waiver or milestone transition has been granted. H01 integration, H02 browser session security and H03 acquisition/path/cancellation/recovery also remain open. Local-first, application-agnostic and the approved five-screen design decisions are preserved.
