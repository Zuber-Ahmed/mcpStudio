"use client";
import "./architecture.css";
import "./studio.css";
import {FormEvent,useCallback,useEffect,useMemo,useState} from "react";
type Source={kind:"local"|"git";location:string;revision?:string};
type Project={id:string;name:string;source:Source;created_at:string;updated_at:string;workflow_status:"created"|"analyzed";latest_analysis_id:string|null};
type Session={csrf_token:string;expires_at:string};
type Evidence={path:string;source_digest:string;line_start:number;line_end:number;detector_version:string};
type GraphNode={id:string;kind:string;label:string;evidence:Evidence[];provenance:"deterministic";confidence:{value:number;method:string}};
type GraphEdge={id:string;from_node_id:string;to_node_id:string;kind:string;provenance:"deterministic";evidence:Evidence[]};
type Analysis={id:string;project_id:string;snapshot_id:string;source_digest:string;resolved_revision:string;status:"succeeded";created_at:string;completed_at:string;scope:{file_count:number;total_bytes:number;extensions:string[]};node_count:number;edge_count:number;diagnostics:unknown[]};
type Graph={analysis_id:string;nodes:GraphNode[];edges:GraphEdge[];truncated:false};
type Candidate={id:string;finding_id:string;graph_node_id:string;operation_type:"read"|"write"|"unknown";side_effects:string[];sensitivity:"public"|"internal"|"sensitive"|"unknown";required_scopes:string[];input_schema:Record<string,unknown>;output_schema:Record<string,unknown>;eligibility:"allowed"|"blocked"|"unsupported"|"unknown";reason_codes:string[];evidence:Evidence[];detector:{id:string;version:string};provenance:"deterministic"|"manual";domain_service_reference:string;adjudication?:{source_candidate_id:string;authorization_basis:string;security_confirmed:true}};
type Recommendation={id:string;analysis_id:string;version:number;source_digest:string;recommended_type:"server"|"client"|"both"|"none";rationale:string;candidate_ids:string[];risks:string[];required_reviews:string[];supported_generation:false;availability_reason:string};
type Plan={id:string;analysis_id:string;version:number;integration_type:"server";capability_ids:string[];status:"draft"|"approved"|"superseded"|"revoked";content_hash:string;canonicalization:string;policy_version:string;rationale:string;risks:string[]};
type Approval={id:string;plan_id:string;plan_version:number;plan_hash:string;security_confirmed:true;approved_at:string;status:"approved"};
type Screen="dashboard"|"setup"|"architecture"|"studio"|"results";
const screens:[Screen,string][]=[["dashboard","Dashboard"],["setup","Project Setup"],["architecture","Architecture Explorer"],["studio","MCP Studio"],["results","Results & Validation"]];
async function request<T>(path:string,init?:RequestInit):Promise<T>{const res=await fetch(path,{credentials:"same-origin",...init});if(!res.ok){const value=await res.json().catch(()=>({message:`Request failed (${res.status})`}));throw new Error(value.message)}return res.status===204?undefined as T:res.json()}
function nonce(){const bytes=new Uint8Array(32);crypto.getRandomValues(bytes);return btoa(String.fromCharCode(...bytes)).replaceAll("+","-").replaceAll("/","_").replaceAll("=","")}

