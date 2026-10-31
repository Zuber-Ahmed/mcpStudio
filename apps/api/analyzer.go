package main

import (
	"crypto/rand"
	"crypto/sha256"
	"encoding/hex"
	"errors"
	"fmt"
	"io"
	"io/fs"
	"os"
	pathpkg "path"
	"path/filepath"
	"regexp"
	"sort"
	"strings"
)

const (
	analyzerVersion = "typescript-next-deterministic-v2"
	maxSourceFiles  = 5000
	maxFileBytes    = 2 << 20
	maxTotalBytes   = 25 << 20
)

type evidence struct {
	Path            string `json:"path"`
	SourceDigest    string `json:"source_digest"`
	LineStart       int    `json:"line_start"`
	LineEnd         int    `json:"line_end"`
	DetectorVersion string `json:"detector_version"`
}

type graphNode struct {
	ID         string         `json:"id"`
	Kind       string         `json:"kind"`
	Label      string         `json:"label"`
	Evidence   []evidence     `json:"evidence"`
	Provenance string         `json:"provenance"`
	Confidence map[string]any `json:"confidence"`
}

type graphEdge struct {
	ID         string     `json:"id"`
	FromNodeID string     `json:"from_node_id"`
	ToNodeID   string     `json:"to_node_id"`
	Kind       string     `json:"kind"`
	Provenance string     `json:"provenance"`
	Evidence   []evidence `json:"evidence"`
}

type analysisDocument struct {
	ID               string           `json:"id"`
	ProjectID        string           `json:"project_id"`
	SnapshotID       string           `json:"snapshot_id"`
	SourceDigest     string           `json:"source_digest"`
	ResolvedRevision string           `json:"resolved_revision"`
	StorageKey       string           `json:"storage_key"`
	Status           string           `json:"status"`
	AnalyzerVersions []map[string]any `json:"analyzer_versions"`
	Scope            map[string]any   `json:"scope"`
	Diagnostics      []map[string]any `json:"diagnostics"`
	Nodes            []graphNode      `json:"nodes"`
	Edges            []graphEdge      `json:"edges"`
}

type sourceFile struct {
	path, digest string
	content      []byte
}

var (
	importPattern    = regexp.MustCompile(`(?m)(?:\bfrom\s*|\brequire\s*\(\s*|\bimport\s*\(\s*)["']([^"']+)["']`)
	routePattern     = regexp.MustCompile(`(?m)\bexport\s+(?:(?:async\s+)?function\s+(GET|POST|PUT|PATCH|DELETE|OPTIONS|HEAD)\s*\(|const\s+(GET|POST|PUT|PATCH|DELETE|OPTIONS|HEAD)\s*=)`)
	routeFilePattern = regexp.MustCompile(`^route\.(?:ts|tsx|js|jsx|mjs|cjs)$`)
)

func newUUID() string {
	b := make([]byte, 16)
	if _, err := rand.Read(b); err != nil {
		panic(err)
	}
	b[6] = (b[6] & 0x0f) | 0x40
	b[8] = (b[8] & 0x3f) | 0x80
	return fmt.Sprintf("%08x-%04x-%04x-%04x-%012x", b[0:4], b[4:6], b[6:8], b[8:10], b[10:16])
}

func withinRoot(root, child string) bool {
	rel, err := filepath.Rel(root, child)
	return err == nil && rel != ".." && !strings.HasPrefix(rel, ".."+string(filepath.Separator)) && !filepath.IsAbs(rel)
}

func canonicalRoot(value string) (string, error) {
	if strings.TrimSpace(value) == "" {
		return "", errors.New("local source path is empty")
	}
	abs, err := filepath.Abs(value)
	if err != nil {
		return "", fmt.Errorf("resolve source root: %w", err)
	}
	root, err := filepath.EvalSymlinks(abs)
	if err != nil {
		return "", fmt.Errorf("resolve source root: %w", err)
	}
	info, err := os.Stat(root)
	if err != nil || !info.IsDir() {
		return "", errors.New("registered local source is not a readable directory")
	}
	return filepath.Clean(root), nil
}

func ignoredDirectory(name string) bool {
	switch strings.ToLower(name) {
	case ".git", ".next", ".local", ".codex", ".agents", ".aws", "node_modules", "dist", "build", "out", "coverage", ".turbo":
		return true
	default:
		return false
	}
}

type ignoreRule struct {
	pattern, original            string
	directory, anchored, negated bool
}

