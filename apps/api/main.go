package main

import (
	"context"
	"crypto/rand"
	"crypto/sha256"
	"crypto/subtle"
	"encoding/base64"
	"encoding/hex"
	"encoding/json"
	"errors"
	"fmt"
	"io"
	"log/slog"
	"net"
	"net/http"
	"os"
	"path/filepath"
	"strconv"
	"strings"
	"sync"
	"time"

	"github.com/jackc/pgx/v5/pgxpool"
)

const cookieName = "mcpstudio_session"

type projectStore interface {
	List(context.Context, string, int) (json.RawMessage, error)
	Create(context.Context, json.RawMessage) (json.RawMessage, error)
	Get(context.Context, string) (json.RawMessage, error)
	SaveAnalysis(context.Context, json.RawMessage) (json.RawMessage, error)
	GetAnalysis(context.Context, string) (json.RawMessage, error)
	GetGraph(context.Context, string) (json.RawMessage, error)
	SaveDiscovery(context.Context, string, json.RawMessage) (json.RawMessage, error)
	GetCandidates(context.Context, string) (json.RawMessage, error)
	GetRecommendation(context.Context, string) (json.RawMessage, error)
	CreatePlan(context.Context, json.RawMessage, []byte, string) (json.RawMessage, error)
	GetPlan(context.Context, string) (json.RawMessage, error)
	GetLatestPlan(context.Context, string) (json.RawMessage, error)
	ApprovePlan(context.Context, string, int, string, bool) (json.RawMessage, error)
	AdjudicateCandidate(context.Context, string, json.RawMessage) (json.RawMessage, error)
}

type postgresStore struct{ pool *pgxpool.Pool }

func (s postgresStore) List(ctx context.Context, q string, limit int) (json.RawMessage, error) {
	var b []byte
	err := s.pool.QueryRow(ctx, "select studio_admission.backend_list_projects($1,$2)", q, limit).Scan(&b)
	return b, err
}
func (s postgresStore) Create(ctx context.Context, b json.RawMessage) (json.RawMessage, error) {
	var in struct {
		Name   string          `json:"name"`
		Source json.RawMessage `json:"source"`
	}
	if err := json.Unmarshal(b, &in); err != nil {
		return nil, err
	}
	var out []byte
	err := s.pool.QueryRow(ctx, "select studio_admission.backend_create_project($1,$2::jsonb)", in.Name, in.Source).Scan(&out)
	return out, err
}
func (s postgresStore) Get(ctx context.Context, id string) (json.RawMessage, error) {
	var out []byte
	err := s.pool.QueryRow(ctx, "select studio_admission.backend_get_project($1::uuid)", id).Scan(&out)
	return out, err
}
func (s postgresStore) SaveAnalysis(ctx context.Context, payload json.RawMessage) (json.RawMessage, error) {
	var out []byte
	err := s.pool.QueryRow(ctx, "select studio_admission.backend_store_analysis($1::jsonb)", payload).Scan(&out)
	return out, err
}
func (s postgresStore) GetAnalysis(ctx context.Context, id string) (json.RawMessage, error) {
	var out []byte
	err := s.pool.QueryRow(ctx, "select studio_admission.backend_get_analysis($1::uuid)", id).Scan(&out)
	return out, err
}
func (s postgresStore) GetGraph(ctx context.Context, id string) (json.RawMessage, error) {
	var out []byte
	err := s.pool.QueryRow(ctx, "select studio_admission.backend_get_analysis_graph($1::uuid)", id).Scan(&out)
	return out, err
}
func (s postgresStore) SaveDiscovery(ctx context.Context, id string, payload json.RawMessage) (json.RawMessage, error) {
	var out []byte
	err := s.pool.QueryRow(ctx, "select studio_admission.backend_store_discovery($1::uuid,$2::jsonb)", id, payload).Scan(&out)
	return out, err
}
func (s postgresStore) GetCandidates(ctx context.Context, id string) (json.RawMessage, error) {
	var out []byte
	err := s.pool.QueryRow(ctx, "select studio_admission.backend_get_candidates($1::uuid)", id).Scan(&out)
	return out, err
}
func (s postgresStore) GetRecommendation(ctx context.Context, id string) (json.RawMessage, error) {
	var out []byte
	err := s.pool.QueryRow(ctx, "select studio_admission.backend_get_recommendation($1::uuid)", id).Scan(&out)
	return out, err
}
func (s postgresStore) CreatePlan(ctx context.Context, payload json.RawMessage, canonical []byte, hash string) (json.RawMessage, error) {
	var out []byte
	err := s.pool.QueryRow(ctx, "select studio_admission.backend_create_exact_plan($1::jsonb,$2::bytea,$3)", payload, canonical, hash).Scan(&out)
	return out, err
}
func (s postgresStore) GetPlan(ctx context.Context, id string) (json.RawMessage, error) {
	var out []byte
	err := s.pool.QueryRow(ctx, "select studio_admission.backend_plan_document($1::uuid)", id).Scan(&out)
	return out, err
}
func (s postgresStore) GetLatestPlan(ctx context.Context, id string) (json.RawMessage, error) {
	var out []byte
	err := s.pool.QueryRow(ctx, "select studio_admission.backend_latest_plan($1::uuid)", id).Scan(&out)
	return out, err
}
func (s postgresStore) ApprovePlan(ctx context.Context, id string, version int, hash string, security bool) (json.RawMessage, error) {
	var out []byte
	err := s.pool.QueryRow(ctx, "select studio_admission.backend_approve_exact_plan($1::uuid,$2,$3,$4)", id, version, hash, security).Scan(&out)
	return out, err
}
func (s postgresStore) AdjudicateCandidate(ctx context.Context, id string, review json.RawMessage) (json.RawMessage, error) {
	var out []byte
	err := s.pool.QueryRow(ctx, "select studio_admission.backend_adjudicate_candidate($1::uuid,$2::jsonb)", id, review).Scan(&out)
	return out, err
}

