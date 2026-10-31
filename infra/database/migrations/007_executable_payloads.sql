BEGIN;
SET LOCAL ROLE studio_kernel_owner;
SET LOCAL search_path=studio_admission,pg_catalog,pg_temp;
CREATE FUNCTION exact_keys(v jsonb,names text[]) RETURNS boolean LANGUAGE sql IMMUTABLE SET search_path=pg_catalog AS $$
 SELECT CASE WHEN jsonb_typeof(v)='object' THEN (SELECT array_agg(x ORDER BY x) FROM jsonb_object_keys(v) x)=
 (SELECT array_agg(x ORDER BY x) FROM unnest(names) x) ELSE false END
$$;
CREATE FUNCTION version_reference(v jsonb) RETURNS boolean LANGUAGE sql IMMUTABLE SET search_path=pg_catalog,studio_admission,pg_temp AS $$
 SELECT exact_keys(v,ARRAY['id','version']) AND jsonb_typeof(v->'id')='string' AND length(trim(v->>'id'))>0
 AND jsonb_typeof(v->'version')='string' AND length(trim(v->>'version'))>0
$$;
ALTER TABLE validation_policy ADD COLUMN version_label text NOT NULL CHECK(length(trim(version_label))>0),
 ADD COLUMN policy_key text NOT NULL CHECK(length(trim(policy_key))>0),ADD COLUMN schema_version text NOT NULL CHECK(length(trim(schema_version))>0),
 ADD COLUMN canonical_content bytea NOT NULL,
 ADD COLUMN content_hash text GENERATED ALWAYS AS(encode(sha256(canonical_content),'hex')) STORED,
 ADD UNIQUE(tenant_id,id,version_label);
CREATE FUNCTION policy_content_matches() RETURNS trigger LANGUAGE plpgsql SET search_path=pg_catalog,studio_admission,pg_temp AS $$
DECLARE v jsonb;
BEGIN
 v=convert_from(NEW.canonical_content,'UTF8')::jsonb;
 IF v IS DISTINCT FROM jsonb_build_object('id',NEW.id,'version',NEW.version_label,'policy_key',NEW.policy_key,
 'schema_version',NEW.schema_version,'required_checks',to_jsonb(NEW.required_checks)) THEN
 RAISE check_violation USING MESSAGE='policy content/label mismatch'; END IF;
 RETURN NEW;
END $$;
CREATE TRIGGER checked_policy_content BEFORE INSERT ON validation_policy FOR EACH ROW EXECUTE FUNCTION policy_content_matches();
ALTER TABLE analysis DROP CONSTRAINT analysis_analyzer_versions_check,
 ALTER COLUMN analyzer_versions DROP DEFAULT,
 ADD CHECK(CASE WHEN jsonb_typeof(analyzer_versions)='array' THEN jsonb_array_length(analyzer_versions)>0 ELSE false END);
ALTER TABLE candidate ADD COLUMN finding_id text NOT NULL CHECK(length(trim(finding_id))>0),
 ADD COLUMN operation_type text NOT NULL CHECK(operation_type IN ('read','write','unknown')),
 ADD COLUMN side_effects text[] NOT NULL,ADD COLUMN sensitivity text NOT NULL CHECK(sensitivity IN ('public','internal','sensitive','unknown')),
 ADD COLUMN required_scopes text[] NOT NULL,ADD COLUMN input_schema jsonb NOT NULL CHECK(jsonb_typeof(input_schema)='object'),
 ADD COLUMN output_schema jsonb NOT NULL CHECK(jsonb_typeof(output_schema)='object'),
 ADD COLUMN eligibility text NOT NULL CHECK(eligibility IN ('allowed','blocked','unsupported','unknown')),
 ADD COLUMN reason_codes text[] NOT NULL,ADD COLUMN evidence jsonb NOT NULL CHECK(jsonb_typeof(evidence)='array'),
 ADD COLUMN detector jsonb NOT NULL CHECK(version_reference(detector) IS TRUE),
 ADD COLUMN provenance text NOT NULL CHECK(provenance IN ('deterministic','model','manual','unknown')),
 ADD COLUMN confidence jsonb NOT NULL CHECK(jsonb_typeof(confidence)='object'),
 ADD COLUMN domain_service_reference text NOT NULL CHECK(length(trim(domain_service_reference))>0),
 ADD CHECK(eligible=(eligibility='allowed')),
 ADD CHECK(array_position(required_scopes,NULL) IS NULL AND array_position(side_effects,NULL) IS NULL AND array_position(reason_codes,NULL) IS NULL),
 ADD CHECK(NOT eligible OR (operation_type='read' AND cardinality(side_effects)=0 AND sensitivity<>'unknown'
 AND provenance='deterministic' AND jsonb_array_length(evidence)>0));
