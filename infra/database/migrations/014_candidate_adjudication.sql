BEGIN;
SET LOCAL ROLE studio_kernel_owner;
SET LOCAL search_path=studio_admission,pg_catalog,pg_temp;

DO $$ DECLARE item record; BEGIN
 FOR item IN SELECT conname FROM pg_constraint
 WHERE conrelid='studio_admission.candidate'::regclass AND contype='c'
 AND pg_get_constraintdef(oid) LIKE '%NOT eligible%provenance%deterministic%' LOOP
  EXECUTE format('ALTER TABLE candidate DROP CONSTRAINT %I',item.conname);
 END LOOP;
END $$;
ALTER TABLE candidate ADD CONSTRAINT candidate_executable_evidence CHECK(
 NOT eligible OR (operation_type='read' AND cardinality(side_effects)=0 AND sensitivity<>'unknown'
 AND provenance IN ('deterministic','manual') AND jsonb_array_length(evidence)>0));

CREATE TABLE candidate_adjudication(
 tenant_id uuid NOT NULL, id uuid NOT NULL, analysis_id uuid NOT NULL,
 source_candidate_id uuid NOT NULL, derived_candidate_id uuid NOT NULL, actor_id uuid NOT NULL REFERENCES actor,
 source_digest digest NOT NULL, authorization_basis text NOT NULL CHECK(length(trim(authorization_basis)) BETWEEN 20 AND 2000),
 sensitivity text NOT NULL CHECK(sensitivity IN ('public','internal','sensitive')),
 domain_service_reference text NOT NULL CHECK(domain_service_reference ~ '^verified:[A-Za-z0-9_.:/-]+$'),
 required_scopes text[] NOT NULL CHECK(array_position(required_scopes,NULL) IS NULL),
 input_schema jsonb NOT NULL CHECK(jsonb_typeof(input_schema)='object'),
 output_schema jsonb NOT NULL CHECK(jsonb_typeof(output_schema)='object'),
 security_confirmed boolean NOT NULL CHECK(security_confirmed), created_at timestamptz NOT NULL DEFAULT clock_timestamp(),
 PRIMARY KEY(tenant_id,id), UNIQUE(tenant_id,source_candidate_id), UNIQUE(tenant_id,derived_candidate_id),
 FOREIGN KEY(tenant_id,analysis_id,source_candidate_id) REFERENCES candidate(tenant_id,analysis_id,id),
 FOREIGN KEY(tenant_id,analysis_id,derived_candidate_id) REFERENCES candidate(tenant_id,analysis_id,id),
 FOREIGN KEY(tenant_id,analysis_id,source_digest) REFERENCES analysis(tenant_id,id,source_digest));
CREATE TRIGGER frozen_candidate_adjudication BEFORE UPDATE OR DELETE ON candidate_adjudication
 FOR EACH ROW EXECUTE FUNCTION frozen_record();

CREATE FUNCTION verified_manual_candidate() RETURNS trigger LANGUAGE plpgsql
SET search_path=pg_catalog,studio_admission,pg_temp AS $$
BEGIN
 IF NEW.eligible AND NEW.provenance='manual' AND NOT EXISTS(
  SELECT 1 FROM candidate_adjudication a WHERE a.tenant_id=NEW.tenant_id AND a.analysis_id=NEW.analysis_id
  AND a.derived_candidate_id=NEW.id AND a.sensitivity=NEW.sensitivity
  AND a.domain_service_reference=NEW.domain_service_reference AND a.required_scopes=NEW.required_scopes
  AND a.input_schema=NEW.input_schema AND a.output_schema=NEW.output_schema AND a.security_confirmed) THEN
  RAISE check_violation USING MESSAGE='manual executable candidate requires exact immutable adjudication';
 END IF;
 RETURN NEW;
END $$;
CREATE CONSTRAINT TRIGGER verified_manual_candidate AFTER INSERT ON candidate DEFERRABLE INITIALLY DEFERRED
 FOR EACH ROW EXECUTE FUNCTION verified_manual_candidate();

CREATE FUNCTION backend_adjudicate_candidate(p_candidate uuid,p_review jsonb) RETURNS jsonb
LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog,studio_admission,pg_temp AS $$
DECLARE ident runtime_principal; source candidate; derived candidate; a analysis; prior candidate_adjudication;
 adjudication_id uuid; derived_id uuid; scopes text[]; sensitivity_value text; domain_value text;