export default function App(){
 const [session,setSession]=useState<Session|null|undefined>(undefined),[projects,setProjects]=useState<Project[]>([]),[screen,setScreen]=useState<Screen>("dashboard"),[query,setQuery]=useState(""),[error,setError]=useState("");
 const load=useCallback(async(q="")=>{const data=await request<{items:Project[]}>(`/v1/projects?limit=100&q=${encodeURIComponent(q)}`);setProjects(data.items)},[]);
 useEffect(()=>{request<Session>("/v1/local-session").then(s=>{setSession(s);return load()}).catch(()=>setSession(null))},[load]);
 if(session===undefined)return <main className="center"><div className="spinner"/><p>Opening local workspace…</p></main>;
 if(!session)return <Connect onConnect={async code=>{setError("");try{const s=await request<Session>("/v1/local-session/exchange",{method:"POST",headers:{"Content-Type":"application/json",Origin:location.origin},body:JSON.stringify({one_time_code:code,browser_nonce:nonce()})});setSession(s);await load()}catch(e){setError((e as Error).message)}}} error={error}/>;
 const filtered=projects.filter(p=>p.name.toLowerCase().includes(query.toLowerCase()));
	 return <div className="shell"><aside><div className="brand"><span className="mark">M</span><div><strong>MCP Studio</strong><small>Local workspace</small></div></div><nav>{screens.map(([id,label],i)=><button key={id} className={screen===id?"active":""} onClick={()=>setScreen(id)}><span>{i+1}</span>{label}{i>3&&<em>Next</em>}</button>)}</nav><div className="local"><span/>Local only · No telemetry</div></aside><main><header><div><small>WORKSPACE / LOCAL</small><h1>{screens.find(([id])=>id===screen)?.[1]}</h1></div><button className="ghost" onClick={async()=>{await request("/v1/local-session/logout",{method:"DELETE",headers:{Origin:location.origin,"X-CSRF-Token":session.csrf_token}});setSession(null)}}>Lock workspace</button></header>{screen==="dashboard"&&<Dashboard projects={filtered} query={query} setQuery={setQuery} openSetup={()=>setScreen("setup")} openArchitecture={()=>setScreen("architecture")}/>} {screen==="setup"&&<ProjectSetup csrf={session.csrf_token} onCreated={async()=>{await load();setScreen("dashboard")}}/>}{screen==="architecture"&&<Architecture projects={projects} csrf={session.csrf_token} refreshProjects={()=>load()}/>} {screen==="studio"&&<MCPStudio projects={projects} csrf={session.csrf_token}/>} {screen==="results"&&<Pending screen={screen}/>}</main></div>
}
function Connect({onConnect,error}:{onConnect:(code:string)=>void;error:string}){const[code,setCode]=useState("");return <main className="center"><section className="connect"><div className="mark large">M</div><p className="eyebrow">LOCAL-FIRST WORKSPACE</p><h1>Connect MCP Studio</h1><p>Enter the one-time code from <code>.local/api/bootstrap-code.txt</code>. It expires after ten minutes and cannot be reused.</p><form onSubmit={e=>{e.preventDefault();onConnect(code)}}><label>One-time bootstrap code<input autoFocus value={code} onChange={e=>setCode(e.target.value.trim())} minLength={43} maxLength={43}/></label>{error&&<p className="error">{error}</p>}<button disabled={code.length!==43}>Open local workspace</button></form></section></main>}
function Dashboard({projects,query,setQuery,openSetup,openArchitecture}:{projects:Project[];query:string;setQuery:(s:string)=>void;openSetup:()=>void;openArchitecture:()=>void}){return <div className="content"><section className="hero"><div><p className="eyebrow">PROJECT REGISTRY</p><h2>Integration projects</h2><p>Register a source, then create a read-only snapshot and inspect deterministic architecture evidence.</p></div><button onClick={openSetup}>+ New project</button></section><section className="stats"><article><strong>{projects.length}</strong><span>Registered projects</span></article><article><strong>{projects.filter(p=>p.workflow_status==="created").length}</strong><span>Awaiting analysis</span></article><article><strong>{projects.filter(p=>p.workflow_status==="analyzed").length}</strong><span>Analyzed projects</span></article></section><section className="panel"><div className="toolbar"><div><h3>Projects</h3><small>PostgreSQL-backed registry</small></div><input aria-label="Search projects" placeholder="Search projects…" value={query} onChange={e=>setQuery(e.target.value)}/></div>{projects.length===0?<div className="empty"><span>◇</span><h3>No projects registered</h3><p>Create the first project to verify the running UI → API → PostgreSQL flow.</p><button onClick={openSetup}>Create project</button></div>:<div className="table"><div className="row heading"><span>Project</span><span>Source</span><span>Status</span><span>Updated</span></div>{projects.map(p=><button className="row project-row" key={p.id} onClick={openArchitecture}><span><b>{p.name}</b><small>{p.id.slice(0,8)}</small></span><span><b>{p.source.kind}</b><small title={p.source.location}>{p.source.location}</small></span><span><i className={p.workflow_status}>{p.workflow_status==="analyzed"?"Analyzed":"Created"}</i></span><span>{new Date(p.updated_at).toLocaleString()}</span></button>)}</div>}</section></div>}
function ProjectSetup({csrf,onCreated}:{csrf:string;onCreated:()=>void}){const[name,setName]=useState(""),[kind,setKind]=useState<"local"|"git">("local"),[location,setLocation]=useState(""),[revision,setRevision]=useState(""),[busy,setBusy]=useState(false),[error,setError]=useState("");async function submit(e:FormEvent){e.preventDefault();setBusy(true);setError("");try{const source:Source={kind,location};if(kind==="git")source.revision=revision;await request("/v1/projects",{method:"POST",headers:{"Content-Type":"application/json",Origin:window.location.origin,"X-CSRF-Token":csrf},body:JSON.stringify({name,source})});onCreated()}catch(e){setError((e as Error).message)}finally{setBusy(false)}}return <div className="content narrow"><div className="hero"><div><p className="eyebrow">STEP 1 OF 5</p><h2>Register a project</h2><p>Register the immutable source identity. Local folders can be analyzed in Architecture Explorer.</p></div></div><form className="form panel" onSubmit={submit}><label>Project name<input value={name} onChange={e=>setName(e.target.value)} maxLength={200} required placeholder="Customer support service"/></label><fieldset><legend>Source type</legend><button type="button" className={kind==="local"?"selected":""} onClick={()=>setKind("local")}>Local folder</button><button type="button" className={kind==="git"?"selected":""} onClick={()=>setKind("git")}>Git repository</button></fieldset><label>{kind==="local"?"Absolute folder path":"Repository URL"}<input value={location} onChange={e=>setLocation(e.target.value)} required placeholder={kind==="local"?"C:\\projects\\service":"https://example.com/team/service.git"}/></label>{kind==="git"&&<label>Immutable revision<input value={revision} onChange={e=>setRevision(e.target.value)} required placeholder="Commit SHA"/></label>}<div className="notice"><b>Data boundary</b><p>Analysis reads supported source files without executing repository scripts. Git acquisition remains unavailable in this slice.</p></div>{error&&<p className="error">{error}</p>}<button disabled={busy}>{busy?"Registering…":"Register project"}</button></form></div>}

