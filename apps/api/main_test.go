package main

import (
	"context"
	"encoding/json"
	"net/http"
	"net/http/httptest"
	"os"
	"path/filepath"
	"strings"
	"testing"
	"time"
)

type memoryStore struct {
	items     []json.RawMessage
	analysis  json.RawMessage
	discovery json.RawMessage
	plan      json.RawMessage
}

func (m *memoryStore) List(context.Context, string, int) (json.RawMessage, error) {
	return json.Marshal(map[string]any{"items": m.items})
}
func (m *memoryStore) Create(_ context.Context, b json.RawMessage) (json.RawMessage, error) {
	p := json.RawMessage(`{"id":"11111111-1111-1111-1111-111111111111","name":"Demo","source":{"kind":"local","location":"C:/demo"},"created_at":"2026-10-30T00:00:00Z","updated_at":"2026-10-30T00:00:00Z","workflow_status":"created","latest_analysis_id":null,"latest_plan_id":null,"latest_generation_id":null,"latest_validation_id":null}`)
	m.items = append(m.items, p)
	return p, nil
}
func (m *memoryStore) Get(context.Context, string) (json.RawMessage, error) { return m.items[0], nil }
func (m *memoryStore) SaveAnalysis(_ context.Context, value json.RawMessage) (json.RawMessage, error) {
	m.analysis = value
	return value, nil
}
func (m *memoryStore) GetAnalysis(context.Context, string) (json.RawMessage, error) {
	return m.analysis, nil
}
func (m *memoryStore) GetGraph(context.Context, string) (json.RawMessage, error) {
	return m.analysis, nil
}
func (m *memoryStore) SaveDiscovery(_ context.Context, _ string, value json.RawMessage) (json.RawMessage, error) {
	m.discovery = value
	return value, nil
}
func (m *memoryStore) GetCandidates(context.Context, string) (json.RawMessage, error) {
	return m.discovery, nil
}
func (m *memoryStore) GetRecommendation(context.Context, string) (json.RawMessage, error) {
	return m.discovery, nil
}
func (m *memoryStore) CreatePlan(_ context.Context, p json.RawMessage, _ []byte, _ string) (json.RawMessage, error) {
	m.plan = p
	return p, nil
}
func (m *memoryStore) GetPlan(context.Context, string) (json.RawMessage, error) { return m.plan, nil }
func (m *memoryStore) GetLatestPlan(context.Context, string) (json.RawMessage, error) {
	return m.plan, nil
}
func (m *memoryStore) ApprovePlan(context.Context, string, int, string, bool) (json.RawMessage, error) {
	return json.RawMessage(`{"status":"approved"}`), nil
}
func (m *memoryStore) AdjudicateCandidate(_ context.Context, _ string, review json.RawMessage) (json.RawMessage, error) {
	return review, nil
}
func testServer() *server {
	code := "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQ"
	return &server{store: &memoryStore{}, origin: "http://127.0.0.1:8080", actor: "11111111-1111-1111-1111-111111111111", tenant: "22222222-2222-2222-2222-222222222222", bootstrap: hashToken(code), bootstrapExpires: time.Now().Add(time.Minute), sessions: map[[32]byte]*session{}, now: time.Now}
}

