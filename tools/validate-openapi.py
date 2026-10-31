"""Full OpenAPI meta-schema and instance-fixture checks using isolated dev tools."""
import json
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'work/python-tools'))
from openapi_spec_validator import validate_spec
from openapi_schema_validator import OAS30Validator
from jsonschema import RefResolver

documents={name:json.loads((ROOT/'packages/contracts/specs'/name).read_text())
           for name in ['openapi.yaml','bootstrap.openapi.yaml']}
results=[]
for name, doc in documents.items():
    try:
        validate_spec(doc)
        results.append({'check':'full OpenAPI 3.0 schema:'+name,'passed':True})
    except Exception as ex:
        results.append({'check':'full OpenAPI 3.0 schema:'+name,'passed':False,'error':str(ex)})
fixtures=json.loads((ROOT/'docs/milestones/M0.3/contract-fixtures.json').read_text())
for case in fixtures:
    if 'schema' not in case:
        continue # Reference-oracle cases are not schema/server enforcement tests.
    doc=next(d for d in documents.values() if case['schema'] in d['components']['schemas'])
    schema=doc['components']['schemas'][case['schema']]
    validator=OAS30Validator(schema,resolver=RefResolver.from_schema(doc),format_checker=OAS30Validator.FORMAT_CHECKER)
    errors=list(validator.iter_errors(case['value']))
    actual=not errors
    results.append({'check':'OAS instance:'+case['name'],'passed':actual==case['expected'],
                    'valid':actual,'expected':case['expected'],
                    'errors':[e.message for e in errors] if actual!=case['expected'] else []})
out={'scope':'OpenAPI meta-schema and selected request/record fixtures, not API runtime',
     'validator':'openapi-spec-validator 0.7.2 / openapi-schema-validator 0.6.3',
     'passed':all(r['passed'] for r in results),'checks':results,'runtime_tests':0}
(ROOT/'docs/quality/openapi-validation.json').write_text(json.dumps(out,indent=2)+'\n')
print(json.dumps({'passed':out['passed'],'checks':len(results),'failures':[r for r in results if not r['passed']]},indent=2))
raise SystemExit(0 if out['passed'] else 1)