func loadIgnoreRules(root string) ([]ignoreRule, error) {
	name := filepath.Join(root, ".gitignore")
	info, err := os.Lstat(name)
	if errors.Is(err, os.ErrNotExist) {
		return nil, nil
	}
	if err != nil {
		return nil, err
	}
	if !info.Mode().IsRegular() || info.Size() > maxFileBytes {
		return nil, errors.New("root .gitignore must be a bounded regular file")
	}
	data, err := os.ReadFile(name)
	if err != nil {
		return nil, err
	}
	var rules []ignoreRule
	for _, raw := range strings.Split(strings.ReplaceAll(string(data), "\r\n", "\n"), "\n") {
		value := strings.TrimSpace(raw)
		if value == "" || strings.HasPrefix(value, "#") {
			continue
		}
		rule := ignoreRule{original: value}
		if strings.HasPrefix(value, "!") {
			rule.negated = true
			value = strings.TrimPrefix(value, "!")
		}
		rule.anchored = strings.HasPrefix(value, "/")
		value = strings.TrimPrefix(value, "/")
		rule.directory = strings.HasSuffix(value, "/")
		value = strings.TrimSuffix(value, "/")
		value = pathpkg.Clean(strings.ReplaceAll(value, "\\", "/"))
		// Double-star and escaped-pattern semantics are not claimed by this bounded reader.
		if value == "." || strings.HasPrefix(value, "../") || strings.Contains(value, "**") {
			continue
		}
		rule.pattern = value
		rules = append(rules, rule)
	}
	return rules, nil
}

func ruleMatches(rule ignoreRule, relative string, directory bool) bool {
	relative = strings.Trim(strings.ReplaceAll(relative, "\\", "/"), "/")
	if rule.directory && !directory && relative != rule.pattern && !strings.HasPrefix(relative, rule.pattern+"/") {
		return false
	}
	if rule.anchored || strings.Contains(rule.pattern, "/") {
		matched, _ := pathpkg.Match(rule.pattern, relative)
		return matched || rule.directory && strings.HasPrefix(relative, rule.pattern+"/")
	}
	for _, segment := range strings.Split(relative, "/") {
		if matched, _ := pathpkg.Match(rule.pattern, segment); matched {
			return true
		}
	}
	return false
}

func ignoredByRules(relative string, directory bool, rules []ignoreRule) bool {
	ignored := false
	for _, rule := range rules {
		if ruleMatches(rule, relative, directory) {
			ignored = !rule.negated
		}
	}
	return ignored
}

func includedSource(path string) bool {
	switch strings.ToLower(filepath.Ext(path)) {
	case ".ts", ".tsx", ".js", ".jsx", ".mjs", ".cjs", ".json":
		return true
	default:
		return false
	}
}

func readSnapshot(root string) ([]sourceFile, string, int64, error) {
	var files []sourceFile
	var total int64
	rules, err := loadIgnoreRules(root)
	if err != nil {
		return nil, "", 0, err
	}
	err = filepath.WalkDir(root, func(path string, entry fs.DirEntry, walkErr error) error {
		if walkErr != nil {
			return walkErr
		}
		if path == root {
			return nil
		}
		rel, err := filepath.Rel(root, path)
		if err != nil {
			return err
		}
		rel = filepath.ToSlash(filepath.Clean(rel))
		if entry.IsDir() && (ignoredDirectory(entry.Name()) || ignoredByRules(rel, true, rules)) {
			return filepath.SkipDir
		}
		if entry.Type()&os.ModeSymlink != 0 {
			return fmt.Errorf("symbolic links are not allowed in source snapshots: %s", entry.Name())
		}
		if entry.IsDir() || ignoredByRules(rel, false, rules) || !includedSource(path) {
			return nil
		}
		resolved, err := filepath.EvalSymlinks(path)
		if err != nil || !withinRoot(root, resolved) {
			return fmt.Errorf("source path escapes canonical root: %s", path)
		}
		info, err := entry.Info()
		if err != nil {
			return err
		}
		if !info.Mode().IsRegular() {
			return fmt.Errorf("non-regular source file is not allowed: %s", path)
		}
		if info.Size() > maxFileBytes {
			return fmt.Errorf("source file exceeds %d-byte limit: %s", maxFileBytes, path)
		}
		total += info.Size()
		if total > maxTotalBytes {
			return fmt.Errorf("source snapshot exceeds %d-byte limit", maxTotalBytes)
		}
		if len(files) >= maxSourceFiles {
			return fmt.Errorf("source snapshot exceeds %d-file limit", maxSourceFiles)
		}
		f, err := os.Open(path)
		if err != nil {
			return err
		}
		data, readErr := io.ReadAll(io.LimitReader(f, maxFileBytes+1))
		closeErr := f.Close()
		if readErr != nil {
			return readErr
		}
		if closeErr != nil {
			return closeErr
		}
		h := sha256.Sum256(data)
		files = append(files, sourceFile{path: rel, digest: hex.EncodeToString(h[:]), content: data})
		return nil
	})
	if err != nil {
		return nil, "", 0, err
	}
	if len(files) == 0 {
		return nil, "", 0, errors.New("no supported TypeScript, JavaScript or JSON files found")
	}
	sort.Slice(files, func(i, j int) bool { return files[i].path < files[j].path })
	manifest := sha256.New()
	for _, file := range files {
		_, _ = manifest.Write([]byte(file.path))
		_, _ = manifest.Write([]byte{0})
		_, _ = manifest.Write([]byte(file.digest))
		_, _ = manifest.Write([]byte{'\n'})
	}
	return files, hex.EncodeToString(manifest.Sum(nil)), total, nil
}