func TestSnapshotDigestAndGraphAreDeterministic(t *testing.T) {
	root := t.TempDir()
	if err := os.MkdirAll(filepath.Join(root, "app", "api", "health"), 0755); err != nil {
		t.Fatal(err)
	}
	if err := os.MkdirAll(filepath.Join(root, "lib"), 0755); err != nil {
		t.Fatal(err)
	}
	if err := os.WriteFile(filepath.Join(root, "lib", "status.ts"), []byte("export const status = 'ok'\n"), 0644); err != nil {
		t.Fatal(err)
	}
	if err := os.WriteFile(filepath.Join(root, "app", "api", "health", "route.ts"), []byte("import { status } from '../../../lib/status'\nexport async function GET() { return Response.json({status}) }\n"), 0644); err != nil {
		t.Fatal(err)
	}
	a, err := acquireAndAnalyze("11111111-1111-1111-1111-111111111111", root)
	if err != nil {
		t.Fatal(err)
	}
	b, err := acquireAndAnalyze("11111111-1111-1111-1111-111111111111", root)
	if err != nil {
		t.Fatal(err)
	}
	if a.SourceDigest != b.SourceDigest {
		t.Fatal("snapshot digest changed")
	}
	if len(a.Nodes) != 3 || len(a.Edges) != 2 {
		t.Fatalf("unexpected graph nodes=%d edges=%d", len(a.Nodes), len(a.Edges))
	}
	if a.Nodes[2].Kind != "http_route" || a.Nodes[2].Label != "GET /api/health" {
		t.Fatalf("route not detected: %#v", a.Nodes[2])
	}
}

func TestSnapshotRejectsSymlink(t *testing.T) {
	root := t.TempDir()
	outside := t.TempDir()
	if err := os.WriteFile(filepath.Join(root, "index.ts"), []byte("export {}\n"), 0644); err != nil {
		t.Fatal(err)
	}
	if err := os.WriteFile(filepath.Join(outside, "secret.ts"), []byte("secret\n"), 0644); err != nil {
		t.Fatal(err)
	}
	if err := os.Symlink(filepath.Join(outside, "secret.ts"), filepath.Join(root, "linked.ts")); err != nil {
		t.Skipf("symlink unavailable: %v", err)
	}
	if _, err := acquireAndAnalyze("11111111-1111-1111-1111-111111111111", root); err == nil || !strings.Contains(err.Error(), "symbolic links") {
		t.Fatalf("expected symlink rejection, got %v", err)
	}
}

func TestRouteAuthorityExcludesCommentsAndStrings(t *testing.T) {
	root := t.TempDir()
	target := filepath.Join(root, "app", "api", "health", "route.ts")
	if err := os.MkdirAll(filepath.Dir(target), 0755); err != nil {
		t.Fatal(err)
	}
	source := "// export async function GET() {}\n/* export const POST = () => {} */\nconst text = 'export async function PUT() {}'\nconst template = `export const DELETE = () => {}`\nconst pattern = /export async function HEAD\\(\\)/\nexport const marker = true\n"
	if err := os.WriteFile(target, []byte(source), 0600); err != nil {
		t.Fatal(err)
	}
	analysis, err := acquireAndAnalyze("11111111-1111-1111-1111-111111111111", root)
	if err != nil {
		t.Fatal(err)
	}
	for _, node := range analysis.Nodes {
		if node.Kind == "http_route" {
			t.Fatalf("non-code text created route authority: %s", node.Label)
		}
	}
}

func TestNextRouteIdentityConventions(t *testing.T) {
	cases := map[string]string{
		"src/app/api/health/route.ts":        "GET /api/health",
		"app/(internal)/api/health/route.ts": "GET /api/health",
		"src/app/(v1)/api/[id]/route.ts":     "GET /api/[id]",
	}
	for file, expected := range cases {
		t.Run(file, func(t *testing.T) {
			root := t.TempDir()
			target := filepath.Join(root, filepath.FromSlash(file))
			if err := os.MkdirAll(filepath.Dir(target), 0755); err != nil {
				t.Fatal(err)
			}
			if err := os.WriteFile(target, []byte("export async function GET() {}\n"), 0600); err != nil {
				t.Fatal(err)
			}
			analysis, err := acquireAndAnalyze("11111111-1111-1111-1111-111111111111", root)
			if err != nil {
				t.Fatal(err)
			}
			found := ""
			for _, node := range analysis.Nodes {
				if node.Kind == "http_route" {
					found = node.Label
				}
			}
			if found != expected {
				t.Fatalf("route identity %q, want %q", found, expected)
			}
		})
	}
}

