package main
import("os";"path/filepath";"strings";"testing")
func TestQAReturnRegexLiteralCannotCreateRoute(t *testing.T){
 root:=fixture(t,"app/api/health/route.ts","export const marker = () => { return /export async function GET/; };\n")
 a,err:=acquireAndAnalyze("qa",root);if err!=nil{t.Fatal(err)}
 for _,n:=range a.Nodes{if n.Kind=="http_route"{t.Fatalf("regex literal after return created phantom route %q",n.Label)}}
}
func TestQAUnsupportedIgnorePatternFailsClosed(t *testing.T){
 root:=fixture(t,"app/api/health/route.ts","export async function GET() { return Response.json({ok:true}) }")
 os.MkdirAll(filepath.Join(root,"config"),0755)
 os.WriteFile(filepath.Join(root,".gitignore"),[]byte("**/secrets.json\n"),0600)
 os.WriteFile(filepath.Join(root,"config","secrets.json"),[]byte(`{"secret":"synthetic-canary"}`),0600)
 files,_,_,err:=readSnapshot(root);if err!=nil{return}
 for _,f:=range files{if strings.HasSuffix(f.path,"secrets.json"){t.Fatalf("unsupported ignore rule silently discarded and secret file acquired: %s",f.path)}}
}
