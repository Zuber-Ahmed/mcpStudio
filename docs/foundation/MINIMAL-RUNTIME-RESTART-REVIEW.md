# Minimal runtime: isolated restart and final-file advisory review

Recorded 30 October 2026. Completed the next candidate-validation step. **No image adopted; H04 and M0.3 remain open.**

Candidate: `sha256:dc612ae7bb151a095b3848d9cbf45c17311514267c39950d3121e223ff52f797`.

## Isolated restart evidence

Created a uniquely named Compose project with fresh credentials, its own PostgreSQL/storage volumes, one internal network and no published host ports. It used the existing digest-pinned foundation server images, so this tests the candidate client's persistence compatibility, not remediation of server-image advisories.

The candidate executed the trusted Temporal/S3 fixture, then the isolated Temporal, storage and PostgreSQL containers were stopped gracefully. PostgreSQL was started and health-checked before Temporal/storage restarted. Container IDs and changed start timestamps establish that all three isolated services actually restarted. Completed workflow results and object bytes survived; the fixture's unique object was deleted afterward.

**11 service checks and 7 isolation/restart/cleanup checks passed.** The disposable stack's containers, network and volumes were removed. Temporary credential/configuration files were deleted. The original local stack's IDs, image IDs, start timestamps, running states and port bindings match before/after snapshots exactly. Existing local data and service configuration were not modified.

This is graceful restart persistence for completed workflow data. It does not establish abrupt-crash recovery, in-flight workflow replay, cancellation semantics or H03 application recovery.

## Final-file High advisory dispositions

Verified the final candidate's retained-file hashes and the absence of the affected tools/libraries. All eight distinct High advisories (44 conservative scanner rows) now have exact-candidate component-exclusion evidence:

- Four util-linux mount/nsenter advisories: mount/nsenter binaries and libmount payload are excluded; required libuuid remains and must not be equated with those affected paths.
- ACL: libacl payload excluded.
- ncurses: affected infocmp CLI excluded; required runtime libraries retained.
- systemd-homed: affected executable and its user-management tooling excluded.
- Perl Archive::Tar: Perl runtime and affected parser payload excluded.

The source/path rationale is linked per advisory in `high-advisory-dispositions.json`, including Debian's [infocmp description](https://security-tracker.debian.org/tracker/CVE-2025-69720), [ACL functions](https://security-tracker.debian.org/tracker/CVE-2026-54369), [systemd-homed description](https://security-tracker.debian.org/tracker/CVE-2026-16742) and [Archive::Tar description](https://security-tracker.debian.org/tracker/CVE-2026-9538). Dispositions concern these affected components in this immutable fixture candidate only. They do not cover baseline/server images, extra mounts, new plugins or changed payloads, and they do not certify every possible code path.

The raw scan remains **164 entries** and is unchanged. No suppression file, score adjustment or risk acceptance was created. Original package records deliberately remain conservative after payload removal. The other **120 Medium/Low/Unknown rows still require semantic review**; they are not automatically accepted. The image is not declared globally vulnerability-free.

## Artifacts and next gate

`tools/readiness/test-minimal-restart.py` reproduces the isolated regression using unique names/volumes, no host ports, redacted errors and bounded cleanup. `tools/readiness/review-minimal-high-advisories.py` reproduces component checks and assembles dispositions from the reviewed primary-source descriptions. A new/changed image or advisory requires fresh interpretation, not automatic inheritance of this result.

Evidence under `docs/quality/runtime-candidates/minimal-restart/` includes lifecycle/cleanup snapshots, the service report, component/hash checks and eight advisory dispositions. The central readiness index hashes scripts and reports. Local-first and application-agnostic decisions remain preserved.

Next gate: finish remaining candidate advisory review and separately remediate/review PostgreSQL, embedded-Go and Alpine images before runtime adoption. H01 integration, H02 browser-session enforcement and H03 real acquisition/cancellation/crash recovery remain open. This step closes the missing graceful restart evidence for this candidate; it does not close M0.3 or authorize a later product milestone.
