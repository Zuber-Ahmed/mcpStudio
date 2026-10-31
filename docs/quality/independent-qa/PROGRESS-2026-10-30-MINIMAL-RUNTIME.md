# QA follow-up: minimal runtime and restart review

Date: 30 October 2026, Asia/Calcutta. Completed step reviewed: Software Engineer turn `01a18d55-1207-7502-89ba-5c43b6308f4f`, plus its preceding minimal-runtime packaging and path-review steps. Candidate image: `sha256:dc612ae7bb151a095b3848d9cbf45c17311514267c39950d3121e223ff52f797`.

## Independently verified

The exact candidate passed **25 fresh runtime/boundary checks**: 11 parser/Python/Temporal readiness entries and 14 Docker isolation/resource/deadline/cleanup entries. A fresh component probe verified content hashes for the 6740-entry retained-file manifest and checked that mount/umount/nsenter/infocmp/systemd-homed/homectl/Perl and the reported libacl/libmount/Archive::Tar payloads are excluded. This verifies packaging evidence; it is not an independent vulnerability applicability determination.

The retained raw scan still recognizes Debian and reports 164 entries: 44 High, 58 Medium, 61 Low and one Unknown. Its hash matches the candidate assessment. No new scan, severity change or suppression was performed by QA.

The recorded isolated restart assessment reports completion, seven lifecycle/isolation checks, 11 service checks, removed disposable resources and identical original-stack before/after snapshots. Those evidence assertions were reviewed, including snapshot equality; the service restart fixture was **not independently rerun**. TLS, DNS, 82-native-library loading and the earlier full 50-entry candidate validation were reviewed as engineer evidence rather than claimed as fresh QA tests.

Fresh QA evidence is stored under `minimal-runtime/verification.json` and its runtime/boundary reports. Reproduce with existing image and Docker access:

```powershell
python -X utf8 tools/fixtures/m03/qa-minimal-runtime.py
```

## Acceptance and current scope

No new failing assertion was found. The exact candidate's packaging checks reproduce, while H04 remains open. The engineer's eight advisory dispositions are scoped component-exclusion interpretations, not removal of raw findings, an accepted-risk decision or a globally clean image. Other severities, server images and actual product execution still need their stated reviews.

The human has explicitly redirected the Software Engineer toward a runnable application slice: session bootstrap, PostgreSQL-backed project create/list/get and Dashboard/Project Setup. That work is currently in progress, including dependency/build repair, and is **not yet verified**. This instruction supplies scope for product development despite the open readiness holds; QA will assess the completed application on its actual behavior and exposure rather than treating the earlier milestone boundary as a new approval requirement. No product code or application service was changed by this QA run.

QA-01/QA-02 remain resolved in the nine-migration foundation chain, which has not changed here. The Windows test-encoding issue and remaining runtime/security obligations remain open. Product UI/API acceptance awaits completion of the runnable slice.
