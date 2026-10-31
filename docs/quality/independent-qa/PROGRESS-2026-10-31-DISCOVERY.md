# Independent QA: Architecture Explorer and candidate discovery

Date: 31 October 2026, Asia/Calcutta. Completed candidate slice: Software Engineer turn `01a19173-c7bd-7880-88f7-2696da8f9b31`; preceding Architecture Explorer implementation also reviewed. Exact-plan/approval slice is currently in progress and is excluded from this verdict.

**Verdict: HOLD. Four adversarial assertions failed; generation-lock assertion passed.** Tests ran against frozen copies of the delivered `analyzer.go` and `candidates.go` in `work/qa-discovery`, not against a modified product module. No application/database records or running services were changed by these checks. This follow-up is code-level verification, not a new manual browser acceptance pass.

## DISC-01 — P1: A commented-out handler becomes an allowed candidate

Fixture: `app/api/health/route.ts` contains only a commented-out `export async function GET()` and an unrelated exported marker. Actual: the regex analyzer emits a real HTTP route, and discovery marks it `allowed`, `public`, with a resolved `builtin:health-status` mapping. There is no actual handler. Regex matches in comments/strings must not become executable capability authority.

Expected: parse syntax and confirm a real supported route export; unresolved or unverified mappings remain review-only. Naming a path health/status does not establish its actual authorization, side effects or domain mapping. The current recommendation generation lock passed and limits present impact, but this faulty candidate authority must not feed later plan/generation admission as verified source truth. No code was executed by the synthetic handler.

## DISC-02 — P2: Valid Next.js layouts produce incorrect route identities

Two failing cases:

- `src/app/api/health/route.ts` produces `GET /src/app/api/health` instead of `GET /api/health`.
- `app/(internal)/api/health/route.ts` produces `GET /(internal)/api/health` instead of `GET /api/health`.

These incorrect URLs propagate into graph labels, finding identities and candidate review. Next.js supports an optional [src application directory](https://nextjs.org/docs/app/api-reference/file-conventions/src-folder), and [route groups](https://nextjs.org/docs/app/api-reference/file-conventions/route-groups) are excluded from URL paths. Implement the supported routing conventions or emit explicit unsupported diagnostics; do not present fabricated URLs with confidence 1.0. Tests cover source-derived identities only, not an independently launched Next.js fixture server.

## DISC-03 — P1: Ignored local credential files enter source acquisition

Fixture: a project includes `.gitignore` excluding `.local/`, a valid route, and `.local/credentials.json` containing a synthetic secret canary. Actual: `readSnapshot` acquires `.local/credentials.json` and returns its raw bytes as a source file. The static ignore-directory list neither honors this ignore rule nor excludes `.local`.

Expected: apply the approved snapshot ignore/secret boundaries before reading sensitive files; host-local credentials must stay outside snapshots. This matters directly for the application's own `.local` credential storage. This test proves acquisition of synthetic secret bytes, **not** external transmission, persisted raw secret contents or actual credential theft. No real credentials were read by this test. Review excluded roots, configured ignore rules and secret-bearing JSON before permitting real repository intake.

## Evidence and reproduction

- `discovery-regression_test.go`: five independent adversarial/positive assertions.
- `discovery-regression-results.txt`: Go output, four failed and one passed; test exit code 1.
- `discovery-regression-inputs.json`: SHA-256 of frozen analyzer/candidate code and QA test.

From `work/qa-discovery`, using the pinned project Go runtime:

```powershell
Copy-Item ../../docs/quality/independent-qa/discovery-regression_test.go qa_test.go
../../work/runtimes/go1.27.3/go/bin/go.exe test -v analyzer.go candidates.go qa_test.go
```

The frozen source copies were taken from the completed implementation before running tests. Future code changes require copying reviewed sources again and refreshing fingerprints. The existing original unit suite was inspected, not rerun or counted as independent assertions here. The engineer's migration/API end-to-end reports remain scoped engineer evidence; this run does not reconfirm tenant authorization or migration correctness.

## Prior findings and boundaries

QA-01/QA-02's original foundation fixes are not reopened by these analyzer tests. Their full regression against migrations beyond 009 has not been established in this run. Earlier MAN-01 has a partial code change (rows are now buttons), but handlers only switch to Architecture Explorer without passing the clicked project identity; manual closure is not established. Search-empty/totals, input semantics and design findings remain unverified as fixed.

Keep source/candidate acceptance open and fix DISC-01–03 before trusting the new classifications for execution. Generation is currently locked; no existing server or product implementation was modified by QA. Do not infer approval of the in-progress plan slice from this report.
