# QA follow-up: runtime audit and Python OS candidates

Date: 30 October 2026, Asia/Calcutta. Latest completed step verified: Software Engineer turn `01a18d42-18da-73d3-9373-da385e3099c3`. Also reviewed the completed initial runtime audit and tooling-free Python candidate step. The subsequent package/execution-path/minimal-runtime investigation is in progress and is excluded from acceptance here.

## Independently executed verification

- Reran the exact recorded Trixie-upgrade and Bookworm candidate image IDs in new controlled containers. Each passed 11 Python/parser/Temporal runtime checks and 14 Docker boundary/resource/deadline/cleanup checks: **50 passing entries** total.
- Confirmed each candidate's installed distribution inventory and absence of pip/ensurepip/wheel directories match its recorded assessment.
- Recounted candidate raw scanner reports and verified their SHA-256 hashes. Trixie retains 164 package/advisory entries, including 44 High. Bookworm retains 243, including 2 Critical and 59 High.
- Recounted and hash-checked all eight initial raw image reports against the audit index. All match the recorded summaries. Independently recounted both tooling-free Python reports: 164 entries each and zero reported language-package findings.
- Confirmed the adopted worker tag still resolves to its original image ID. No running service was restarted and no image was adopted or rebuilt by QA. Test containers and temporary boundary fixtures were removed.

Raw QA evidence: `os-candidates/verification.json`, per-candidate runtime/boundary reports under `os-candidates/`, and `scan-evidence-verification.json`.

Reproduce with existing local candidate images and Docker access:

```powershell
python -X utf8 tools/fixtures/m03/qa-os-candidates.py
python -X utf8 tools/fixtures/m03/qa-scan-evidence.py
```

## Verdict and limits

The completed OS-candidate runtime claims reproduce. **Security acceptance remains HOLD.** The initial audit's successful collection and passing runtime/isolation checks do not clear reported advisories. The engineer correctly leaves H04/M0.3 open and adopts neither OS candidate. Counts describe scanner package/advisory occurrences; they are not unique exploits or demonstrated reachability.

This QA run reconciles recorded vulnerability evidence; it does not perform a fresh scan, new advisory lookup, vendor applicability review or signature verification. The earlier tooling-free service workflow/storage report and package/core runtime audits were reviewed, but their network queries and service regression suite were not independently repeated. The fresh 50 entries above cover only the two worker OS candidates, not service restart/persistence or the entire runtime gate.

No new failing assertion was found in this verification. Existing H01–H04 and the documented Windows test-encoding issue remain separate open obligations. Database migration files were unchanged since the previous QA run; QA-01/QA-02 did not need another database rerun for this image-only step. Actual source intake, browser API/session, plugin validation, worker/object truth, recovery and visual/product acceptance remain pending.
