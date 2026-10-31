"""Catalog-backed name mapping only; column presence is not semantic completion."""
from pathlib import Path
import hashlib,json
root=Path(__file__).resolve().parents[1]
catalog_path=root/'docs/quality/physical-schema-catalog.json'
catalog=json.loads(catalog_path.read_text(encoding='utf-8'))
logical_path=root/'packages/contracts/specs/data-dictionary.json'
logical=json.loads(logical_path.read_text(encoding='utf-8'))['entities']
tables={}
for c in catalog['columns']:tables.setdefault(c['table'],{})[c['column']]=c
names={'ARTIFACT':'artifact','FINDING':'finding','PLAN_REVOCATION':'plan_revocation','SOURCE_SNAPSHOT':'source_snapshot','GRAPH_NODE':'graph_node','GRAPH_EDGE':'graph_edge','RECOMMENDATION':'recommendation','TENANT':'tenant','USER':'actor','MEMBERSHIP':'membership','PROJECT':'project','ANALYSIS_RUN':'analysis','PLAN':'plan',
 'APPROVAL':'approval','GENERATION_RUN':'run','VALIDATION_RUN':'validation','VALIDATION_CHECK':'validation_check',
 'AUDIT_EVENT':'audit_event','CANDIDATE':'candidate','POLICY':'validation_policy','INFERENCE_CONSENT':'consent',
 'IDEMPOTENCY_RECORD':'idempotency','OUTBOX_EVENT':'outbox'}
aliases={'MEMBERSHIP':{'user_id':'actor_id'},'ANALYSIS_RUN':{'source_digest':'source_digest'},
 'PLAN':{'analysis_run_id':'analysis_id','content_hash':'plan_hash','is_current':'current'},
 'VALIDATION_RUN':{'generation_run_id':'run_id'},'VALIDATION_CHECK':{'validation_run_id':'validation_id'},
 'CANDIDATE':{'analysis_run_id':'analysis_id'},'IDEMPOTENCY_RECORD':{'operation_id':'operation','request_digest':'request_digest','resource_id':'run_id'},
 'OUTBOX_EVENT':{'id':'event_id','aggregate_id':'run_id'},'AUDIT_EVENT':{'action':'event_type','created_at':'recorded_at'}}
additional={'PLAN':{'canonical_payload':('plan_binding','canonical_payload'),'policy_id':('plan_binding','policy_id'),'policy_version':('plan_binding','policy_version')},
 'GENERATION_RUN':{'artifact_set_digest':('artifact_set','artifact_digest')}}
notes={'ARTIFACT':'Immutable relative portable-path metadata and exact manifest binding exist; actual object bytes, host path resolution/symlink protection and secret-safe publication remain integration work.','FINDING':'Immutable same-generation stable identities and validation-check links exist; worker evidence ingestion/redaction and complete report integration remain incomplete.','PLAN_REVOCATION':'Immutable actor/reason record blocks supported admission/replay/publication/export; HTTP idempotency, cancellation and full lifecycle integration remain incomplete.','SOURCE_SNAPSHOT':'Immutable database identity and scope exist; actual source acquisition/storage byte verification and retention controls remain unimplemented.','GRAPH_NODE':'Scope and nonempty JSON evidence are enforced; analyzer/evidence-content validation and snapshot output sealing remain incomplete.','GRAPH_EDGE':'Same-analysis/tenant endpoints are enforced; analyzer lifecycle output sealing remains incomplete.','RECOMMENDATION':'Immutable scope/version/candidate ownership exists; actual deterministic recommendation computation and full content schema validation remain incomplete.','PLAN':'Stored payload is bytea, not JSON; full recommendation/config/plugin payload and canonical publisher are incomplete. Policy version currently integer, logical version string.',
 'POLICY':'Version is integer, required_checks is text[], while logical contract uses string/JSON; full policy content hash/schema/executable policy missing.',
 'AUDIT_EVENT':'ID is bigint identity rather than logical UUID; actor attribution and complete resource identity/lifecycle missing.',
 'MEMBERSHIP':'Active flag is not the logical authorization role model.',
 'VALIDATION_CHECK':'Composite name identity replaces logical UUID; mandatory derives from immutable policy; finding links absent.',
 'CANDIDATE':'Eligible boolean/source reference are not the full operation/evidence/security eligibility resource.',
 'INFERENCE_CONSENT':'Payload classes are text[], not JSON; transaction admission scope exists, actual egress recheck not integrated.',
 'OUTBOX_EVENT':'Identity only; dispatch payload, durable attempts/claim/recovery and exactly-once-effect handling absent.'}