func TestSnapshotExcludesLocalAndIgnoredSources(t *testing.T) {
	root := t.TempDir()
	files := map[string]string{
		"app/api/health/route.ts": "export async function GET() {}\n",
		".local/credentials.json": `{"secret":"synthetic"}`,
		"private/ignored.json":    `{"secret":"synthetic"}`,
		".gitignore":              ".local/\nprivate/\n",
	}
	for name, content := range files {
		target := filepath.Join(root, filepath.FromSlash(name))
		if err := os.MkdirAll(filepath.Dir(target), 0755); err != nil {
			t.Fatal(err)
		}
		if err := os.WriteFile(target, []byte(content), 0600); err != nil {
			t.Fatal(err)
		}
	}
	snapshot, _, _, err := readSnapshot(root)
	if err != nil {
		t.Fatal(err)
	}
	for _, file := range snapshot {
		if strings.HasPrefix(file.path, ".local/") || strings.HasPrefix(file.path, "private/") {
			t.Fatalf("ignored source acquired: %s", file.path)
		}
	}
}

func TestCandidateDiscoveryFailsClosed(t *testing.T) {
	digest := strings.Repeat("a", 64)
	nodes := []graphNode{
		{ID: "11111111-1111-4111-8111-111111111111", Kind: "http_route", Label: "GET /api/health", Evidence: []evidence{{Path: "app/api/health/route.ts", SourceDigest: strings.Repeat("b", 64), LineStart: 2, LineEnd: 2, DetectorVersion: analyzerVersion}}},
		{ID: "22222222-2222-4222-8222-222222222222", Kind: "http_route", Label: "GET /api/users", Evidence: []evidence{{Path: "app/api/users/route.ts", SourceDigest: strings.Repeat("c", 64), LineStart: 4, LineEnd: 4, DetectorVersion: analyzerVersion}}},
		{ID: "33333333-3333-4333-8333-333333333333", Kind: "http_route", Label: "POST /api/users", Evidence: []evidence{{Path: "app/api/users/route.ts", SourceDigest: strings.Repeat("c", 64), LineStart: 9, LineEnd: 9, DetectorVersion: analyzerVersion}}},
	}
	doc := discoverCandidates("aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa", digest, nodes)
	if len(doc.Candidates) != 3 {
		t.Fatalf("candidates=%d", len(doc.Candidates))
	}
	if doc.Candidates[0].Eligibility != "unknown" || doc.Candidates[1].Eligibility != "unknown" || doc.Candidates[2].Eligibility != "blocked" {
		t.Fatalf("unexpected eligibility: %#v", doc.Candidates)
	}
	if doc.Candidates[2].OperationType != "write" || len(doc.Candidates[2].SideEffects) == 0 {
		t.Fatal("write route did not fail closed")
	}
	if doc.Recommendation.SupportedGeneration || doc.Recommendation.RecommendedType != "none" || len(doc.Recommendation.CandidateIDs) != 0 {
		t.Fatal("recommendation boundary")
	}
	for _, item := range doc.Candidates {
		if item.Evidence[0].SourceDigest != digest {
			t.Fatal("candidate evidence not snapshot-bound")
		}
	}
}