CREATE FUNCTION candidate_security_scope() RETURNS trigger LANGUAGE plpgsql SET search_path=pg_catalog,studio_admission,pg_temp AS $$
DECLARE d digest;
BEGIN
 SELECT source_digest INTO d FROM analysis WHERE tenant_id=NEW.tenant_id AND id=NEW.analysis_id;
 IF cardinality(NEW.required_scopes)<>(SELECT count(DISTINCT x) FROM unnest(NEW.required_scopes) x)
 OR EXISTS(SELECT 1 FROM unnest(NEW.required_scopes) x WHERE length(trim(x))=0)
 OR EXISTS(SELECT 1 FROM jsonb_array_elements(NEW.evidence) e WHERE e->>'source_digest' IS DISTINCT FROM d::text
 OR length(coalesce(e->>'path',''))=0 OR length(coalesce(e->>'detector_version',''))=0) THEN
 RAISE check_violation USING MESSAGE='candidate scope/evidence mismatch'; END IF;
 RETURN NEW;
END $$;
CREATE TRIGGER candidate_security BEFORE INSERT ON candidate FOR EACH ROW EXECUTE FUNCTION candidate_security_scope();
CREATE OR REPLACE FUNCTION bind_payload_v2() RETURNS trigger LANGUAGE plpgsql SET search_path=pg_catalog,studio_admission,pg_temp AS $$
DECLARE p plan; a analysis; pol validation_policy; body jsonb; c candidate; item jsonb; ids uuid[];
BEGIN
 SELECT * INTO p FROM plan WHERE tenant_id=NEW.tenant_id AND id=NEW.plan_id FOR UPDATE;
 SELECT * INTO a FROM analysis WHERE tenant_id=p.tenant_id AND id=p.analysis_id;
 SELECT * INTO pol FROM validation_policy WHERE tenant_id=NEW.tenant_id AND id=NEW.policy_id AND version=NEW.policy_version;
 body=convert_from(NEW.canonical_payload,'UTF8')::jsonb;
 IF exact_keys(body,ARRAY['snapshot_id','source_digest','analysis_id','analyzer_versions','recommendation_id',
 'recommendation_version','selected_type','candidates','generator','configuration','transport','policy','override_reason']) IS DISTINCT FROM true
 OR encode(sha256(NEW.canonical_payload),'hex') IS DISTINCT FROM p.plan_hash::text
 OR NEW.source_digest IS DISTINCT FROM a.source_digest OR body->>'analysis_id' IS DISTINCT FROM p.analysis_id::text
 OR body->>'source_digest' IS DISTINCT FROM a.source_digest::text OR body->'analyzer_versions' IS DISTINCT FROM a.analyzer_versions
 OR body->>'selected_type' IS DISTINCT FROM 'server' OR body->>'transport' IS DISTINCT FROM 'stdio'
 OR version_reference(body->'generator') IS DISTINCT FROM true
 OR jsonb_typeof(body->'candidates') IS DISTINCT FROM 'array' OR pol.id IS NULL
 OR body->'policy' IS DISTINCT FROM jsonb_build_object('id',pol.id,'version',pol.version_label,'required_checks',to_jsonb(pol.required_checks))
 OR exact_keys(body->'configuration',ARRAY['plugin','schema','values']) IS DISTINCT FROM true
 OR version_reference(body->'configuration'->'plugin') IS DISTINCT FROM true
 OR version_reference(body->'configuration'->'schema') IS DISTINCT FROM true
 OR jsonb_typeof(body->'configuration'->'values') IS DISTINCT FROM 'object' THEN
 RAISE check_violation USING MESSAGE='executable payload hash/configuration/policy mismatch'; END IF;
 SELECT array_agg((value->>'id')::uuid) INTO ids FROM jsonb_array_elements(body->'candidates');
 IF ids IS NULL OR array_position(ids,NULL) IS NOT NULL OR cardinality(ids)<>(SELECT count(DISTINCT x) FROM unnest(ids) x) THEN
 RAISE check_violation USING MESSAGE='executable candidate IDs invalid'; END IF;
 FOR item IN SELECT value FROM jsonb_array_elements(body->'candidates') LOOP
  SELECT * INTO c FROM candidate WHERE tenant_id=p.tenant_id AND analysis_id=p.analysis_id AND id=(item->>'id')::uuid;
  IF c.id IS NULL OR NOT c.eligible OR item IS DISTINCT FROM jsonb_build_object('id',c.id,'input_schema',c.input_schema,
  'output_schema',c.output_schema,'domain_service_reference',c.domain_service_reference,'required_scopes',to_jsonb(c.required_scopes)) THEN
  RAISE check_violation USING MESSAGE='executable candidate differs from immutable security metadata'; END IF;
 END LOOP;
 RETURN NEW;