func evidenceAt(file sourceFile, line int) []evidence {
	if line < 1 {
		line = 1
	}
	return []evidence{{Path: file.path, SourceDigest: file.digest, LineStart: line, LineEnd: line, DetectorVersion: analyzerVersion}}
}

func lineAt(content []byte, offset int) int { return 1 + strings.Count(string(content[:offset]), "\n") }

func resolveImport(from, spec string, known map[string]string) string {
	if !strings.HasPrefix(spec, ".") {
		return ""
	}
	base := filepath.ToSlash(filepath.Clean(filepath.Join(filepath.Dir(from), filepath.FromSlash(spec))))
	candidates := []string{base}
	for _, ext := range []string{".ts", ".tsx", ".js", ".jsx", ".mjs", ".cjs", ".json"} {
		candidates = append(candidates, base+ext)
	}
	for _, ext := range []string{".ts", ".tsx", ".js", ".jsx", ".mjs", ".cjs"} {
		candidates = append(candidates, base+"/index"+ext)
	}
	for _, candidate := range candidates {
		if id, ok := known[candidate]; ok {
			return id
		}
	}
	return ""
}

func nextRoutePath(file string) (string, bool) {
	value := filepath.ToSlash(file)
	switch {
	case strings.HasPrefix(value, "src/app/"):
		value = strings.TrimPrefix(value, "src/app/")
	case strings.HasPrefix(value, "app/"):
		value = strings.TrimPrefix(value, "app/")
	default:
		return "", false
	}
	parts := strings.Split(value, "/")
	if len(parts) == 0 || !routeFilePattern.MatchString(parts[len(parts)-1]) {
		return "", false
	}
	var urlParts []string
	for _, part := range parts[:len(parts)-1] {
		if strings.HasPrefix(part, "(") && strings.HasSuffix(part, ")") {
			continue
		}
		if strings.HasPrefix(part, "@") || strings.HasPrefix(part, "(.)") || strings.HasPrefix(part, "(..)") || strings.HasPrefix(part, "(...)") {
			return "", false
		}
		urlParts = append(urlParts, part)
	}
	return "/" + strings.Join(urlParts, "/"), true
}

// maskNonCode preserves byte offsets and newlines while removing comments and
// string/template contents from route-export authority.
func maskNonCode(content []byte) []byte {
	out := append([]byte(nil), content...)
	const (
		code = iota
		lineComment
		blockComment
		singleQuote
		doubleQuote
		templateQuote
		regexQuote
	)
	state, escaped, regexClass := code, false, false
	for i := 0; i < len(out); i++ {
		ch := out[i]
		if state == code {
			switch {
			case ch == '/' && i+1 < len(out) && out[i+1] == '/':
				out[i], out[i+1], state = ' ', ' ', lineComment
				i++
			case ch == '/' && i+1 < len(out) && out[i+1] == '*':
				out[i], out[i+1], state = ' ', ' ', blockComment
				i++
			case ch == '\'':
				out[i], state = ' ', singleQuote
			case ch == '"':
				out[i], state = ' ', doubleQuote
			case ch == '`':
				out[i], state = ' ', templateQuote
			case ch == '/' && regexLiteralStart(content, i):
				out[i], state, regexClass = ' ', regexQuote, false
			}
			continue
		}
		if ch == '\n' || ch == '\r' {
			if state == lineComment {
				state = code
			}
			escaped = false
			continue
		}
		out[i] = ' '
		if state == blockComment && ch == '*' && i+1 < len(content) && content[i+1] == '/' {
			out[i+1], state = ' ', code
			i++
			continue
		}
		if escaped {
			escaped = false
			continue
		}
		if ch == '\\' && state != lineComment && state != blockComment {
			escaped = true
			continue
		}
		if state == regexQuote {
			if ch == '[' {
				regexClass = true
			} else if ch == ']' {
				regexClass = false
			} else if ch == '/' && !regexClass {
				state = code
			}
			continue
		}
		if state == singleQuote && ch == '\'' || state == doubleQuote && ch == '"' || state == templateQuote && ch == '`' {
			state = code
		}
	}
	return out
}

