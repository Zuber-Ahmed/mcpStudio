package main

import (
	"crypto/sha256"
	"fmt"
	"strings"
)

const candidateDetectorVersion = "route-candidate-deterministic-v2"

type candidate struct {
	ID                     string         `json:"id"`
	FindingID              string         `json:"finding_id"`
	GraphNodeID            string         `json:"graph_node_id"`
	OperationType          string         `json:"operation_type"`
	SideEffects            []string       `json:"side_effects"`
	Sensitivity            string         `json:"sensitivity"`
	RequiredScopes         []string       `json:"required_scopes"`
	InputSchema            map[string]any `json:"input_schema"`
	OutputSchema           map[string]any `json:"output_schema"`
	Eligibility            string         `json:"eligibility"`
	ReasonCodes            []string       `json:"reason_codes"`
	Evidence               []evidence     `json:"evidence"`
	Detector               map[string]any `json:"detector"`
	Provenance             string         `json:"provenance"`
	Confidence             map[string]any `json:"confidence"`
	DomainServiceReference string         `json:"domain_service_reference"`
	Adjudication           *adjudication  `json:"adjudication,omitempty"`
}

type adjudication struct {
	SourceCandidateID  string `json:"source_candidate_id"`
	AuthorizationBasis string `json:"authorization_basis"`
	SecurityConfirmed  bool   `json:"security_confirmed"`
}

type recommendationDocument struct {
	ID                  string   `json:"id"`
	Version             int      `json:"version"`
	SourceDigest        string   `json:"source_digest"`
	RecommendedType     string   `json:"recommended_type"`
	Rationale           string   `json:"rationale"`
	CandidateIDs        []string `json:"candidate_ids"`
	Risks               []string `json:"risks"`
	RequiredReviews     []string `json:"required_reviews"`
	SupportedGeneration bool     `json:"supported_generation"`
	AvailabilityReason  string   `json:"availability_reason"`
}

type discoveryDocument struct {
	AnalysisID     string                 `json:"analysis_id"`
	Candidates     []candidate            `json:"candidates"`
	Recommendation recommendationDocument `json:"recommendation"`
}

func uuidFromKey(key string) string {
	b := sha256.Sum256([]byte(key))
	b[6] = (b[6] & 0x0f) | 0x50
	b[8] = (b[8] & 0x3f) | 0x80
	return fmt.Sprintf("%08x-%04x-%04x-%04x-%012x", b[0:4], b[4:6], b[6:8], b[8:10], b[10:16])
}

func routeParts(label string) (string, string, bool) {
	method, path, ok := strings.Cut(strings.TrimSpace(label), " ")
	return strings.ToUpper(method), strings.TrimSpace(path), ok && strings.HasPrefix(path, "/")
}

func sensitiveRoute(path string) bool {
	lower := strings.ToLower(path)
	for _, token := range []string{"admin", "auth", "login", "token", "secret", "user", "account", "billing", "payment"} {
		if strings.Contains(lower, token) {
			return true
		}
	}
	return false
}

func discoverCandidates(analysisID, sourceDigest string, nodes []graphNode) discoveryDocument {
	doc := discoveryDocument{AnalysisID: analysisID, Candidates: []candidate{}}
	allowed := []string{}
	for _, node := range nodes {
		if node.Kind != "http_route" || len(node.Evidence) == 0 || node.Evidence[0].DetectorVersion != analyzerVersion {
			continue
		}
		method, path, ok := routeParts(node.Label)
		if !ok {
			continue
		}
		operation, eligibility, sensitivity := "unknown", "unsupported", "unknown"
		sideEffects, reasons := []string{}, []string{"operation_not_supported"}
		switch method {
		case "GET", "HEAD":
			operation, sensitivity = "read", "unknown"
			reasons = []string{"authorization_unknown", "sensitivity_unknown", "schema_unverified", "domain_mapping_required", "route_name_not_authority"}
			eligibility = "unknown"
		case "POST", "PUT", "PATCH", "DELETE":
			operation, eligibility, sensitivity = "write", "blocked", "internal"
			sideEffects = []string{"state_change"}
			reasons = []string{"write_operation_requires_domain_review", "authorization_unverified", "schema_unverified"}
			if sensitiveRoute(path) {
				sensitivity = "sensitive"
			}
		}
		ev := node.Evidence[0]
		ev.SourceDigest = sourceDigest
		ev.DetectorVersion = candidateDetectorVersion
		id := uuidFromKey(analysisID + "|" + node.ID + "|" + candidateDetectorVersion)
		domainReference := "unresolved:" + node.Label
		item := candidate{
			ID: id, FindingID: "http-route:" + method + ":" + path, GraphNodeID: node.ID, OperationType: operation,
			SideEffects: sideEffects, Sensitivity: sensitivity, RequiredScopes: []string{},
			InputSchema: map[string]any{"type": "object", "additionalProperties": true}, OutputSchema: map[string]any{"type": "object", "additionalProperties": true},
			Eligibility: eligibility, ReasonCodes: reasons, Evidence: []evidence{ev},
			Detector: map[string]any{"id": "route-candidate-detector", "version": candidateDetectorVersion}, Provenance: "deterministic",
			Confidence: map[string]any{"value": 1.0, "method": "static-http-route"}, DomainServiceReference: domainReference,
		}
		doc.Candidates = append(doc.Candidates, item)
		if eligibility == "allowed" {
			allowed = append(allowed, id)
		}
	}
	recommended := "none"
	rationale := "No safely eligible route was detected; route names alone do not prove authorization, sensitivity, side effects or domain mapping."
	if len(allowed) > 0 {
		recommended = "server"
		rationale = "Deterministic public health/status read routes are suitable MCP server candidates after operator review."
	}
	doc.Recommendation = recommendationDocument{
		ID: uuidFromKey(analysisID + "|recommendation|" + candidateDetectorVersion), Version: 1, SourceDigest: sourceDigest,
		RecommendedType: recommended, Rationale: rationale, CandidateIDs: allowed,
		Risks:               []string{"Authorization and response schemas are not inferred beyond deterministic route evidence."},
		RequiredReviews:     []string{"Confirm domain-service mapping", "Confirm authorization and data sensitivity", "Confirm input and output schemas"},
		SupportedGeneration: false, AvailabilityReason: "Generation remains locked; deterministic route evidence does not establish an executable domain-service mapping.",
	}
	return doc
}