type session struct {
	tokenHash, csrf string
	created, last   time.Time
}
type server struct {
	store            projectStore
	origin           string
	actor, tenant    string
	bootstrap        [32]byte
	bootstrapExpires time.Time
	mu               sync.Mutex
	used             bool
	sessions         map[[32]byte]*session
	now              func() time.Time
}

func randomToken() string {
	b := make([]byte, 32)
	if _, err := rand.Read(b); err != nil {
		panic(err)
	}
	return base64.RawURLEncoding.EncodeToString(b)
}
func hashToken(v string) [32]byte { return sha256.Sum256([]byte(v)) }
func requestID() *string          { v := randomToken()[:16]; return &v }
func writeJSON(w http.ResponseWriter, status int, v any) {
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(status)
	_ = json.NewEncoder(w).Encode(v)
}
func fail(w http.ResponseWriter, status int, code, msg string) {
	writeJSON(w, status, map[string]any{"code": code, "message": msg, "request_id": *requestID()})
}
func strictJSON(r *http.Request, dst any) error {
	d := json.NewDecoder(io.LimitReader(r.Body, 1<<20))
	d.DisallowUnknownFields()
	if err := d.Decode(dst); err != nil {
		return err
	}
	if d.Decode(&struct{}{}) == nil {
		return errors.New("multiple JSON values")
	}
	return nil
}
func (s *server) exactOrigin(r *http.Request) bool { return r.Header.Get("Origin") == s.origin }
func (s *server) authenticate(r *http.Request) (*session, bool) {
	c, err := r.Cookie(cookieName)
	if err != nil {
		return nil, false
	}
	key := hashToken(c.Value)
	s.mu.Lock()
	defer s.mu.Unlock()
	item, ok := s.sessions[key]
	if !ok {
		return nil, false
	}
	now := s.now()
	if now.Sub(item.last) > 30*time.Minute || now.Sub(item.created) > 8*time.Hour {
		delete(s.sessions, key)
		return nil, false
	}
	item.last = now
	return item, true
}
func (s *server) authorize(w http.ResponseWriter, r *http.Request, mutation bool) (*session, bool) {
	item, ok := s.authenticate(r)
	if !ok {
		fail(w, 401, "authentication_required", "Local session required")
		return nil, false
	}
	if mutation && (!s.exactOrigin(r) || subtle.ConstantTimeCompare([]byte(r.Header.Get("X-CSRF-Token")), []byte(item.csrf)) != 1) {
		fail(w, 403, "request_forbidden", "Exact origin and CSRF token required")
		return nil, false
	}
	return item, true
}
func (s *server) sessionResponse(item *session) map[string]any {
	return map[string]any{"actor_id": s.actor, "tenant_id": s.tenant, "csrf_token": item.csrf, "expires_at": item.created.Add(8 * time.Hour).UTC().Format(time.RFC3339), "idle_timeout_seconds": 1800, "absolute_timeout_seconds": 28800}
}
func (s *server) exchange(w http.ResponseWriter, r *http.Request) {
	if r.Method != "POST" {
		fail(w, 405, "method_not_allowed", "POST required")
		return
	}
	if !s.exactOrigin(r) {
		fail(w, 403, "request_forbidden", "Exact local origin required")
		return
	}
	var in struct {
		Code  string `json:"one_time_code"`
		Nonce string `json:"browser_nonce"`
	}
	if strictJSON(r, &in) != nil || len(in.Nonce) != 43 {
		fail(w, 400, "invalid_request", "Invalid bootstrap request")
		return
	}
	provided := hashToken(in.Code)
	s.mu.Lock()
	defer s.mu.Unlock()
	if s.used || s.now().After(s.bootstrapExpires) || subtle.ConstantTimeCompare(provided[:], s.bootstrap[:]) != 1 {
		fail(w, 401, "authentication_required", "Bootstrap code invalid, expired or used")
		return
	}
	s.used = true
	token := randomToken()
	tokenHash := hashToken(token)
	item := &session{tokenHash: hex.EncodeToString(tokenHash[:]), csrf: randomToken(), created: s.now(), last: s.now()}
	s.sessions[tokenHash] = item
	http.SetCookie(w, &http.Cookie{Name: cookieName, Value: token, Path: "/v1", HttpOnly: true, SameSite: http.SameSiteStrictMode, MaxAge: 28800})
	w.Header().Set("Cache-Control", "no-store")
	writeJSON(w, 200, s.sessionResponse(item))
}
func (s *server) localSession(w http.ResponseWriter, r *http.Request) {
	item, ok := s.authorize(w, r, r.Method == "DELETE")
	if !ok {
		return
	}
	w.Header().Set("Cache-Control", "no-store")
	if r.Method == "GET" {
		writeJSON(w, 200, s.sessionResponse(item))
		return
	}
	if r.Method == "DELETE" {
		c, _ := r.Cookie(cookieName)
		s.mu.Lock()
		delete(s.sessions, hashToken(c.Value))
		s.mu.Unlock()
		http.SetCookie(w, &http.Cookie{Name: cookieName, Path: "/v1", MaxAge: -1, HttpOnly: true, SameSite: http.SameSiteStrictMode})
		w.WriteHeader(204)
		return
	}
	fail(w, 405, "method_not_allowed", "GET or DELETE required")
}
func (s *server) projects(w http.ResponseWriter, r *http.Request) {
	_, ok := s.authorize(w, r, r.Method == "POST")
	if !ok {
		return
	}
	ctx, cancel := context.WithTimeout(r.Context(), 3*time.Second)
	defer cancel()
	var out json.RawMessage
	var err error
	switch r.Method {
	case "GET":
		limit := 25
		if v := r.URL.Query().Get("limit"); v != "" {
			limit, _ = strconv.Atoi(v)
		}
		if limit < 1 || limit > 100 {
			fail(w, 400, "invalid_request", "limit must be 1..100")
			return
		}
		out, err = s.store.List(ctx, r.URL.Query().Get("q"), limit)
	case "POST":
		body, readErr := json.Marshal(json.RawMessage{})
		_ = body
		var raw json.RawMessage
		if readErr = strictJSON(r, &raw); readErr != nil {
			fail(w, 400, "invalid_request", "Invalid project document")
			return
		}
		out, err = s.store.Create(ctx, raw)
	default:
		fail(w, 405, "method_not_allowed", "GET or POST required")
		return
	}
	if err != nil {
		slog.Error("project operation failed", "error", err)
		fail(w, 422, "project_operation_failed", "Project request could not be completed")
		return
	}
	status := 200
	if r.Method == "POST" {
		status = 201
	}
	writeJSON(w, status, out)
}
func (s *server) project(w http.ResponseWriter, r *http.Request) {
	if r.Method != "GET" {
		fail(w, 405, "method_not_allowed", "GET required")
		return
	}
	if _, ok := s.authorize(w, r, false); !ok {
		return
	}
	id := strings.TrimPrefix(r.URL.Path, "/v1/projects/")
	ctx, cancel := context.WithTimeout(r.Context(), 3*time.Second)
	defer cancel()
	out, err := s.store.Get(ctx, id)
	if err != nil {
		fail(w, 404, "resource_unavailable", "Project unavailable")
		return
	}
	writeJSON(w, 200, out)
}
func (s *server) analyses(w http.ResponseWriter, r *http.Request) {
	if r.Method != "POST" {
		fail(w, 405, "method_not_allowed", "POST required")
		return
	}
	if _, ok := s.authorize(w, r, true); !ok {
		return
	}
	if key := r.Header.Get("Idempotency-Key"); len(key) < 16 || len(key) > 128 {
		fail(w, 400, "invalid_request", "Idempotency-Key must be 16..128 characters")
		return
	}
	var in struct {
		ProjectID string `json:"project_id"`
	}
	if strictJSON(r, &in) != nil || in.ProjectID == "" {
		fail(w, 400, "invalid_request", "project_id is required")
		return
	}
	ctx, cancel := context.WithTimeout(r.Context(), 30*time.Second)
	defer cancel()
	projectJSON, err := s.store.Get(ctx, in.ProjectID)
	if err != nil {
		fail(w, 404, "resource_unavailable", "Project unavailable")
		return
	}
	var project struct {
		Source struct{ Kind, Location string } `json:"source"`
	}
	if json.Unmarshal(projectJSON, &project) != nil || project.Source.Kind != "local" {
		fail(w, 422, "unsupported_source", "This slice analyzes registered local folders only")
		return
	}
	doc, err := acquireAndAnalyze(in.ProjectID, project.Source.Location)
	if err != nil {
		slog.Warn("source analysis rejected", "project_id", in.ProjectID, "error", err)
		fail(w, 422, "analysis_rejected", err.Error())
		return
	}
	payload, _ := json.Marshal(doc)
	out, err := s.store.SaveAnalysis(ctx, payload)
	if err != nil {
		slog.Error("analysis persistence failed", "project_id", in.ProjectID, "error", err)
		fail(w, 422, "analysis_operation_failed", "Analysis could not be persisted")
		return
	}
	writeJSON(w, 202, out)
}
func (s *server) analysisResource(w http.ResponseWriter, r *http.Request) {
	mutation := r.Method == "POST"
	if _, ok := s.authorize(w, r, mutation); !ok {
		return
	}
	path := strings.TrimPrefix(r.URL.Path, "/v1/analyses/")
	if strings.HasSuffix(path, "/candidate-discovery") {
		if r.Method != "POST" {
			fail(w, 405, "method_not_allowed", "POST required")
			return
		}
		id := strings.TrimSuffix(path, "/candidate-discovery")
		ctx, cancel := context.WithTimeout(r.Context(), 5*time.Second)
		defer cancel()
		analysisJSON, err := s.store.GetAnalysis(ctx, id)
		if err != nil {
			fail(w, 404, "resource_unavailable", "Analysis unavailable")
			return
		}
		graphJSON, err := s.store.GetGraph(ctx, id)
		if err != nil {
			fail(w, 404, "resource_unavailable", "Analysis graph unavailable")
			return
		}
		var analysis struct {
			ID           string `json:"id"`
			SourceDigest string `json:"source_digest"`
		}
		var graph struct {
			Nodes []graphNode `json:"nodes"`
		}
		if json.Unmarshal(analysisJSON, &analysis) != nil || json.Unmarshal(graphJSON, &graph) != nil {
			fail(w, 500, "internal_failure", "Stored analysis could not be read")
			return
		}
		discovery := discoverCandidates(analysis.ID, analysis.SourceDigest, graph.Nodes)
		payload, _ := json.Marshal(discovery)
		out, err := s.store.SaveDiscovery(ctx, id, payload)
		if err != nil {
			slog.Error("candidate discovery persistence failed", "analysis_id", id, "error", err)
			fail(w, 422, "candidate_discovery_failed", "Candidate discovery could not be persisted")
			return
		}
		writeJSON(w, 201, out)
		return
	}
	if r.Method != "GET" {
		fail(w, 405, "method_not_allowed", "GET required")
		return
	}
	if strings.HasSuffix(path, "/candidates") {
		id := strings.TrimSuffix(path, "/candidates")
		ctx, cancel := context.WithTimeout(r.Context(), 3*time.Second)
		defer cancel()
		out, err := s.store.GetCandidates(ctx, id)
		if err != nil {
			fail(w, 404, "resource_unavailable", "Candidates unavailable")
			return
		}
		writeJSON(w, 200, out)
		return
	}
	if strings.HasSuffix(path, "/recommendation") {
		id := strings.TrimSuffix(path, "/recommendation")
		ctx, cancel := context.WithTimeout(r.Context(), 3*time.Second)
		defer cancel()
		out, err := s.store.GetRecommendation(ctx, id)
		if err != nil {
			fail(w, 404, "resource_unavailable", "Recommendation unavailable")
			return
		}
		writeJSON(w, 200, out)
		return
	}
	if strings.HasSuffix(path, "/plan") {
		id := strings.TrimSuffix(path, "/plan")
		ctx, cancel := context.WithTimeout(r.Context(), 3*time.Second)
		defer cancel()
		out, err := s.store.GetLatestPlan(ctx, id)
		if err != nil {
			fail(w, 404, "resource_unavailable", "Plan unavailable")
			return
		}
		writeJSON(w, 200, out)
		return
	}
	isGraph := strings.HasSuffix(path, "/graph")
	id := strings.TrimSuffix(path, "/graph")
	ctx, cancel := context.WithTimeout(r.Context(), 3*time.Second)
	defer cancel()
	var out json.RawMessage
	var err error
	if isGraph {
		out, err = s.store.GetGraph(ctx, id)
	} else {
		out, err = s.store.GetAnalysis(ctx, id)
	}
	if err != nil {
		fail(w, 404, "resource_unavailable", "Analysis unavailable")
		return
	}
	writeJSON(w, 200, out)
}
func (s *server) plans(w http.ResponseWriter, r *http.Request) {
	if r.Method != "POST" {
		fail(w, 405, "method_not_allowed", "POST required")
		return
	}
	if _, ok := s.authorize(w, r, true); !ok {
		return
	}
	var in struct {
		AnalysisID   string   `json:"analysis_id"`
		CandidateIDs []string `json:"candidate_ids"`
	}
	if strictJSON(r, &in) != nil || in.AnalysisID == "" || len(in.CandidateIDs) == 0 {
		fail(w, 400, "invalid_request", "analysis_id and candidate_ids are required")
		return
	}
	ctx, cancel := context.WithTimeout(r.Context(), 5*time.Second)
	defer cancel()
	analysisJSON, err := s.store.GetAnalysis(ctx, in.AnalysisID)
	if err != nil {
		fail(w, 404, "resource_unavailable", "Analysis unavailable")
		return
	}
	candidateJSON, err := s.store.GetCandidates(ctx, in.AnalysisID)
	if err != nil {
		fail(w, 404, "resource_unavailable", "Candidates unavailable")
		return
	}
	recommendationJSON, err := s.store.GetRecommendation(ctx, in.AnalysisID)
	if err != nil {
		fail(w, 404, "resource_unavailable", "Recommendation unavailable")
		return
	}
	var analysis analysisDocument
	var candidateList struct {
		Items []candidate `json:"items"`
	}
	var recommendation recommendationDocument
	if json.Unmarshal(analysisJSON, &analysis) != nil || json.Unmarshal(candidateJSON, &candidateList) != nil || json.Unmarshal(recommendationJSON, &recommendation) != nil {
		fail(w, 500, "internal_failure", "Stored review data could not be read")
		return
	}
	envelope, canonical, err := buildPlan(analysis, recommendation, candidateList.Items, in.CandidateIDs)
	if err != nil {
		fail(w, 422, "plan_rejected", err.Error())
		return
	}
	payload, _ := json.Marshal(envelope)
	out, err := s.store.CreatePlan(ctx, payload, canonical, envelope.ContentHash)
	if err != nil {
		slog.Error("plan persistence failed", "analysis_id", in.AnalysisID, "error", err)
		fail(w, 422, "plan_operation_failed", "Exact plan could not be persisted")
		return
	}
	writeJSON(w, 201, out)
}
func (s *server) candidateResource(w http.ResponseWriter, r *http.Request) {
	if r.Method != "POST" || !strings.HasSuffix(r.URL.Path, "/adjudication") {
		fail(w, 405, "method_not_allowed", "POST adjudication required")
		return
	}
	if _, ok := s.authorize(w, r, true); !ok {
		return
	}
	id := strings.TrimSuffix(strings.TrimPrefix(r.URL.Path, "/v1/candidates/"), "/adjudication")
	var in struct {
		AuthorizationBasis     string          `json:"authorization_basis"`
		Sensitivity            string          `json:"sensitivity"`
		DomainServiceReference string          `json:"domain_service_reference"`
		RequiredScopes         []string        `json:"required_scopes"`
		InputSchema            json.RawMessage `json:"input_schema"`
		OutputSchema           json.RawMessage `json:"output_schema"`
		SecurityConfirmed      bool            `json:"security_confirmed"`
	}
	if strictJSON(r, &in) != nil || id == "" || len(strings.TrimSpace(in.AuthorizationBasis)) < 20 ||
		!strings.HasPrefix(in.DomainServiceReference, "verified:") ||
		(in.Sensitivity != "public" && in.Sensitivity != "internal" && in.Sensitivity != "sensitive") ||
		len(in.InputSchema) == 0 || len(in.OutputSchema) == 0 || !in.SecurityConfirmed {
		fail(w, 400, "invalid_request", "Complete mapping, schemas, authorization basis and security confirmation are required")
		return
	}
	payload, _ := json.Marshal(in)
	ctx, cancel := context.WithTimeout(r.Context(), 5*time.Second)
	defer cancel()
	out, err := s.store.AdjudicateCandidate(ctx, id, payload)
	if err != nil {
		slog.Warn("candidate adjudication rejected", "candidate_id", id, "error", err)
		fail(w, 422, "adjudication_rejected", "Candidate adjudication was rejected")
		return
	}
	writeJSON(w, 201, out)
}
func (s *server) planResource(w http.ResponseWriter, r *http.Request) {
	path := strings.TrimPrefix(r.URL.Path, "/v1/plans/")
	if strings.HasSuffix(path, "/approval") {
		if r.Method != "POST" {
			fail(w, 405, "method_not_allowed", "POST required")
			return
		}
		if _, ok := s.authorize(w, r, true); !ok {
			return
		}
		id := strings.TrimSuffix(path, "/approval")
		var in struct {
			PlanVersion       int    `json:"plan_version"`
			ContentHash       string `json:"content_hash"`
			SecurityConfirmed bool   `json:"security_confirmed"`
		}
		if strictJSON(r, &in) != nil || in.PlanVersion < 1 || len(in.ContentHash) != 64 || !in.SecurityConfirmed {
			fail(w, 400, "invalid_request", "Exact plan version/hash and security confirmation are required")
			return
		}
		ctx, cancel := context.WithTimeout(r.Context(), 3*time.Second)
		defer cancel()
		out, err := s.store.ApprovePlan(ctx, id, in.PlanVersion, in.ContentHash, in.SecurityConfirmed)
		if err != nil {
			fail(w, 409, "approval_conflict", "Plan approval was rejected")
			return
		}
		writeJSON(w, 201, out)
		return
	}
	if r.Method != "GET" {
		fail(w, 405, "method_not_allowed", "GET required")
		return
	}
	if _, ok := s.authorize(w, r, false); !ok {
		return
	}
	ctx, cancel := context.WithTimeout(r.Context(), 3*time.Second)
	defer cancel()
	out, err := s.store.GetPlan(ctx, path)
	if err != nil {
		fail(w, 404, "resource_unavailable", "Plan unavailable")
		return
	}
	writeJSON(w, 200, out)
}
func (s *server) routes(webDir string) http.Handler {
	mux := http.NewServeMux()
	mux.HandleFunc("/v1/local-session/exchange", s.exchange)
	mux.HandleFunc("/v1/local-session", s.localSession)
	mux.HandleFunc("/v1/local-session/logout", s.localSession)
	mux.HandleFunc("/v1/projects", s.projects)
	mux.HandleFunc("/v1/projects/", s.project)
	mux.HandleFunc("/v1/analyses", s.analyses)
	mux.HandleFunc("/v1/analyses/", s.analysisResource)
	mux.HandleFunc("/v1/candidates/", s.candidateResource)
	mux.HandleFunc("/v1/plans", s.plans)
	mux.HandleFunc("/v1/plans/", s.planResource)
	mux.Handle("/", http.FileServer(http.Dir(webDir)))
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.Header().Set("X-Content-Type-Options", "nosniff")
		w.Header().Set("Referrer-Policy", "no-referrer")
		mux.ServeHTTP(w, r)
	})
}
func main() {
	listen := os.Getenv("MCPSTUDIO_LISTEN")
	if listen == "" {
		listen = "127.0.0.1:8080"
	}
	host, _, _ := net.SplitHostPort(listen)
	if host != "127.0.0.1" && host != "localhost" {
		panic("API must bind to loopback")
	}
	dsn := os.Getenv("MCPSTUDIO_DATABASE_URL")
	if dsn == "" {
		panic("MCPSTUDIO_DATABASE_URL required")
	}
	pool, err := pgxpool.New(context.Background(), dsn)
	if err != nil {
		panic(err)
	}
	defer pool.Close()
	code := os.Getenv("MCPSTUDIO_BOOTSTRAP_CODE")
	if len(code) != 43 {
		panic("43-character MCPSTUDIO_BOOTSTRAP_CODE required")
	}
	srv := &server{store: postgresStore{pool}, origin: "http://" + listen, actor: os.Getenv("MCPSTUDIO_ACTOR_ID"), tenant: os.Getenv("MCPSTUDIO_TENANT_ID"), bootstrap: hashToken(code), bootstrapExpires: time.Now().Add(10 * time.Minute), sessions: map[[32]byte]*session{}, now: time.Now}
	web := os.Getenv("MCPSTUDIO_WEB_DIR")
	if web == "" {
		web = filepath.Join("..", "web", "out")
	}
	slog.Info("MCPStudio started", "address", srv.origin)
	if err = http.ListenAndServe(listen, srv.routes(web)); err != nil {
		panic(fmt.Errorf("serve: %w", err))
	}
}