BEGIN
 ident=runtime_identity('backend');
 IF exact_keys(p_review,ARRAY['authorization_basis','sensitivity','domain_service_reference','required_scopes','input_schema','output_schema','security_confirmed']) IS DISTINCT FROM true
 OR jsonb_typeof(p_review->'required_scopes')<>'array' OR jsonb_typeof(p_review->'input_schema')<>'object'
 OR jsonb_typeof(p_review->'output_schema')<>'object' OR (p_review->>'security_confirmed')::boolean IS DISTINCT FROM true THEN
  RAISE check_violation USING MESSAGE='complete exact candidate adjudication required';
 END IF;
 SELECT * INTO source FROM candidate WHERE tenant_id=ident.tenant_id AND id=p_candidate FOR SHARE;
 SELECT * INTO a FROM analysis WHERE tenant_id=ident.tenant_id AND id=source.analysis_id AND status='succeeded' FOR SHARE;
 IF source.id IS NULL OR source.operation_type<>'read' OR source.eligibility<>'unknown' OR source.provenance<>'deterministic'
 OR source.detector IS DISTINCT FROM jsonb_build_object('id','route-candidate-detector','version','route-candidate-deterministic-v2')
 OR NOT a.analyzer_versions @> '[{"id":"typescript-next","version":"typescript-next-deterministic-v2"}]'::jsonb THEN
  RAISE check_violation USING MESSAGE='current deterministic read candidate required';
 END IF;
 scopes=ARRAY(SELECT value FROM jsonb_array_elements_text(p_review->'required_scopes') ORDER BY value);
 IF cardinality(scopes)<>(SELECT count(DISTINCT value) FROM unnest(scopes) value)
 OR EXISTS(SELECT 1 FROM unnest(scopes) value WHERE length(trim(value))=0) THEN
  RAISE check_violation USING MESSAGE='required scopes must be unique and nonempty';
 END IF;
 sensitivity_value=p_review->>'sensitivity';domain_value=p_review->>'domain_service_reference';
 IF sensitivity_value NOT IN ('public','internal','sensitive') OR domain_value !~ '^verified:[A-Za-z0-9_.:/-]+$'
 OR length(trim(p_review->>'authorization_basis')) NOT BETWEEN 20 AND 2000
 OR p_review->'input_schema'->>'type' IS DISTINCT FROM 'object'
 OR p_review->'input_schema'->'additionalProperties' IS DISTINCT FROM 'false'::jsonb
 OR p_review->'output_schema'->>'type' IS DISTINCT FROM 'object' THEN
  RAISE check_violation USING MESSAGE='review basis, mapping, sensitivity and strict object schemas are required';
 END IF;
 SELECT * INTO prior FROM candidate_adjudication WHERE tenant_id=ident.tenant_id AND source_candidate_id=source.id;
 IF prior.id IS NOT NULL THEN
  IF prior.authorization_basis IS DISTINCT FROM p_review->>'authorization_basis' OR prior.sensitivity IS DISTINCT FROM sensitivity_value
  OR prior.domain_service_reference IS DISTINCT FROM domain_value OR prior.required_scopes IS DISTINCT FROM scopes
  OR prior.input_schema IS DISTINCT FROM p_review->'input_schema' OR prior.output_schema IS DISTINCT FROM p_review->'output_schema' THEN
   RAISE check_violation USING MESSAGE='candidate already has a different immutable adjudication';
  END IF;
  SELECT * INTO derived FROM candidate WHERE tenant_id=ident.tenant_id AND id=prior.derived_candidate_id;
 ELSE
  adjudication_id=gen_random_uuid();derived_id=gen_random_uuid();
  INSERT INTO candidate(tenant_id,analysis_id,id,eligible,source_reference,graph_node_id,finding_id,operation_type,
   side_effects,sensitivity,required_scopes,input_schema,output_schema,eligibility,reason_codes,evidence,detector,
   provenance,confidence,domain_service_reference)
  VALUES(ident.tenant_id,source.analysis_id,derived_id,true,source.source_reference,source.graph_node_id,
   source.finding_id||':verified','read',ARRAY[]::text[],sensitivity_value,scopes,p_review->'input_schema',p_review->'output_schema',
   'allowed',ARRAY['operator_verified','exact_manual_review'],source.evidence,
   jsonb_build_object('id','candidate-adjudication','version','manual-v1'),'manual',
   jsonb_build_object('value',NULL,'method','operator-adjudication'),domain_value);
  INSERT INTO candidate_adjudication(tenant_id,id,analysis_id,source_candidate_id,derived_candidate_id,actor_id,source_digest,
   authorization_basis,sensitivity,domain_service_reference,required_scopes,input_schema,output_schema,security_confirmed)
  VALUES(ident.tenant_id,adjudication_id,source.analysis_id,source.id,derived_id,ident.actor_id,a.source_digest,
   p_review->>'authorization_basis',sensitivity_value,domain_value,scopes,p_review->'input_schema',p_review->'output_schema',true);
  SELECT * INTO derived FROM candidate WHERE tenant_id=ident.tenant_id AND id=derived_id;
 END IF;
 RETURN jsonb_build_object('id',derived.id,'finding_id',derived.finding_id,'graph_node_id',derived.graph_node_id,
  'operation_type',derived.operation_type,'side_effects',to_jsonb(derived.side_effects),'sensitivity',derived.sensitivity,
  'required_scopes',to_jsonb(derived.required_scopes),'input_schema',derived.input_schema,'output_schema',derived.output_schema,
  'eligibility',derived.eligibility,'reason_codes',to_jsonb(derived.reason_codes),'evidence',derived.evidence,'detector',derived.detector,
  'provenance',derived.provenance,'confidence',derived.confidence,'domain_service_reference',derived.domain_service_reference,
  'adjudication',jsonb_build_object('source_candidate_id',source.id,'authorization_basis',p_review->>'authorization_basis',
   'security_confirmed',true));
