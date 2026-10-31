# Worker OS finding paths and minimal-runtime design

Recorded 30 October 2026. Completed a file/path inventory and proposed the next isolated runtime design. No image was changed or adopted; H04 and M0.3 remain OPEN.

## Evidence and findings

All **164 scanner entries across 40 installed packages** now map to Debian source package/version, present owned files, ELF files and observed process mappings. Installed versions match the scan. The **44 High entries represent eight distinct advisories**; repeated source-package attribution explains much of the count. This is an inventory, not 164 exploitability determinations.

The exact preceding tooling-free worker image was inspected without network access, as UID 65534, with a read-only root, no-new-privileges and zero effective/permitted/bounding capability sets. The trusted parser/Temporal fixture passed its 11 checks. File ownership and ELF/set-ID hashes are retained; process maps were collected after fixture execution. The inventory made 85 native dependency queries: **84 resolved, one did not**. The existing `_tkinter` extension cannot find Tcl/Tk libraries. This previously unexercised slim-image limitation is explicitly open; no all-stdlib compatibility claim is made.

| Advisory group | Local evidence | Design consequence |
|---|---|---|
| Four util-linux mount/nsenter advisories (36 entries) | Tools exist; mount/umount have set-ID bits. Fixture denies privilege gain; fstab is unconfigured. libuuid is actually loaded by the fixture. | Exclude administrative tools from candidate. Retain required libraries; do not purge the entire source-package family. |
| ACL (1 entry) | libacl installed, not observed in the fixture's final process maps. | Determine dependency closure; absence from one snapshot is not proof of unreachability. |
| ncurses infocmp (4 entries) | infocmp exists; advisory identifies a CLI path. | Exclude CLI, preserve runtime libraries needed by retained Python extensions. |
| systemd-homed (2 entries) | Checked homed/homectl paths absent; installed source-family packages are libraries. | Record component-absence evidence; reassess against final candidate before any formal disposition. |
| Perl Archive::Tar (1 entry) | perl-base exists; Archive::Tar import fails in configured include paths. | Exclude Perl tooling; no blanket statement about future modules/images. |

The per-advisory JSON links to the primary Debian tracker and separates affected-path descriptions, observations and proposed actions. Examples: [mount helper issue](https://security-tracker.debian.org/tracker/CVE-2026-76642), [infocmp issue](https://security-tracker.debian.org/tracker/CVE-2025-69720), [systemd-homed issue](https://security-tracker.debian.org/tracker/CVE-2026-16742), [Archive::Tar issue](https://security-tracker.debian.org/tracker/CVE-2026-9538). These are scoped observations, not vulnerability waivers. All raw findings and severities remain intact; lower-severity entries have inventory coverage but have not received full semantic applicability review.

## Proposed candidate design

Build a separate final filesystem from the exact recorded input: Python 3.14.10, unchanged pinned application distributions, required native libraries and explicitly inventoried runtime data. Exclude shell/package-installation/admin tools and set-ID executables. Keep libuuid and other dependencies supported by evidence; do not copy only the files touched by one test. Dynamic loading, DNS/NSS, certificate trust, locale and timezone requirements need independent validation.

Retain per-file hashes, source package/version attribution and required licenses. Preserve original package inventory as provenance and distinguish retained files from excluded files. Do not remove package metadata merely to make a scanner report fewer findings. Compare scanner coverage to the retained-file inventory and record unresolved findings. Candidate rebuilds must use verified local IDs and must not install packages at runtime.

The current Tkinter/Tcl/Tk gap requires an explicit candidate support boundary: either exclude GUI support from the worker fixture or supply reviewed native dependencies. This is not permission to remove arbitrary stdlib modules from the future application. A shell-free design must also be reconciled with any future plugin/subprocess contract; the observed fixture cannot decide those requirements.

## Validation and next gate

The matrix has 164 rows, all matched to installed package versions; all eight High advisories have reviewed path notes. Eleven existing fixture checks passed. Native inventory reports 84 resolved entries and the one Tkinter gap without suppressing it. Collector and evidence hashes are included in the central readiness index. No exploit payload, user source script, service restart or production migration was run; the temporary probe container was removed.

Next: build the isolated minimal-runtime candidate from this design and test dependency completeness, prohibited-tool absence, boundary controls, TLS/CA/DNS/locale behavior and real Temporal/S3 integration. A promising scan is insufficient for adoption: relevant restart/persistence regressions, final-image applicability and package-provenance coverage must also pass. H01/H02/H03 and PostgreSQL/embedded-Go/Alpine portions of H04 remain separate open work. No risk acceptance or milestone transition occurred.

Artifacts: `docs/quality/runtime-candidates/python-path-review/` contains assessment.json, runtime-path-evidence.json, finding-path-matrix.json, high-advisory-review.json, minimal-runtime-design.json and the fixture report. Reproduce collection with `python tools/readiness/map-worker-os-findings.py`; advisory interpretation and design are reviewed artifacts, not automatically accepted by rerunning the collector.
