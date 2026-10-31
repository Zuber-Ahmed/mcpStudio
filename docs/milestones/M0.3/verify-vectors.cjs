// Independent restricted ASCII/integer serialization check; not a JCS library.
const fs = require('node:fs');
const path = require('node:path');
const crypto = require('node:crypto');
const vectors = JSON.parse(fs.readFileSync(path.join(__dirname,'canonical-vectors.json'),'utf8'));
function ordered(x) {
  if (Array.isArray(x)) return x.map(ordered);
  if (x && typeof x === 'object') return Object.fromEntries(Object.keys(x).sort().map(k=>[k,ordered(x[k])]));
  return x;
}
for (const v of vectors) {
  const canonical=JSON.stringify(ordered(v.input));
  if(canonical!==v.canonical || crypto.createHash('sha256').update(canonical).digest('hex')!==v.sha256) process.exit(1);
}
process.stdout.write(`${vectors.length} restricted vectors agree\n`);