END $$;

CREATE OR REPLACE FUNCTION backend_get_candidates(p_analysis uuid) RETURNS jsonb
LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog,studio_admission,pg_temp AS $$
DECLARE ident runtime_principal; exists_id uuid; items jsonb;
BEGIN
 ident=runtime_identity('backend');SELECT id INTO exists_id FROM analysis WHERE tenant_id=ident.tenant_id AND id=p_analysis;
 IF exists_id IS NULL THEN RAISE insufficient_privilege USING MESSAGE='analysis unavailable'; END IF;
 SELECT coalesce(jsonb_agg(jsonb_build_object('id',c.id,'finding_id',c.finding_id,'graph_node_id',c.graph_node_id,
  'operation_type',c.operation_type,'side_effects',to_jsonb(c.side_effects),'sensitivity',c.sensitivity,
  'required_scopes',to_jsonb(c.required_scopes),'input_schema',c.input_schema,'output_schema',c.output_schema,
  'eligibility',c.eligibility,'reason_codes',to_jsonb(c.reason_codes),'evidence',c.evidence,'detector',c.detector,
  'provenance',c.provenance,'confidence',c.confidence,'domain_service_reference',c.domain_service_reference,
  'adjudication',CASE WHEN j.id IS NULL THEN NULL ELSE jsonb_build_object('source_candidate_id',j.source_candidate_id,
   'authorization_basis',j.authorization_basis,'security_confirmed',j.security_confirmed,'created_at',j.created_at) END)
  ORDER BY c.finding_id,c.id),'[]'::jsonb) INTO items FROM candidate c LEFT JOIN candidate_adjudication j
  ON j.tenant_id=c.tenant_id AND j.derived_candidate_id=c.id WHERE c.tenant_id=ident.tenant_id AND c.analysis_id=p_analysis;
 RETURN jsonb_build_object('analysis_id',p_analysis,'items',items);
END $$;

ALTER FUNCTION backend_adjudicate_candidate(uuid,jsonb) OWNER TO studio_kernel_owner;
ALTER FUNCTION backend_get_candidates(uuid) OWNER TO studio_kernel_owner;
REVOKE ALL ON FUNCTION backend_adjudicate_candidate(uuid,jsonb) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION backend_adjudicate_candidate(uuid,jsonb) TO studio_backend;
REVOKE ALL ON ALL TABLES IN SCHEMA studio_admission FROM PUBLIC,studio_backend,studio_worker;
COMMIT;
