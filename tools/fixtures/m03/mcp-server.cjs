// Trusted M0.3 service fixture, not generated product code or repository analysis.
const path = require('node:path');
const { createRequire } = require('node:module');
const root = path.resolve(__dirname, '../../..');
const deps = createRequire(path.join(root, 'work/mcp-fixture/package.json'));
const { McpServer } = deps('@modelcontextprotocol/server');
const { serveStdio } = deps('@modelcontextprotocol/server/stdio');
const z = deps('zod/v4');
function createServer() {
  const server = new McpServer({ name:'mcpstudio-readiness-fixture', version:'0.1.0' },
    { supportedProtocolVersions:['2026-07-28'] });
  const operatorTenant='tenant-a';
  const records={ alpha:{ tenant:'tenant-a',value:'fixture-alpha' }, beta:{ tenant:'tenant-b',value:'DO-NOT-LEAK' } };
  server.registerTool('read_fixture', {
    description:'Read a controlled fixture through a tenant-scoped domain service.',
    inputSchema:z.object({ record_id:z.string().min(1) }).strict()
  }, async ({record_id}) => {
    const row=records[record_id];
    if(!row || row.tenant!==operatorTenant) return {isError:true,content:[{type:'text',text:'not_found_or_forbidden'}]};
    return {content:[{type:'text',text:row.value}]};
  });
  return server;
}
serveStdio(createServer, { legacy:'reject', onerror:err=>console.error(err.message) });
