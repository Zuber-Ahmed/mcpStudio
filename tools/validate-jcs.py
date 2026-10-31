"""Selected RFC 8785 numeric/Unicode vectors through two independent libraries."""
import json
import hashlib
import subprocess
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'work/python-tools'))
import rfc8785

vectors=[
 {'name':'object key sorting','value':{'b':2,'a':1},'expected':'{"a":1,"b":2}'},
 {'name':'RFC numeric serialization','value':[333333333.33333329,1e30,4.50,2e-3,1e-27],
  'expected':'[333333333.3333333,1e+30,4.5,0.002,1e-27]'},
 {'name':'negative zero','value':[-0.0,0.0],'expected':'[0,0]'},
 {'name':'UTF16 key order','value':{'\ufb33':7,'\U0001f600':6,'\u20ac':5,'ö':4,'\u0080':3,'1':2,'\r':1},
  'expected':'{"\\r":1,"1":2,"\u0080":3,"ö":4,"€":5,"😀":6,"דּ":7}'},
 {'name':'control escapes','value':{'s':'\b\t\n\f\r"\\'},'expected':'{"s":"\\b\\t\\n\\f\\r\\"\\\\"}'},
 {'name':'ordered arrays retained','value':{'args':['--stdio','--safe']},'expected':'{"args":["--stdio","--safe"]}'},
 {'name':'no Unicode normalization','value':['é','e\u0301'],'expected':'["é","é"]'}
]
(ROOT/'docs/quality/jcs-vectors.json').write_text(json.dumps(vectors,ensure_ascii=True,indent=2)+'\n')
node=subprocess.run(['node',str(ROOT/'tools/verify-jcs.cjs')],capture_output=True,text=True,encoding="utf-8")
if node.returncode:
    raise RuntimeError(node.stderr)
node_results={x['name']:x for x in json.loads(node.stdout)}
results=[]
for v in vectors:
    actual=rfc8785.dumps(v['value']).decode('utf-8')
    other=node_results[v['name']]['canonical']
    results.append({'name':v['name'],'passed':actual==v['expected']==other,
        'python':actual,'javascript':other,'sha256':hashlib.sha256(actual.encode()).hexdigest()})
for name,value in [('NaN',float('nan')),('Infinity',float('inf')),('unsafe integer',2**53),('unpaired surrogate','\ud800')]:
    rejected=False
    try: rfc8785.dumps(value)
    except (ValueError,UnicodeError): rejected=True
    if name in node_results:
        rejected=rejected and node_results[name]['rejected']
    results.append({'name':name+' rejected','passed':rejected,
                    'scope':'both libraries' if name in node_results else 'Python library boundary'})
report={'scope':'Selected RFC numeric/Unicode canonicalization vectors; no runtime plan approval proof',
    'libraries':{'python':'rfc8785 0.1.4','javascript':'canonicalize 2.1.0'},
    'source':'https://www.rfc-editor.org/rfc/rfc8785',
    'passed':all(x['passed'] for x in results),'checks':results}
(ROOT/'docs/quality/jcs-validation.json').write_text(json.dumps(report,ensure_ascii=True,indent=2)+'\n')
print(json.dumps({'passed':report['passed'],'checks':len(results),'failures':[x for x in results if not x['passed']]}))
raise SystemExit(0 if report['passed'] else 1)