# Migration-006 reconciled identities and derived contract fields.
aliases['VALIDATION_RUN']['artifact_set_digest']='artifact_digest'
additional.setdefault('VALIDATION_CHECK',{}).update({'mandatory':('validation_check_contract','mandatory'),'finding_ids':('validation_check_contract','finding_ids')})
notes['AUDIT_EVENT']='UUID external identity and generated resource ID exist; runtime actor comes from authenticated principal. Administrative/bootstrap actor remains explicitly nullable; complete audit lifecycle/redaction still pending.'
notes['VALIDATION_CHECK']='Stable UUID plus private contract projection derives mandatory/finding IDs; actual worker evidence ingestion and complete policy execution still require integration.'
notes['OUTBOX_EVENT']='Durable immutable payload/timestamps and monotonic attempt metadata exist; dispatcher leases, crash recovery and deduplicated external effects remain unimplemented.'
notes['APPROVAL']='Exact current plan hash/version and affirmative security confirmation are required; scoped stored Approval validates against OpenAPI. Browser/session and POST idempotency integration remain open.'
notes['IDEMPOTENCY_RECORD']='UUID/timestamp and immutable original admission response are persisted for generate; other POST operations and HTTP response/status mapping remain integration work.'


# Migration-007 exact payload and opaque policy-version projections.
additional.setdefault('PLAN',{}).update({field:('plan_contract',field) for field in ['status','integration_type','configuration','candidate_ids','rationale','risks','canonicalization','generator','override_reason','canonical_payload','policy_id','policy_version']})
additional.setdefault('POLICY',{})['version']=('validation_policy','version_label')
additional.setdefault('VALIDATION_RUN',{})['policy_version']=('validation_policy_reference','policy_version')
notes['PLAN']='Full canonical payload and read-only projection validate against original CanonicalPlan/Plan schemas; trusted publisher must enforce JCS/installed plugin schema and secret-reference policy before product exposure.'
notes['POLICY']='Exact opaque string labels and canonical content hash are stored; integer revision remains a private relational key. Reference projections preserve labels, including leading zeroes. Actual policy command execution remains integration work.'
notes['CANDIDATE']='All declared security/evidence metadata exists and selected executable fields bind exactly; schema-valid fixture and basic admission prerequisites are tested, not source truth or installed plugin compatibility.'
notes['ANALYSIS_RUN']='Analyzer version references are a pinned nonempty array; actual source/analyzer lifecycle and snapshot output sealing remain integration work.'
notes['GENERATION_RUN']='Generator and plan hash derive from immutable canonical binding; actual generation, verified object publication and recovery still require application integration.'


# Migration-008 closes declared principal/project field presence.
notes['TENANT']='Workspace display name is required; local workspace only, no tenant-management product surface.'
notes['USER']='Unique immutable local subject exists; real bootstrap/session credential provisioning remains unimplemented.'
notes['MEMBERSHIP']='Explicit operator role plus active state enforces the approved initial single-operator capability; no enterprise role-management UI or broader permission model is added.'
notes['PROJECT']='Source/name/timestamps exist and Source/ProjectInput fixture documents validate. Source identity is immutable; actual local/Git acquisition, credential resolution and full workflow/latest-run API projections remain pending.'