func regexLiteralStart(content []byte, offset int) bool {
	for i := offset - 1; i >= 0; i-- {
		switch content[i] {
		case ' ', '\t', '\r', '\n':
			continue
		case '=', '(', '[', '{', ',', ':', ';', '!', '?', '&', '|', '+', '-', '*', '%', '^', '~', '<', '>':
			return true
		default:
			return false
		}
	}
	return true
}

func acquireAndAnalyze(projectID, rootValue string) (analysisDocument, error) {
	root, err := canonicalRoot(rootValue)
	if err != nil {
		return analysisDocument{}, err
	}
	files, digest, total, err := readSnapshot(root)
	if err != nil {
		return analysisDocument{}, err
	}
	result := analysisDocument{
		ID: newUUID(), ProjectID: projectID, SnapshotID: newUUID(), SourceDigest: digest,
		ResolvedRevision: "local-sha256:" + digest, StorageKey: root, Status: "succeeded",
		AnalyzerVersions: []map[string]any{{"id": "typescript-next", "version": analyzerVersion}},
		Scope:            map[string]any{"file_count": len(files), "total_bytes": total, "extensions": []string{"ts", "tsx", "js", "jsx", "mjs", "cjs", "json"}},
		Diagnostics:      []map[string]any{}, Nodes: []graphNode{}, Edges: []graphEdge{},
	}
	known := map[string]string{}
	for _, file := range files {
		id := newUUID()
		known[file.path] = id
		kind := "module"
		if strings.HasSuffix(file.path, "/page.tsx") || file.path == "app/page.tsx" || file.path == "src/app/page.tsx" {
			kind = "next_page"
		}
		if _, supported := nextRoutePath(file.path); supported {
			kind = "next_route_module"
		}
		result.Nodes = append(result.Nodes, graphNode{ID: id, Kind: kind, Label: file.path, Evidence: evidenceAt(file, 1), Provenance: "deterministic", Confidence: map[string]any{"value": 1.0, "method": "static-file-match"}})
	}
	for _, file := range files {
		from := known[file.path]
		for _, match := range importPattern.FindAllSubmatchIndex(file.content, -1) {
			spec := string(file.content[match[2]:match[3]])
			to := resolveImport(file.path, spec, known)
			if to == "" {
				continue
			}
			result.Edges = append(result.Edges, graphEdge{ID: newUUID(), FromNodeID: from, ToNodeID: to, Kind: "imports", Provenance: "deterministic", Evidence: evidenceAt(file, lineAt(file.content, match[0]))})
		}
		if routePath, supported := nextRoutePath(file.path); supported {
			masked := maskNonCode(file.content)
			for _, match := range routePattern.FindAllSubmatchIndex(masked, -1) {
				methodStart, methodEnd := match[2], match[3]
				if methodStart < 0 {
					methodStart, methodEnd = match[4], match[5]
				}
				method := string(file.content[methodStart:methodEnd])
				routeID := newUUID()
				ev := evidenceAt(file, lineAt(file.content, match[0]))
				result.Nodes = append(result.Nodes, graphNode{ID: routeID, Kind: "http_route", Label: method + " " + routePath, Evidence: ev, Provenance: "deterministic", Confidence: map[string]any{"value": 1.0, "method": "next-route-export-v2"}})
				result.Edges = append(result.Edges, graphEdge{ID: newUUID(), FromNodeID: from, ToNodeID: routeID, Kind: "declares", Provenance: "deterministic", Evidence: ev})
			}
		}
	}
	return result, nil
}
