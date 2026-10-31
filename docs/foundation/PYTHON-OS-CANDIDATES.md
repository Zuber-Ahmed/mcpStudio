# Python OS/base-image candidate evaluation

Recorded 30 October 2026. Two isolated worker candidates completed evaluation; neither is adopted. H04 and M0.3 remain OPEN.

## Findings

The official Python 3.14.10 slim-Trixie tag resolves to the already selected digest. A signed Debian repository refresh and ordinary package upgrade changed only tzdata from 2026e-0+deb13u1 to 2026f-0+deb13u1. No reported security findings were removed. The official slim-Bookworm variant was also built with the exact existing hash-locked Python wheels and without pip/ensurepip/wheel archives.

| Image | Critical | High | Medium | Low | Unknown | Total |
|---|---:|---:|---:|---:|---:|---:|
| Prior tooling-free Trixie worker | 0 | 44 | 58 | 61 | 1 | 164 |
| trixie_apt_upgrade | 0 | 44 | 58 | 61 | 1 | 164 |
| bookworm | 2 | 59 | 91 | 89 | 2 | 243 |

Counts are scanner package/advisory occurrences, not unique vulnerabilities or exploitability scores. The exact candidates use the same Trivy binary and advisory database as the prior tooling-free baseline, with no suppression/severity filters. Raw OS/library scans are retained. No top-level Python dependency versions changed. Base distro changes can alter vulnerability classification and package coverage, so a lower count alone is not sufficient for adoption.

The [official Python image inventory](https://raw.githubusercontent.com/docker-library/official-images/master/library/python) identifies the two selected runtime variants. Debian's [util-linux issue](https://security-tracker.debian.org/tracker/CVE-2026-78408) and [ACL issue](https://security-tracker.debian.org/tracker/CVE-2026-54369) illustrate why a package refresh cannot currently clear every stable-release finding: both trackers list stable packages vulnerable, with fixes in newer distributions. These are examples, not a complete applicability review, and no finding is waived. Switching to Debian unstable or replacing core libraries is not an approved remedy.

## Validation and scope

50 checks passed: each candidate passed 11 Python/parser/Temporal sandbox checks and 14 Docker isolation/resource/deadline/cleanup checks. Runtime inventory equality verifies that application distributions match the preceding tooling-free worker exactly, and that pip, ensurepip and downloaded wheel directories remain absent. Python remains 3.14.10; both images are amd64.

The Bookworm build installs the preserved wheels offline with their existing hashes and runs pip dependency validation before removing tooling. The Trixie experiment uses signed configured Debian repositories; build logs and complete before/after package-version inventories record the selected update. Package upgrades are time-dependent, so rerunning against changed repositories produces a new candidate requiring review. The final filesystem is copied into a fresh image. Runtime tests retain non-root, read-only, no-network and bounded resource controls.

This stage evaluates worker OS choices only. It does not test a new service-client image, service restart/persistence, PostgreSQL migrations, real acquisition or application crash recovery. Existing services and approved images/pins are unchanged. Temporary test containers and boundary fixtures were removed; local candidate images/build caches remain for inspection. Source documents and the five approved screens are unchanged.

## Artifacts and reproduction

`tools/readiness/evaluate-python-os-candidates.py` is the collector. It imports the preceding candidate helpers, requires the recorded official base digests locally, builds/scans exact images and writes separate evidence under `docs/quality/runtime-candidates/python-os/`. Pull commands used during evaluation were `docker pull python:3.14.10-slim-trixie` and `docker pull python:3.14.10-slim-bookworm`; their resolved digests are in assessment.json. All subsequent candidate recipes use recorded digests or verified local aliases. Run `python tools/readiness/evaluate-python-os-candidates.py` after its baseline/scanner prerequisites are present.

The directory contains assessment.json, decision.json, raw scans, generated Dockerfiles, build logs, before/after package inventories and each candidate's runtime/boundary reports. The central readiness index hashes these files and the collector. Build-time inventories live outside /tmp because runtime /tmp is deliberately replaced by a temporary filesystem.

## Next gate

H04-R01 remains open: a routine refresh did not resolve the Python OS findings. Next is package/binary-specific applicability evidence and a reviewed minimal-runtime design, while PostgreSQL, embedded-Go and Alpine remediations remain separate pending work. Do not repeatedly rebuild unchanged bases or suppress advisories to clear this gate. Any chosen replacement requires exact-image rescans and relevant integration/restart regressions before adoption. No risk acceptance, approved-pin change or milestone transition occurred. Local-first and application-agnostic decisions remain preserved.