# Migration-009 closes SCHEMA-D01 without a DB01 exception.
notes['POLICY']='Each immutable version resource now has a tenant-unique UUID; policy_key groups lineage and exact labels/revisions are unique within it. Canonical references retain the version-row UUID and opaque label. Legacy identity conflicts block migration; actual policy execution remains integration work.'

rows=[]
for entity,fields in logical.items():
 table=names.get(entity);mapped={};missing=[]
 for field in fields:
  column=aliases.get(entity,{}).get(field,field)
  target=additional.get(entity,{}).get(field,(table,column))
  if target[0] in tables and target[1] in tables[target[0]]:
   c=tables[target[0]][target[1]];mapped[field]={'table':target[0],'column':target[1],'physical_type':c['type'],'logical_type':fields[field]}
  else:missing.append(field)
 rows.append({'logical_entity':entity,'physical_table':table,'status':'ABSENT' if table is None else 'PARTIAL; name mapping only',
 'mapped_fields':mapped,'missing_fields':missing,'notes':notes.get(entity,'Existence/name alignment does not establish complete behavior, tenant authorization or API compatibility.')})
assert len(rows)==len(logical) and all(e['logical_entity'] in logical for e in rows)
for row in rows:
 assert set(row['mapped_fields'])|set(row['missing_fields'])==set(logical[row['logical_entity']])
assert not any(row['status']=='COMPLETE' for row in rows)
report={'scope':'All logical entity fields accounted for against actual column catalog; no schema completeness claim',
 'catalog_sha256':hashlib.sha256(catalog_path.read_bytes()).hexdigest(),'logical_dictionary_sha256':hashlib.sha256(logical_path.read_bytes()).hexdigest(),
 'logical_entity_count':len(rows),'absent_entities':[r['logical_entity'] for r in rows if r['status']=='ABSENT'],'entities':rows,
 'supporting_tables':sorted(set(tables)-set(names.values())),'mapping_consistency_passed':True,'unmapped_field_count':sum(len(r['missing_fields']) for r in rows),'field_coverage_complete':all(not r['missing_fields'] and r['physical_table'] for r in rows),'full_schema_complete':False}
(root/'docs/quality/physical-model-mapping.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
lines=['# Logical-to-physical model mapping','',f'All {len(rows)} logical entities and all declared fields are accounted for using the live migrated fixture catalog. Every implemented entity remains partial; name correspondence is not behavioral completion.','',
 '| Logical entity | Physical table | Fields mapped / total | Remaining fields |','|---|---|---|---|']
for row in rows:
 lines.append('| '+row['logical_entity']+' | '+(row['physical_table'] or 'ABSENT')+' | '+str(len(row['mapped_fields']))+' / '+str(len(logical[row['logical_entity']]))+' | '+', '.join(row['missing_fields'])+' |')
lines+=['','## Representation and integration differences','']
for entity,note in notes.items():lines.append('- '+entity+': '+note)
lines+=['','## Gate and reproduction','','`docs/quality/physical-model-mapping.json` contains each source field, target column/type or missing designation and source hashes. `physical-schema-catalog.json` was captured from the disposable database after the migration chain recorded in that catalog. Run `python tools/map-physical-schema.py` to reproduce the mapping; rerun `tools/fixtures/m03/policy-identity-runner.py` to refresh its database catalog first.','',
 'No source data dictionary or API contract was changed to fit the partial implementation. H01 remains open. Next physical-model work should complete remaining schema/API semantics, then complete lifecycle, credential-reference and worker/publication integration. Runtime identity/assignment and bound artifact/export tables are supporting physical structures, not extra product screens.']
(root/'docs/foundation/PHYSICAL-MODEL-MAPPING.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
print(json.dumps({'logical_entities':len(rows),'absent_entities':report['absent_entities'],'mapping_consistency_passed':True,'unmapped_field_count':sum(len(r['missing_fields']) for r in rows),'field_coverage_complete':all(not r['missing_fields'] and r['physical_table'] for r in rows),'full_schema_complete':False}))
