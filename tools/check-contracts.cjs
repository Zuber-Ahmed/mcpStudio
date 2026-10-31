// Offline foundation integrity check; not a full OpenAPI validator.
const fs = require('node:fs');
const path = require('node:path');
const crypto = require('node:crypto');
const root = path.resolve(__dirname, '..');
const base = path.join(root, 'packages/contracts');
const manifest = JSON.parse(fs.readFileSync(path.join(base,'source-manifest.json'),'utf8'));
let failures = [];
for (const item of manifest) {
  const target = path.resolve(base,item.path);
  if(!target.startsWith(base+path.sep)) { failures.push(`Unsafe manifest path: ${item.path}`); continue; }
  if(!fs.existsSync(target)) { failures.push(`Missing ${item.path}`); continue; }
  const actual = crypto.createHash('sha256').update(fs.readFileSync(target)).digest('hex');
  if(actual !== item.sha256) failures.push(`Changed ${item.path}`);
}
const api=JSON.parse(fs.readFileSync(path.join(base,'specs/openapi.yaml'),'utf8'));
const bootstrap=JSON.parse(fs.readFileSync(path.join(base,'specs/bootstrap.openapi.yaml'),'utf8'));
const count = d => Object.values(d.paths).reduce((n,x)=>n+Object.keys(x).length,0);
if(count(api)!==24 || count(bootstrap)!==3) failures.push('Unexpected operation counts');
if(failures.length) { console.error(failures.join('\n')); process.exitCode=1; }
else console.log(`Contract copies match ${manifest.length} source hashes; 24 resource + 3 session operations. See docs/quality/final-readiness-review.json for separately scoped validation and runtime evidence.`);