END $$;
CREATE OR REPLACE FUNCTION bind_payload() RETURNS trigger LANGUAGE plpgsql SET search_path=pg_catalog,studio_admission,pg_temp AS $$
DECLARE p plan; rec recommendation; body jsonb;
BEGIN
 SELECT * INTO p FROM plan WHERE tenant_id=NEW.tenant_id AND id=NEW.plan_id FOR UPDATE;
 SELECT * INTO rec FROM recommendation WHERE tenant_id=p.tenant_id AND id=p.recommendation_id AND version=p.recommendation_version;
 body=convert_from(NEW.canonical_payload,'UTF8')::jsonb;
 IF body->>'snapshot_id' IS DISTINCT FROM p.snapshot_id::text OR body->>'recommendation_id' IS DISTINCT FROM p.recommendation_id::text
 OR body->>'recommendation_version' IS DISTINCT FROM p.recommendation_version::text OR body->'override_reason' IS DISTINCT FROM 'null'::jsonb
 OR EXISTS(SELECT 1 FROM jsonb_array_elements(body->'candidates') x WHERE NOT (x.value->>'id')::uuid=ANY(rec.candidate_ids)) THEN
 RAISE check_violation USING MESSAGE='plan recommendation/snapshot/override binding mismatch'; END IF;
 RETURN NEW;
END $$;
CREATE OR REPLACE FUNCTION link_candidates() RETURNS trigger LANGUAGE plpgsql SET search_path=pg_catalog,studio_admission,pg_temp AS $$
BEGIN
 INSERT INTO plan_candidate SELECT NEW.tenant_id,NEW.plan_id,p.analysis_id,(v.value->>'id')::uuid FROM plan p,
 jsonb_array_elements(convert_from(NEW.canonical_payload,'UTF8')::jsonb->'candidates') v WHERE p.tenant_id=NEW.tenant_id AND p.id=NEW.plan_id;
 RETURN NEW;
END $$;
CREATE OR REPLACE FUNCTION selection_scope() RETURNS trigger LANGUAGE plpgsql SET search_path=pg_catalog,studio_admission,pg_temp AS $$
BEGIN
 PERFORM 1 FROM plan_binding b JOIN plan p ON p.tenant_id=b.tenant_id AND p.id=b.plan_id,
 jsonb_array_elements(convert_from(b.canonical_payload,'UTF8')::jsonb->'candidates') c
 WHERE b.tenant_id=NEW.tenant_id AND b.plan_id=NEW.plan_id AND p.analysis_id=NEW.analysis_id AND c.value->>'id'=NEW.candidate_id::text;
 IF NOT FOUND THEN RAISE check_violation USING MESSAGE='selection not in executable payload'; END IF;
 RETURN NEW;
