BEGIN;
SET LOCAL ROLE studio_kernel_owner;
SET LOCAL search_path=studio_admission,pg_catalog,pg_temp;

CREATE FUNCTION backend_create_exact_plan(p_document jsonb,p_canonical bytea,p_hash text) RETURNS jsonb
LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog,studio_admission,pg_temp AS $$
DECLARE ident runtime_principal; a analysis; rec jsonb; plan_id uuid; policy_id uuid='00000000-0000-4000-8000-000000000101';
 policy_version integer=1; actual_hash text; candidate_id uuid; version_created integer;
BEGIN
 ident=runtime_identity('backend');actual_hash=encode(sha256(p_canonical),'hex');
 IF actual_hash IS DISTINCT FROM p_hash OR p_document->>'content_hash' IS DISTINCT FROM p_hash
  OR p_document->>'canonicalization' IS DISTINCT FROM 'RFC8785+MCPStudio-sets-v1'
  OR convert_from(p_canonical,'UTF8')::jsonb IS DISTINCT FROM p_document->'canonical_payload' THEN
  RAISE check_violation USING MESSAGE='canonical plan bytes/hash mismatch';
 END IF;
 plan_id=(p_document->>'plan_id')::uuid;rec=p_document->'recommendation';
 SELECT * INTO a FROM analysis WHERE tenant_id=ident.tenant_id AND id=(p_document->>'analysis_id')::uuid AND status='succeeded' FOR UPDATE;
 IF a.id IS NULL OR p_document->>'source_digest' IS DISTINCT FROM a.source_digest::text
  OR rec->>'source_digest' IS DISTINCT FROM a.source_digest::text OR rec->>'recommended_type' IS DISTINCT FROM 'server'
  OR (rec->>'supported_generation')::boolean IS DISTINCT FROM true OR jsonb_array_length(rec->'candidate_ids')=0 THEN
  RAISE check_violation USING MESSAGE='source-bound executable recommendation required';
 END IF;
 FOR candidate_id IN SELECT value::uuid FROM jsonb_array_elements_text(rec->'candidate_ids') LOOP
  PERFORM 1 FROM candidate WHERE tenant_id=ident.tenant_id AND analysis_id=a.id AND id=candidate_id AND eligible
   AND operation_type='read' AND domain_service_reference NOT LIKE 'unresolved:%';
  IF NOT FOUND THEN RAISE check_violation USING MESSAGE='selected candidate is not executable'; END IF;
 END LOOP;
 INSERT INTO validation_policy(tenant_id,id,version,required_checks,version_label,policy_key,schema_version,canonical_content)
 VALUES(ident.tenant_id,policy_id,policy_version,ARRAY['artifact_manifest','compile','test'],'local-safe-v1','local-safe','1',
  convert_to(jsonb_build_object('id',policy_id,'version','local-safe-v1','policy_key','local-safe','schema_version','1',
   'required_checks',to_jsonb(ARRAY['artifact_manifest','compile','test']::text[]))::text,'UTF8')) ON CONFLICT(tenant_id,id) DO NOTHING;
 INSERT INTO recommendation(tenant_id,analysis_run_id,id,version,source_digest,recommended_type,rationale,candidate_ids,
  risks,required_reviews,supported_generation,availability_reason)
 VALUES(ident.tenant_id,a.id,(rec->>'id')::uuid,(rec->>'version')::integer,a.source_digest,'server',rec->>'rationale',
  (SELECT array_agg(value::uuid ORDER BY value) FROM jsonb_array_elements_text(rec->'candidate_ids')),
  rec->'risks',rec->'required_reviews',true,rec->>'availability_reason');
 version_created=new_plan(ident.tenant_id,a.id,plan_id,p_hash::digest,(rec->>'id')::uuid,(rec->>'version')::integer);
 INSERT INTO plan_binding(tenant_id,plan_id,policy_id,policy_version,canonical_payload,source_digest)
 VALUES(ident.tenant_id,plan_id,policy_id,policy_version,p_canonical,a.source_digest);
 IF version_created IS DISTINCT FROM (SELECT version FROM plan WHERE tenant_id=ident.tenant_id AND id=plan_id) THEN
  RAISE check_violation USING MESSAGE='plan version allocation mismatch'; END IF;
 RETURN backend_plan_document(plan_id);
END $$;

CREATE FUNCTION backend_latest_plan(p_analysis uuid) RETURNS jsonb
LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog,studio_admission,pg_temp AS $$
DECLARE ident runtime_principal; plan_id uuid;
BEGIN
 ident=runtime_identity('backend');
 SELECT id INTO plan_id FROM plan WHERE tenant_id=ident.tenant_id AND analysis_id=p_analysis AND current ORDER BY version DESC LIMIT 1;
 IF plan_id IS NULL THEN RAISE insufficient_privilege USING MESSAGE='plan unavailable'; END IF;
 RETURN backend_plan_document(plan_id);
END $$;

CREATE FUNCTION backend_approve_exact_plan(p_plan uuid,p_version integer,p_hash text,p_security boolean) RETURNS jsonb
LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog,studio_admission,pg_temp AS $$
DECLARE ident runtime_principal; approval_id uuid; p plan; approved approval;
BEGIN
 ident=runtime_identity('backend');
 SELECT * INTO p FROM plan WHERE tenant_id=ident.tenant_id AND id=p_plan FOR UPDATE;
 IF p.id IS NULL OR NOT p.current OR p.version IS DISTINCT FROM p_version OR p.plan_hash::text IS DISTINCT FROM p_hash OR NOT p_security THEN
  RAISE check_violation USING MESSAGE='exact current plan security confirmation required'; END IF;
 SELECT * INTO approved FROM approval WHERE tenant_id=ident.tenant_id AND plan_id=p.id AND actor_id=ident.actor_id
  AND plan_hash=p.plan_hash AND plan_version=p.version AND revoked_at IS NULL ORDER BY approved_at DESC LIMIT 1;
 IF approved.id IS NULL THEN
  approval_id=backend_approve_plan(p.id,p.version,p.plan_hash::text,true);
  SELECT * INTO approved FROM approval WHERE tenant_id=ident.tenant_id AND id=approval_id;
 END IF;
 RETURN jsonb_build_object('id',approved.id,'plan_id',approved.plan_id,'actor_id',approved.actor_id,'plan_version',approved.plan_version,
  'plan_hash',approved.plan_hash,'security_confirmed',approved.security_confirmed,'approved_at',approved.approved_at,'status','approved');
END $$;

ALTER FUNCTION backend_create_exact_plan(jsonb,bytea,text) OWNER TO studio_kernel_owner;
ALTER FUNCTION backend_latest_plan(uuid) OWNER TO studio_kernel_owner;
ALTER FUNCTION backend_approve_exact_plan(uuid,integer,text,boolean) OWNER TO studio_kernel_owner;
REVOKE ALL ON FUNCTION backend_create_exact_plan(jsonb,bytea,text),backend_latest_plan(uuid),backend_approve_exact_plan(uuid,integer,text,boolean) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION backend_create_exact_plan(jsonb,bytea,text),backend_latest_plan(uuid),backend_approve_exact_plan(uuid,integer,text,boolean) TO studio_backend;
COMMIT;
