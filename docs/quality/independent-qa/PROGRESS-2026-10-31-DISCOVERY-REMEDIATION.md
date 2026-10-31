# Independent remediation re-review

Date: 31 October 2026, Asia/Calcutta. Reviewed completed Software Engineer turn `01a19185-ff3b-72b3-8a72-66ca9dc5520f`. The subsequent operator-adjudication implementation is in progress and is not signed off here.

## Result: six passed, one failed — HOLD remains

Fresh copies of the analyzer and discovery sources were tested with the original five QA assertions plus two additional adversarial assertions. The original five now pass. A regex-literal-after-return fixture also passes (no phantom route). A broader ignore-rule safety assertion fails.

Confirmed fixes:

- Comment-only exports no longer produce candidates in the supplied fixture.
- `src/app` and route groups produce the expected source-derived URLs.
- `.local/credentials.json` is excluded in the supplied fixture.
- Recommendation generation remains locked.
- A fake export within a returned regex literal does not create a route in the additional fixture.

## Outstanding DISC-03 extension — P1: unsupported ignore rules silently permit secret acquisition

Synthetic fixture: `.gitignore` contains `**/secrets.json`; `config/secrets.json` contains a fake secret canary; the project also contains a valid route. Actual: `readSnapshot` returns `config/secrets.json` with its raw content. The bounded ignore parser explicitly skips any rule containing `**` and continues acquisition without an error or diagnostic.

Expected: honor the exclusion or fail closed with an actionable unsupported-ignore-pattern error before acquiring the affected source. A deliberately limited ignore interpreter must not silently convert exclusion rules into permission to read secret-bearing files. This is a broader instance of DISC-03: the hardcoded `.local` exclusion is fixed, but general ignore-boundary acceptance remains open. The failure proves only synthetic in-memory acquisition; it does not prove actual secret exfiltration or persisted raw secrets.

## Evidence and provenance

- `discovery-remediation-expanded-results.txt`: seven assertions, six passed and one failed, exit code 1.
- `discovery-remediation-extra_test.go`: two added adversarial fixtures.
- `discovery-remediation-inputs.json`: frozen source fingerprints.
- Original unchanged regression file: `discovery-regression_test.go`.

The frozen analyzer SHA-256 is `8bd69c31687240c35650b3fb7daf32c21cfb6bd1796cd154792d393a25762864`, matching the engineer's completed remediation report. Candidate source was already being changed for the subsequent adjudication slice: frozen hash `375c3d2821d29c8d777e5a3e118e967c0652c41ad7ee493043972516fc8ee0e1`. Thus this is not a claim of binary-level sign-off for that newer candidate slice. The failed ignore-boundary assertion depends only on the fingerprint-matched completed analyzer.

Reproduce in `work/qa-discovery-remediation` after copying the reviewed sources and both QA test files there:

```powershell
../../work/runtimes/go1.27.3/go/bin/go.exe test -p 1 -timeout 30s -v analyzer.go candidates.go qa_test.go extra_test.go
```

QA added no product implementation changes and touched no live database or application service. No new manual browser pass or complete migration-chain regression was performed. Prior manual UI findings, QA-01/QA-02 current-chain acceptance, and the in-progress adjudication/approval work retain their independent verification requirements. Keep real-source intake and execution acceptance on HOLD until unsupported ignore rules fail safely and the new slices are independently verified.
