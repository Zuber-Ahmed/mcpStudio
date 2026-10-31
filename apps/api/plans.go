package main

import (
	"crypto/sha256"
	"encoding/hex"
	"encoding/json"
	"errors"
	"fmt"
	"sort"
	"strings"
)

const (
	localPolicyID      = "00000000-0000-4000-8000-000000000101"
	localPolicyVersion = "local-safe-v1"
)

type planEnvelope struct {
	PlanID           string                 `json:"plan_id"`
	AnalysisID       string                 `json:"analysis_id"`
	SourceDigest     string                 `json:"source_digest"`
	Recommendation   recommendationDocument `json:"recommendation"`
	CanonicalPayload map[string]any         `json:"canonical_payload"`
	Canonicalization string                 `json:"canonicalization"`
	ContentHash      string                 `json:"content_hash"`
}

func buildPlan(analysis analysisDocument, current recommendationDocument, all []candidate, selectedIDs []string) (planEnvelope, []byte, error) {
	currentAnalyzer := false
	for _, version := range analysis.AnalyzerVersions {
		if version["id"] == "typescript-next" && version["version"] == analyzerVersion {
			currentAnalyzer = true
		}
	}
	if !currentAnalyzer {
		return planEnvelope{}, nil, errors.New("analysis must be refreshed with the current analyzer before planning")
	}
	if len(selectedIDs) == 0 {
		return planEnvelope{}, nil, errors.New("at least one eligible candidate is required")
	}
	selectedSet := map[string]bool{}
	for _, id := range selectedIDs {
		if selectedSet[id] {
			return planEnvelope{}, nil, errors.New("candidate selection contains duplicates")
		}
		selectedSet[id] = true
	}
	selected := make([]candidate, 0, len(selectedIDs))
	for _, item := range all {
		if !selectedSet[item.ID] {
			continue
		}
		if item.Eligibility != "allowed" || item.OperationType != "read" || strings.HasPrefix(item.DomainServiceReference, "unresolved:") {
			return planEnvelope{}, nil, errors.New("candidate is not executable")
		}
		deterministic := item.Provenance == "deterministic" && item.Detector["id"] == "route-candidate-detector" && item.Detector["version"] == candidateDetectorVersion
		adjudicated := item.Provenance == "manual" && item.Detector["id"] == "candidate-adjudication" && item.Detector["version"] == "manual-v1" && item.Adjudication != nil && item.Adjudication.SecurityConfirmed && len(strings.TrimSpace(item.Adjudication.AuthorizationBasis)) >= 20
		if (!deterministic && !adjudicated) || len(item.Evidence) == 0 || item.Evidence[0].DetectorVersion != candidateDetectorVersion {
			return planEnvelope{}, nil, errors.New("candidate must be refreshed with the current detector before planning")
		}
		selected = append(selected, item)
	}
	if len(selected) != len(selectedIDs) {
		return planEnvelope{}, nil, errors.New("candidate selection is unavailable")
	}
	sort.Slice(selected, func(i, j int) bool { return selected[i].ID < selected[j].ID })
	candidateDocs := make([]any, 0, len(selected))
	recommendationIDs := make([]string, 0, len(selected))
	for _, item := range selected {
		scopes := append([]string{}, item.RequiredScopes...)
		sort.Strings(scopes)
		candidateDocs = append(candidateDocs, map[string]any{"id": item.ID, "input_schema": item.InputSchema, "output_schema": item.OutputSchema, "domain_service_reference": item.DomainServiceReference, "required_scopes": scopes})
		recommendationIDs = append(recommendationIDs, item.ID)
	}
	recommendationID := uuidFromKey(analysis.ID + "|plan-recommendation|" + strings.Join(recommendationIDs, ",") + "|version|" + fmt.Sprint(current.Version+1))
	recommendation := recommendationDocument{ID: recommendationID, Version: current.Version + 1, SourceDigest: analysis.SourceDigest, RecommendedType: "server", Rationale: "Operator-selected eligible read candidates are bound to an exact review plan.", CandidateIDs: recommendationIDs, Risks: current.Risks, RequiredReviews: current.RequiredReviews, SupportedGeneration: true, AvailabilityReason: "Eligible for exact plan review; the product generation endpoint is not implemented."}
	versions := append([]map[string]any{}, analysis.AnalyzerVersions...)
	sort.Slice(versions, func(i, j int) bool { return versions[i]["id"].(string) < versions[j]["id"].(string) })
	payload := map[string]any{
		"snapshot_id": analysis.SnapshotID, "source_digest": analysis.SourceDigest, "analysis_id": analysis.ID, "analyzer_versions": versions,
		"recommendation_id": recommendation.ID, "recommendation_version": recommendation.Version, "selected_type": "server", "candidates": candidateDocs,
		"generator":     map[string]any{"id": "mcpstudio-go-generator", "version": "not-enabled-v1"},
		"configuration": map[string]any{"plugin": map[string]any{"id": "builtin-route-review", "version": "1"}, "schema": map[string]any{"id": "builtin-route-config", "version": "1"}, "values": map[string]any{}},
		"transport":     "stdio", "policy": map[string]any{"id": localPolicyID, "version": localPolicyVersion, "required_checks": []string{"artifact_manifest", "compile", "test"}}, "override_reason": nil,
	}
	canonical, err := json.Marshal(payload)
	if err != nil {
		return planEnvelope{}, nil, err
	}
	hash := sha256.Sum256(canonical)
	envelope := planEnvelope{PlanID: newUUID(), AnalysisID: analysis.ID, SourceDigest: analysis.SourceDigest, Recommendation: recommendation, CanonicalPayload: payload, Canonicalization: "RFC8785+MCPStudio-sets-v1", ContentHash: hex.EncodeToString(hash[:])}
	return envelope, canonical, nil
}