function Architecture({projects,csrf,refreshProjects}:{projects:Project[];csrf:string;refreshProjects:()=>Promise<void>}){
 const local=useMemo(()=>projects.filter(p=>p.source.kind==="local"),[projects]);
 const [selected,setSelected]=useState(local[0]?.id??""),[analysis,setAnalysis]=useState<Analysis|null>(null),[graph,setGraph]=useState<Graph|null>(null),[busy,setBusy]=useState(false),[error,setError]=useState("");
 const project=local.find(p=>p.id===selected);
 const loadAnalysis=useCallback(async(id:string)=>{const [a,g]=await Promise.all([request<Analysis>(`/v1/analyses/${id}`),request<Graph>(`/v1/analyses/${id}/graph`)]);setAnalysis(a);setGraph(g)},[]);
 useEffect(()=>{setAnalysis(null);setGraph(null);setError("");const next=local.find(p=>p.id===selected);if(next?.latest_analysis_id)loadAnalysis(next.latest_analysis_id).catch(e=>setError((e as Error).message))},[selected,local,loadAnalysis]);
 async function analyze(){if(!project)return;setBusy(true);setError("");try{const a=await request<Analysis>("/v1/analyses",{method:"POST",headers:{"Content-Type":"application/json",Origin:location.origin,"X-CSRF-Token":csrf,"Idempotency-Key":nonce()+nonce()},body:JSON.stringify({project_id:project.id})});await loadAnalysis(a.id);await refreshProjects()}catch(e){setError((e as Error).message)}finally{setBusy(false)}}
 return <div className="content architecture"><section className="hero"><div><p className="eyebrow">STEP 2 OF 5 · DETERMINISTIC</p><h2>Architecture evidence</h2><p>Read-only TypeScript and Next.js analysis. No repository scripts, dependency installs, or remote inference.</p></div><button disabled={!project||busy} onClick={analyze}>{busy?"Analyzing…":analysis?"Create new snapshot":"Analyze source"}</button></section>{local.length===0?<section className="pending"><h2>No local project available</h2><p>Register a local folder in Project Setup. Git acquisition is intentionally not active yet.</p></section>:<><section className="panel source-picker"><label>Project<select value={selected} onChange={e=>setSelected(e.target.value)}>{local.map(p=><option key={p.id} value={p.id}>{p.name}</option>)}</select></label><div><b>{project?.source.location}</b><small>Canonical root is resolved and enforced by the API</small></div></section>{error&&<p className="error">{error}</p>}{!analysis?<section className="pending"><h2>Ready for a read-only snapshot</h2><p>The analyzer includes supported TypeScript, JavaScript and JSON files, rejects symbolic-link escapes, and applies file and byte limits.</p></section>:<><section className="analysis-stats"><article><span>Snapshot</span><b title={analysis.source_digest}>{analysis.source_digest.slice(0,16)}…</b></article><article><span>Files</span><b>{analysis.scope.file_count}</b></article><article><span>Nodes</span><b>{analysis.node_count}</b></article><article><span>Edges</span><b>{analysis.edge_count}</b></article></section><section className="graph-grid"><div className="panel"><div className="toolbar"><div><h3>Detected architecture</h3><small>Every node includes source evidence</small></div></div><div className="node-list">{graph?.nodes.map(n=><article key={n.id}><span className="kind">{n.kind.replaceAll("_"," ")}</span><b>{n.label}</b><small>{n.evidence[0]?.path}:{n.evidence[0]?.line_start} · {n.provenance}</small></article>)}</div></div><div className="panel"><div className="toolbar"><div><h3>Relationships</h3><small>Resolved local imports and route declarations</small></div></div><div className="edge-list">{graph?.edges.length?graph.edges.map(e=>{const from=graph.nodes.find(n=>n.id===e.from_node_id)?.label;const to=graph.nodes.find(n=>n.id===e.to_node_id)?.label;return <article key={e.id}><span>{e.kind}</span><b>{from}</b><small>→ {to}</small></article>}):<p>No local relationships detected.</p>}</div></div></section></>}</>}</div>
}
function MCPStudio({projects,csrf}:{projects:Project[];csrf:string}){
 const analyzed=useMemo(()=>projects.filter(p=>p.latest_analysis_id),[projects]);
 const [selected,setSelected]=useState(analyzed[0]?.id??"");
 const [candidates,setCandidates]=useState<Candidate[]>([]);
 const [recommendation,setRecommendation]=useState<Recommendation|null>(null);
 const [selectedCandidates,setSelectedCandidates]=useState<string[]>([]);
 const [plan,setPlan]=useState<Plan|null>(null);
 const [securityConfirmed,setSecurityConfirmed]=useState(false);
 const [reviewing,setReviewing]=useState<string|null>(null);
 const [authorizationBasis,setAuthorizationBasis]=useState("");
 const [domainReference,setDomainReference]=useState("verified:");
 const [reviewSensitivity,setReviewSensitivity]=useState<"public"|"internal"|"sensitive">("internal");
 const [requiredScopes,setRequiredScopes]=useState("");
 const [inputSchema,setInputSchema]=useState('{"type":"object","additionalProperties":false}');
 const [outputSchema,setOutputSchema]=useState('{"type":"object","additionalProperties":false}');
 const [mappingConfirmed,setMappingConfirmed]=useState(false);
 const [busy,setBusy]=useState(false),[error,setError]=useState("");
 const project=analyzed.find(p=>p.id===selected);const analysisId=project?.latest_analysis_id;
 const load=useCallback(async(id:string)=>{
  const data=await request<{items:Candidate[]}>(`/v1/analyses/${id}/candidates`);
  setCandidates(data.items);
  setSelectedCandidates(data.items.filter(c=>c.eligibility==="allowed"&&!c.domain_service_reference.startsWith("unresolved:")).map(c=>c.id));
  if(data.items.length){
   setRecommendation(await request<Recommendation>(`/v1/analyses/${id}/recommendation`));
   request<Plan>(`/v1/analyses/${id}/plan`).then(setPlan).catch(()=>setPlan(null));
  }else{setRecommendation(null);setPlan(null)}
 },[]);
 useEffect(()=>{
  setCandidates([]);setRecommendation(null);setSelectedCandidates([]);setPlan(null);setSecurityConfirmed(false);
  setReviewing(null);setMappingConfirmed(false);setError("");
  if(analysisId)load(analysisId).catch(e=>setError((e as Error).message));
 },[analysisId,load]);
 async function discover(){
  if(!analysisId)return;setBusy(true);setError("");
  try{
   const data=await request<{candidates:Candidate[];recommendation:Recommendation}>(`/v1/analyses/${analysisId}/candidate-discovery`,{method:"POST",headers:{Origin:location.origin,"X-CSRF-Token":csrf}});
   setCandidates(data.candidates);setRecommendation(data.recommendation);
   setSelectedCandidates(data.candidates.filter(c=>c.eligibility==="allowed"&&!c.domain_service_reference.startsWith("unresolved:")).map(c=>c.id));
  }catch(e){setError((e as Error).message)}finally{setBusy(false)}
 }
 async function adjudicate(candidate:Candidate){
  setBusy(true);setError("");
  try{
   const input=JSON.parse(inputSchema),output=JSON.parse(outputSchema);
   await request<Candidate>(`/v1/candidates/${candidate.id}/adjudication`,{method:"POST",headers:{"Content-Type":"application/json",Origin:location.origin,"X-CSRF-Token":csrf},body:JSON.stringify({
    authorization_basis:authorizationBasis,sensitivity:reviewSensitivity,domain_service_reference:domainReference,
    required_scopes:requiredScopes.split(",").map(v=>v.trim()).filter(Boolean),input_schema:input,output_schema:output,security_confirmed:mappingConfirmed
   })});
   if(analysisId)await load(analysisId);
   setReviewing(null);setMappingConfirmed(false);setAuthorizationBasis("");setDomainReference("verified:");
  }catch(e){setError((e as Error).message)}finally{setBusy(false)}
 }
 async function createPlan(){
  if(!analysisId||!selectedCandidates.length)return;setBusy(true);setError("");
  try{
   const next=await request<Plan>("/v1/plans",{method:"POST",headers:{"Content-Type":"application/json",Origin:location.origin,"X-CSRF-Token":csrf},body:JSON.stringify({analysis_id:analysisId,candidate_ids:selectedCandidates})});
   setPlan(next);setSecurityConfirmed(false);
  }catch(e){setError((e as Error).message)}finally{setBusy(false)}
 }
 async function approve(){
  if(!plan||!securityConfirmed)return;setBusy(true);setError("");
  try{
   await request<Approval>(`/v1/plans/${plan.id}/approval`,{method:"POST",headers:{"Content-Type":"application/json",Origin:location.origin,"X-CSRF-Token":csrf},body:JSON.stringify({plan_version:plan.version,content_hash:plan.content_hash,security_confirmed:true})});
   setPlan(await request<Plan>(`/v1/plans/${plan.id}`));
  }catch(e){setError((e as Error).message)}finally{setBusy(false)}
 }
 const counts={allowed:candidates.filter(c=>c.eligibility==="allowed").length,unknown:candidates.filter(c=>c.eligibility==="unknown").length,blocked:candidates.filter(c=>c.eligibility==="blocked").length};
 return <div className="content studio">
  <section className="hero"><div><p className="eyebrow">STEP 3 OF 5 · VERIFIED REVIEW</p><h2>MCP plan review</h2><p>Route evidence stays review-only until an operator records exact security and domain mapping evidence.</p></div><button disabled={!analysisId||busy} onClick={discover}>{busy?"Working…":candidates.length?"Refresh discovery":"Discover candidates"}</button></section>
  {!analyzed.length?<section className="pending"><h2>No completed analysis</h2><p>Run Architecture Explorer before discovering MCP candidates.</p></section>:<>
   <section className="panel source-picker"><label>Analyzed project<select value={selected} onChange={e=>setSelected(e.target.value)}>{analyzed.map(p=><option key={p.id} value={p.id}>{p.name}</option>)}</select></label><div><b>{analysisId}</b><small>Exact immutable analysis used for this review</small></div></section>
   {error&&<p className="error">{error}</p>}
   {!candidates.length?<section className="pending"><h2>No route candidates recorded</h2><p>Run deterministic discovery. Comments, strings and unsupported route layouts cannot create candidate authority.</p></section>:<>
    <section className="candidate-stats"><article><b>{counts.allowed}</b><span>Verified mappings</span></article><article><b>{counts.unknown}</b><span>Needs review</span></article><article><b>{counts.blocked}</b><span>Blocked writes</span></article></section>
    <section className="studio-grid">
     <div className="panel candidate-list"><div className="toolbar"><div><h3>Evidence-backed candidates</h3><small>Only immutable operator-adjudicated reads may enter a plan</small></div></div>
      {candidates.map(c=>{const selectable=c.eligibility==="allowed"&&c.provenance==="manual"&&!c.domain_service_reference.startsWith("unresolved:");const canReview=c.operation_type==="read"&&c.eligibility==="unknown"&&c.provenance==="deterministic";return <article key={c.id}>
       <div>{selectable&&<input aria-label={`Select ${c.finding_id}`} type="checkbox" checked={selectedCandidates.includes(c.id)} disabled={Boolean(plan)} onChange={e=>setSelectedCandidates(e.target.checked?[...selectedCandidates,c.id]:selectedCandidates.filter(id=>id!==c.id))}/>}<span className={`eligibility ${c.eligibility}`}>{c.eligibility}</span><b>{c.finding_id.replace("http-route:","")}</b>{canReview&&<button className="review-trigger" onClick={()=>setReviewing(reviewing===c.id?null:c.id)}>Review mapping</button>}</div>
       <dl><dt>Operation</dt><dd>{c.operation_type}</dd><dt>Sensitivity</dt><dd>{c.sensitivity}</dd><dt>Mapping</dt><dd>{c.domain_service_reference}</dd><dt>Evidence</dt><dd>{c.evidence[0]?.path}:{c.evidence[0]?.line_start}</dd><dt>Provenance</dt><dd>{c.provenance} · {c.detector.version}</dd><dt>Reasons</dt><dd>{c.reason_codes.join(", ")}</dd></dl>
       {reviewing===c.id&&<div className="adjudication-form"><h4>Immutable operator adjudication</h4><p>Do not use a route name as evidence. Record the actual application authorization and domain-service boundary.</p>
        <label>Authorization basis<textarea value={authorizationBasis} onChange={e=>setAuthorizationBasis(e.target.value)} placeholder="Describe the enforced caller identity, tenant boundary and read authorization (minimum 20 characters)."/></label>
        <label>Verified domain service<input value={domainReference} onChange={e=>setDomainReference(e.target.value)} placeholder="verified:service.health.read"/></label>
        <label>Data sensitivity<select value={reviewSensitivity} onChange={e=>setReviewSensitivity(e.target.value as typeof reviewSensitivity)}><option value="public">Public</option><option value="internal">Internal</option><option value="sensitive">Sensitive</option></select></label>
        <label>Required scopes<input value={requiredScopes} onChange={e=>setRequiredScopes(e.target.value)} placeholder="health:read, tenant:read"/></label>
        <label>Input JSON Schema<textarea className="schema-input" value={inputSchema} onChange={e=>setInputSchema(e.target.value)}/></label>
        <label>Output JSON Schema<textarea className="schema-input" value={outputSchema} onChange={e=>setOutputSchema(e.target.value)}/></label>
        <label className="security-check"><input type="checkbox" checked={mappingConfirmed} onChange={e=>setMappingConfirmed(e.target.checked)}/> I verified the source evidence, authorization boundary, sensitivity, scopes, schemas and domain-service mapping.</label>
        <button disabled={busy||!mappingConfirmed||authorizationBasis.trim().length<20||!domainReference.startsWith("verified:")} onClick={()=>adjudicate(c)}>Record immutable adjudication</button>
       </div>}
      </article>})}
     </div>
     <aside className="panel review-panel"><p className="eyebrow">{plan?`PLAN V${plan.version}`:`RECOMMENDATION V${recommendation?.version}`}</p>
      {plan?<><h3 className={plan.status==="approved"?"approved-title":""}>{plan.status==="approved"?"Exact plan approved":"Immutable draft plan"}</h3><p className="plan-hash" title={plan.content_hash}>{plan.content_hash}</p><dl className="plan-facts"><dt>Policy</dt><dd>{plan.policy_version}</dd><dt>Transport</dt><dd>stdio</dd><dt>Candidates</dt><dd>{plan.capability_ids.length}</dd></dl>{plan.status==="draft"&&<><label className="security-check"><input type="checkbox" checked={securityConfirmed} onChange={e=>setSecurityConfirmed(e.target.checked)}/> I reviewed the exact candidate evidence, mappings, policy and plan hash.</label><button className="approve-button" disabled={!securityConfirmed||busy} onClick={approve}>Approve exact plan</button></>}<div className="generation-lock"><b>Generation unavailable</b><p>Approval does not execute generation. Independent QA sign-off remains required.</p></div></>:<><h3>{counts.allowed?"Verified server candidate":"No executable fit"}</h3><p>{counts.allowed?"An operator-adjudicated read can now enter an exact plan.":recommendation?.rationale}</p><h4>Required reviews</h4><ul>{recommendation?.required_reviews.map(r=><li key={r}>{r}</li>)}</ul><button className="plan-button" disabled={!selectedCandidates.length||busy} onClick={createPlan}>Create exact draft plan</button><div className="generation-lock"><b>Generation locked</b><p>Mapping and plan approval do not bypass independent QA or isolated-generation controls.</p></div></>}
     </aside>
    </section>
   </>}
  </>}
 </div>
}

function Pending({screen}:{screen:Screen}){return <div className="content"><section className="pending"><p className="eyebrow">IMPLEMENTATION STATUS</p><h2>Validation and artifact review</h2><p>This screen is part of the approved five-screen design. Its backend behavior has not been implemented, so no sample success data is shown.</p><div><span>Current</span><b>Exact plan binding and explicit security approval</b></div><div><span>Next</span><b>Isolated generation with an artifact manifest and no source writes</b></div></section></div>}