END $$;
ALTER TABLE run ADD COLUMN generator jsonb NOT NULL;
CREATE OR REPLACE FUNCTION bind_run_hash() RETURNS trigger LANGUAGE plpgsql SET search_path=pg_catalog,studio_admission,pg_temp AS $$
DECLARE h digest; g jsonb;
BEGIN
 SELECT p.plan_hash,convert_from(b.canonical_payload,'UTF8')::jsonb->'generator' INTO h,g
 FROM plan p JOIN plan_binding b ON b.tenant_id=p.tenant_id AND b.plan_id=p.id WHERE p.tenant_id=NEW.tenant_id AND p.id=NEW.plan_id;
 IF (NEW.plan_hash IS NOT NULL AND NEW.plan_hash IS DISTINCT FROM h) OR (NEW.generator IS NOT NULL AND NEW.generator IS DISTINCT FROM g) THEN
 RAISE check_violation USING MESSAGE='generation hash/generator mismatch'; END IF;
 NEW.plan_hash=h;NEW.generator=g;RETURN NEW;
END $$;
CREATE VIEW plan_contract AS
 SELECT p.tenant_id,p.id,p.analysis_id AS analysis_run_id,p.version,p.plan_hash AS content_hash,p.current AS is_current,
 p.snapshot_id,p.recommendation_id,p.recommendation_version,
 CASE WHEN EXISTS(SELECT 1 FROM plan_revocation r WHERE r.tenant_id=p.tenant_id AND r.plan_id=p.id) THEN 'revoked'
 WHEN NOT p.current THEN 'superseded' WHEN EXISTS(SELECT 1 FROM approval a WHERE a.tenant_id=p.tenant_id AND a.plan_id=p.id AND a.revoked_at IS NULL) THEN 'approved' ELSE 'draft' END AS status,
 body->>'selected_type' AS integration_type,body->'configuration' AS configuration,
 (SELECT jsonb_agg(c.value->'id' ORDER BY c.value->>'id') FROM jsonb_array_elements(body->'candidates') c) AS candidate_ids,
 rec.rationale,rec.risks,'RFC8785+MCPStudio-sets-v1'::text AS canonicalization,body->'generator' AS generator,
 body->>'override_reason' AS override_reason,body AS canonical_payload,pol.id AS policy_id,pol.version_label AS policy_version
 FROM plan p JOIN plan_binding b ON b.tenant_id=p.tenant_id AND b.plan_id=p.id
 JOIN validation_policy pol ON pol.tenant_id=b.tenant_id AND pol.id=b.policy_id AND pol.version=b.policy_version
 JOIN recommendation rec ON rec.tenant_id=p.tenant_id AND rec.id=p.recommendation_id,
 LATERAL (SELECT convert_from(b.canonical_payload,'UTF8')::jsonb AS body) payload;
CREATE VIEW validation_policy_reference AS
 SELECT v.tenant_id,v.id AS validation_id,pol.id AS policy_id,pol.version_label AS policy_version,to_jsonb(pol.required_checks) AS required_checks
 FROM validation v JOIN validation_policy pol ON pol.tenant_id=v.tenant_id AND pol.id=v.policy_id AND pol.version=v.policy_version;
CREATE FUNCTION backend_plan_document(p_plan uuid) RETURNS jsonb LANGUAGE plpgsql SECURITY DEFINER
SET search_path=pg_catalog,studio_admission,pg_temp AS $$
DECLARE ident runtime_principal; p plan_contract;
BEGIN
 ident=runtime_identity('backend');SELECT * INTO p FROM plan_contract WHERE tenant_id=ident.tenant_id AND id=p_plan;
 IF p.id IS NULL THEN RAISE insufficient_privilege USING MESSAGE='plan unavailable'; END IF;
 RETURN jsonb_build_object('id',p.id,'analysis_id',p.analysis_run_id,'version',p.version,'integration_type',p.integration_type,
 'capability_ids',p.candidate_ids,'configuration',p.configuration,'recommendation_id',p.recommendation_id,'recommendation_version',p.recommendation_version,
 'status',p.status,'content_hash',p.content_hash,'canonicalization',p.canonicalization,'canonical_payload',p.canonical_payload,
 'policy_version',p.policy_version,'rationale',p.rationale,'risks',p.risks)
 || CASE WHEN p.override_reason IS NULL THEN '{}'::jsonb ELSE jsonb_build_object('override_reason',p.override_reason) END;
END $$;
GRANT EXECUTE ON FUNCTION backend_plan_document(uuid) TO studio_backend;
REVOKE ALL ON ALL TABLES IN SCHEMA studio_admission FROM PUBLIC,studio_backend,studio_worker;
COMMIT;
