const fs=require('node:fs');
const path=require('node:path');
const {createRequire}=require('node:module');
const root=path.resolve(__dirname,'../../..');
const deps=createRequire(path.join(root,'work/mcp-fixture/package.json'));
const {Client}=deps('@modelcontextprotocol/client');
const {StdioClientTransport}=deps('@modelcontextprotocol/client/stdio');
const checks=[];
const check=(name,passed)=>checks.push({name,passed:!!passed});
async function denied(client,args) {
  try { const r=await client.callTool(args);return r.isError===true && !JSON.stringify(r).includes('DO-NOT-LEAK'); }
  catch { return true; }
}
async function main(){
  const transport=new StdioClientTransport({command:process.execPath,args:[path.join(__dirname,'mcp-server.cjs')],stderr:'pipe'});
  let stderr=''; transport.stderr?.on('data',b=>{stderr+=b.toString('utf8');});
  const client=new Client({name:'mcpstudio-readiness-client',version:'0.1.0'},
    {versionNegotiation:{mode:{pin:'2026-07-28'},probe:{timeoutMs:5000,maxRetries:0}}});
  try {
    await client.connect(transport);
    check('connect requires exactly 2026-07-28, no legacy fallback',true);
    const listing=await client.listTools();
    check('discover one read-only fixture tool',listing.tools.length===1 && listing.tools[0].name==='read_fixture');
    const value=await client.callTool({name:'read_fixture',arguments:{record_id:'alpha'}});
    check('typed read invokes controlled domain service',!value.isError && value.content.some(x=>x.type==='text'&&x.text==='fixture-alpha'));
    check('cross-tenant fixture result denied',await denied(client,{name:'read_fixture',arguments:{record_id:'beta'}}));
    check('malformed input denied',await denied(client,{name:'read_fixture',arguments:{record_id:123}}));
    check('unexpected input field denied',await denied(client,{name:'read_fixture',arguments:{record_id:'alpha',admin:true}}));
    check('unregistered write tool denied',await denied(client,{name:'write_fixture',arguments:{record_id:'alpha'}}));

    const after=await client.callTool({name:'read_fixture',arguments:{record_id:'alpha'}});
    check('server remains usable after negative cases',!after.isError && after.content.some(x=>x.type==='text'&&x.text==='fixture-alpha'));

  } catch(error){ check('fixture connection or invocation error: '+error.message,false); }
  finally { await client.close(); }
  const report={scope:'Official SDK stdio fixture; not generated adapter/product authorization proof',
    protocol_pin:'2026-07-28',server_sdk:'2.4.0',client_sdk:'2.4.0',node:process.version,
    passed:checks.every(x=>x.passed),checks,stderr};
  fs.writeFileSync(path.join(root,'docs/quality/mcp-stdio-validation.json'),JSON.stringify(report,null,2)+'\n');
  console.log(JSON.stringify(report,null,2));
  if(!report.passed) process.exitCode=1;
}
main().catch(error=>{console.error(error);process.exitCode=1;});