func TestPlanHashStableAndRejectsUnresolvedCandidate(t *testing.T) {
	analysis := analysisDocument{ID: "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa", SnapshotID: "bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb", SourceDigest: strings.Repeat("a", 64), AnalyzerVersions: []map[string]any{{"id": "typescript-next", "version": analyzerVersion}}}
	rec := recommendationDocument{ID: "cccccccc-cccc-4ccc-8ccc-cccccccccccc", Version: 1, Risks: []string{"review"}, RequiredReviews: []string{"security"}}
	item := candidate{ID: "dddddddd-dddd-4ddd-8ddd-dddddddddddd", OperationType: "read", Eligibility: "allowed", RequiredScopes: []string{}, InputSchema: map[string]any{"type": "object"}, OutputSchema: map[string]any{"type": "object"}, DomainServiceReference: "verified:health-status", Detector: map[string]any{"id": "route-candidate-detector", "version": candidateDetectorVersion}, Evidence: []evidence{{DetectorVersion: candidateDetectorVersion}}, Provenance: "deterministic"}
	a, bytesA, err := buildPlan(analysis, rec, []candidate{item}, []string{item.ID})
	if err != nil {
		t.Fatal(err)
	}
	b, bytesB, err := buildPlan(analysis, rec, []candidate{item}, []string{item.ID})
	if err != nil {
		t.Fatal(err)
	}
	if a.ContentHash != b.ContentHash || string(bytesA) != string(bytesB) {
		t.Fatal("canonical plan hash changed")
	}
	item.DomainServiceReference = "unresolved:GET /api/health"
	if _, _, err = buildPlan(analysis, rec, []candidate{item}, []string{item.ID}); err == nil {
		t.Fatal("unresolved candidate entered plan")
	}
	item.DomainServiceReference = "verified:health-status"
	item.Detector["version"] = "route-candidate-deterministic-v1"
	if _, _, err = buildPlan(analysis, rec, []candidate{item}, []string{item.ID}); err == nil {
		t.Fatal("legacy candidate entered plan")
	}
}
func exchange(t *testing.T, s *server) (*http.Cookie, string) {
	t.Helper()
	body := `{"one_time_code":"abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQ","browser_nonce":"abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQ"}`
	r := httptest.NewRequest("POST", "http://x/v1/local-session/exchange", strings.NewReader(body))
	r.Header.Set("Origin", s.origin)
	w := httptest.NewRecorder()
	s.exchange(w, r)
	if w.Code != 200 {
		t.Fatalf("exchange %d: %s", w.Code, w.Body.String())
	}
	var v struct {
		CSRF string `json:"csrf_token"`
	}
	json.Unmarshal(w.Body.Bytes(), &v)
	return w.Result().Cookies()[0], v.CSRF
}
func TestBootstrapReplayAndOrigin(t *testing.T) {
	s := testServer()
	cookie, _ := exchange(t, s)
	if !cookie.HttpOnly || cookie.SameSite != http.SameSiteStrictMode {
		t.Fatal("cookie flags")
	}
	r := httptest.NewRequest("POST", "http://x/v1/local-session/exchange", strings.NewReader(`{}`))
	r.Header.Set("Origin", s.origin)
	w := httptest.NewRecorder()
	s.exchange(w, r)
	if w.Code != 400 {
		t.Fatal(w.Code)
	}
	s2 := testServer()
	r = httptest.NewRequest("POST", "http://x/v1/local-session/exchange", strings.NewReader(`{}`))
	r.Header.Set("Origin", "http://evil.invalid")
	w = httptest.NewRecorder()
	s2.exchange(w, r)
	if w.Code != 403 {
		t.Fatal(w.Code)
	}
}
func TestProjectMutationRequiresCSRF(t *testing.T) {
	s := testServer()
	cookie, csrf := exchange(t, s)
	body := `{"name":"Demo","source":{"kind":"local","location":"C:/demo"}}`
	r := httptest.NewRequest("POST", "http://x/v1/projects", strings.NewReader(body))
	r.AddCookie(cookie)
	r.Header.Set("Origin", s.origin)
	w := httptest.NewRecorder()
	s.projects(w, r)
	if w.Code != 403 {
		t.Fatal(w.Code)
	}
	r = httptest.NewRequest("POST", "http://x/v1/projects", strings.NewReader(body))
	r.AddCookie(cookie)
	r.Header.Set("Origin", s.origin)
	r.Header.Set("X-CSRF-Token", csrf)
	w = httptest.NewRecorder()
	s.projects(w, r)
	if w.Code != 201 {
		t.Fatalf("%d %s", w.Code, w.Body.String())
	}
}
