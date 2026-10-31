const fs = require('node:fs');
const path = require('node:path');
const canonicalize = require('../work/node-tools/node_modules/canonicalize');
const root = path.resolve(__dirname,'..');
const vectors = JSON.parse(fs.readFileSync(path.join(root,'docs/quality/jcs-vectors.json'),'utf8'));
let results = vectors.map(v=>({name:v.name,canonical:canonicalize(v.value)}));
for(const [name,value] of [['NaN',NaN],['Infinity',Infinity]]) {
  let rejected=false;
  try { canonicalize(value); } catch { rejected=true; }
  results.push({name,rejected});
}
process.stdout.write(JSON.stringify(results));
