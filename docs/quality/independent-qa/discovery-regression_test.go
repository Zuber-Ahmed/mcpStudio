package main

import (
 "os"
 "path/filepath"
 "strings"
 "testing"
)

func fixture(t *testing.T, path, source string) string {
 t.Helper(); root:=t.TempDir(); target:=filepath.Join(root,filepath.FromSlash(path))
 if err:=os.MkdirAll(filepath.Dir(target),0755);err!=nil{t.Fatal(err)}
 if err:=os.WriteFile(target,[]byte(source),0600);err!=nil{t.Fatal(err)}
 return root
}
func TestQACommentCannotBecomeExecutableCandidate(t *testing.T){
 root:=fixture(t,"app/api/health/route.ts","// export async function GET() { return Response.json({ok:true}) }\nexport const marker = true\n")
 a,err:=acquireAndAnalyze("qa",root);if err!=nil{t.Fatal(err)}
 d:=discoverCandidates(a.ID,a.SourceDigest,a.Nodes)
 if len(d.Candidates)!=0{t.Fatalf("comment created %d candidates; eligibility=%s mapping=%s",len(d.Candidates),d.Candidates[0].Eligibility,d.Candidates[0].DomainServiceReference)}
}
func TestQASrcAppRouteIdentity(t *testing.T){
 root:=fixture(t,"src/app/api/health/route.ts","export async function GET() { return Response.json({ok:true}) }")
 a,err:=acquireAndAnalyze("qa",root);if err!=nil{t.Fatal(err)}
 for _,n:=range a.Nodes{if n.Kind=="http_route"{if n.Label!="GET /api/health"{t.Fatalf("wrong route identity %q",n.Label)};return}}
 t.Fatal("route missing")
}
func TestQARouteGroupNotURLSegment(t *testing.T){
 root:=fixture(t,"app/(internal)/api/health/route.ts","export async function GET() { return Response.json({ok:true}) }")
 a,err:=acquireAndAnalyze("qa",root);if err!=nil{t.Fatal(err)}
 for _,n:=range a.Nodes{if n.Kind=="http_route"{if n.Label!="GET /api/health"{t.Fatalf("route group leaked into URL %q",n.Label)};return}}
 t.Fatal("route missing")
}
func TestQAIgnoredLocalCredentialFilesExcluded(t *testing.T){
 root:=fixture(t,"app/api/health/route.ts","export async function GET() { return Response.json({ok:true}) }")
 if err:=os.MkdirAll(filepath.Join(root,".local"),0755);err!=nil{t.Fatal(err)}
 os.WriteFile(filepath.Join(root,".gitignore"),[]byte(".local/\n"),0600)
 os.WriteFile(filepath.Join(root,".local","credentials.json"),[]byte(`{"secret":"synthetic-qa-canary"}`),0600)
 files,_,_,err:=readSnapshot(root);if err!=nil{t.Fatal(err)}
 for _,f:=range files{if strings.HasPrefix(f.path,".local/"){t.Fatalf("ignored local credential file acquired: %s",f.path)}}
}
func TestQAGenerationRemainsLocked(t *testing.T){
 root:=fixture(t,"app/api/health/route.ts","export async function GET() { return Response.json({ok:true}) }")
 a,err:=acquireAndAnalyze("qa",root);if err!=nil{t.Fatal(err)}
 d:=discoverCandidates(a.ID,a.SourceDigest,a.Nodes)
 if len(d.Candidates)!=1||d.Recommendation.SupportedGeneration{t.Fatal("expected one candidate with generation locked")}
}
