# Minimal worker/service runtime candidate

Recorded 30 October 2026. Built and validated an isolated candidate; **not adopted**. H04 and M0.3 remain OPEN.

Candidate image: `sha256:dc612ae7bb151a095b3848d9cbf45c17311514267c39950d3121e223ff52f797`. Input: `sha256:bd320540b91dabf4f7fabe7bef85aefea4745d256895bbd6b2261c562db22049`. The existing tooling-free service fixture was used so one candidate could exercise both worker/parser and real workflow/storage behavior. Python remains 3.14.10; all 14 application distribution versions match that input.

## Implemented packaging

The build assembles a fresh filesystem from Python, pinned application packages, native dependencies, NSS/locale/timezone data, certificate trust and identity files. It retains required libuuid and other libraries instead of deleting entire source-package families. Shells, package installers, mount/nsenter/login utilities, Perl and ncurses CLI tools are excluded. Retained files have set-ID bits removed and an exhaustive content-hash/symlink manifest. Original license documents and package ownership/version records remain available as provenance.

Tkinter/IDLE and compiler configuration/object artifacts are explicitly excluded from this fixture candidate. It does not support GUI programs, compiling native packages or shell-based plugins. This is a candidate support boundary, not an approved restriction on future product plugins. The baseline image is unchanged.

## Validation

**50 check entries passed**: 14 minimal-runtime checks, 2 service DNS checks, 11 parser/Temporal sandbox checks, 14 isolation/resource/deadline checks and 9 real Temporal/S3 checks. All **82 retained Python native libraries loaded**; the manifest verifies 6740 retained file/symlink entries. Identity lookup, UTF-8 locale, timezone and system certificate store checks passed. Controlled loopback TLS accepted an explicitly trusted test certificate and rejected both an untrusted issuer and hostname mismatch. Test keys were generated for the invocation and existed only in temporary container storage.

Temporal and storage DNS resolution worked on the existing local network. A real workflow/activity stored and retrieved unique S3 fixture data, rejected incorrect credentials and verified bytes/digests. Fresh-process readback and object cleanup passed. Test containers were removed. Completed fixture workflow history remains subject to normal local retention. Existing services were not restarted; restart/persistence regression is still pending before adoption.

## Scan coverage and remaining findings

The final unsuppressed scan recognizes Debian 13.7 and inventories 87 original Debian package records, 14 Python distributions and 367 Rust dependency entries. It still reports **164 OS findings: 44 High, 58 Medium, 61 Low and 1 Unknown**, with zero language-package findings. These are repeated package/advisory occurrences, not confirmed reachable exploits.

Package records intentionally remain conservative: they describe the input packages even where executable payloads were excluded. `package-provenance-coverage.json` intersects their ownership lists with the final retained-file manifest. Every scanner-reported package maps to that evidence. Retained libraries can keep source-package findings after associated CLI tools are removed. No package metadata was deleted to improve a score; no finding was suppressed or waived.

An intermediate candidate returned zero findings while its OS was unrecognized. That result is retained as **invalid coverage evidence**, not a clean scan. Restoring `/etc/debian_version` corrected detection; the [Trivy 0.76.1 Debian analyzer](https://raw.githubusercontent.com/aquasecurity/trivy/v0.76.1/pkg/fanal/analyzer/os/debian/debian.go) requires that file. The collector now rejects an unrecognized OS. Another early check caught missing OpenSSL default certificate-directory aliases; those were restored and the complete checks rerun. A build check also excluded a compiler object from the runtime-only filesystem.

## Artifacts, reproduction and next gate

Run `python tools/readiness/evaluate-minimal-runtime.py`, then `python tools/readiness/minimal-runtime-provenance.py`. The existing exact input image, scanner/database and local service fixture configuration are required; the host collector uses cryptography to generate disposable test certificates. It never installs packages in the runtime. `build-minimal-root.py` implements assembly and `check-minimal-runtime.py` implements the controlled candidate tests.

Evidence under `docs/quality/runtime-candidates/minimal-runtime/` includes generated Dockerfile/build log, final image ID, retained-file/native dependency manifests, package coverage, raw scan and all test reports. The central readiness index hashes those artifacts and source files. Historical invalid scan evidence is clearly marked and separated.

Next: evaluate each advisory against the final retained files, document any scoped non-applicability with primary-source evidence, and run isolated service restart/persistence regressions before considering adoption. Lower-severity findings and other PostgreSQL/Go/Alpine images remain open work. Candidate packaging is validated for these fixtures only; dynamic loading, arbitrary plugins and real source acquisition are not universally certified. H01/H02/H03 remain open. No approved pin, running service configuration, design screen, risk acceptance or milestone changed.
