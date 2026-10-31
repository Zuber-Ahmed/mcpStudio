BEGIN;
SET LOCAL ROLE studio_kernel_owner;
SET LOCAL search_path=studio_admission,pg_catalog,pg_temp;

CREATE FUNCTION backend_get_candidates(p_analysis uuid) RETURNS jsonb
LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog,studio_admission,pg_temp AS $$
DECLARE ident runtime_principal; exists_id uuid; items jsonb;
BEGIN
 ident=runtime_identity('backend');
 SELECT id INTO exists_id FROM analysis WHERE tenant_id=ident.tenant_id AND id=p_analysis;
 IF exists_id IS NULL THEN RAISE insufficient_privilege USING MESSAGE='analysis unavailable'; END IF;
 SELECT coalesce(jsonb_agg(jsonb_build_object('id',id,'finding_id',finding_id,'graph_node_id',graph_node_id,
  'operation_type',operation_type,'side_effects',to_jsonb(side_effects),'sensitivity',sensitivity,
  'required_scopes',to_jsonb(required_scopes),'input_schema',input_schema,'output_schema',output_schema,
  'eligibility',eligibility,'reason_codes',to_jsonb(reason_codes),'evidence',evidence,'detector',detector,
  'provenance',provenance,'confidence',confidence,'domain_service_reference',domain_service_reference)
  ORDER BY finding_id,id),'[]'::jsonb) INTO items
 FROM candidate WHERE tenant_id=ident.tenant_id AND analysis_id=p_analysis;
 RETURN jsonb_build_object('analysis_id',p_analysis,'items',items);
END $$;

CREATE FUNCTION backend_get_recommendation(p_analysis uuid) RETURNS jsonb
LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog,studio_admission,pg_temp AS $$
DECLARE ident runtime_principal; item recommendation;
BEGIN
 ident=runtime_identity('backend');
 SELECT * INTO item FROM recommendation WHERE tenant_id=ident.tenant_id AND analysis_run_id=p_analysis ORDER BY version DESC LIMIT 1;
 IF item.id IS NULL THEN RAISE insufficient_privilege USING MESSAGE='recommendation unavailable'; END IF;
 RETURN jsonb_build_object('id',item.id,'analysis_id',item.analysis_run_id,'version',item.version,
  'source_digest',item.source_digest,'recommended_type',item.recommended_type,'rationale',item.rationale,
  'candidate_ids',to_jsonb(item.candidate_ids),'risks',item.risks,'required_reviews',item.required_reviews,
  'supported_generation',item.supported_generation,'availability_reason',item.availability_reason);
END $$;

CREATE FUNCTION backend_store_discovery(p_analysis uuid,p_payload jsonb) RETURNS jsonb
LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog,studio_admission,pg_temp AS $$
DECLARE ident runtime_principal; analysis_row analysis; item jsonb; rec jsonb;
BEGIN
 ident=runtime_identity('backend');
 SELECT * INTO analysis_row FROM analysis WHERE tenant_id=ident.tenant_id AND id=p_analysis AND status='succeeded' FOR SHARE;
 IF analysis_row.id IS NULL THEN RAISE insufficient_privilege USING MESSAGE='succeeded analysis unavailable'; END IF;
 IF EXISTS(SELECT 1 FROM recommendation WHERE tenant_id=ident.tenant_id AND analysis_run_id=p_analysis) THEN
  RETURN jsonb_build_object('analysis_id',p_analysis,'candidates',backend_get_candidates(p_analysis)->'items',
   'recommendation',backend_get_recommendation(p_analysis));
 END IF;
 IF p_payload->>'analysis_id' IS DISTINCT FROM p_analysis::text OR jsonb_typeof(p_payload->'candidates')<>'array'
  OR jsonb_array_length(p_payload->'candidates')>1000 OR jsonb_typeof(p_payload->'recommendation')<>'object' THEN
  RAISE check_violation USING MESSAGE='invalid discovery payload';
 END IF;
 FOR item IN SELECT value FROM jsonb_array_elements(p_payload->'candidates') LOOP
  INSERT INTO candidate(tenant_id,analysis_id,id,eligible,source_reference,graph_node_id,finding_id,operation_type,
   side_effects,sensitivity,required_scopes,input_schema,output_schema,eligibility,reason_codes,evidence,detector,
   provenance,confidence,domain_service_reference)
  VALUES(ident.tenant_id,p_analysis,(item->>'id')::uuid,(item->>'eligibility')='allowed',
   (item->'evidence'->0->>'path')||':'||(item->'evidence'->0->>'line_start'),(item->>'graph_node_id')::uuid,
   item->>'finding_id',item->>'operation_type',
   (SELECT coalesce(array_agg(value),ARRAY[]::text[]) FROM jsonb_array_elements_text(item->'side_effects')),
   item->>'sensitivity',(SELECT coalesce(array_agg(value),ARRAY[]::text[]) FROM jsonb_array_elements_text(item->'required_scopes')),
   item->'input_schema',item->'output_schema',item->>'eligibility',
   (SELECT coalesce(array_agg(value),ARRAY[]::text[]) FROM jsonb_array_elements_text(item->'reason_codes')),
   item->'evidence',item->'detector',item->>'provenance',item->'confidence',item->>'domain_service_reference');
 END LOOP;
 rec=p_payload->'recommendation';
 IF rec->>'source_digest' IS DISTINCT FROM analysis_row.source_digest::text OR (rec->>'supported_generation')::boolean THEN
  RAISE check_violation USING MESSAGE='discovery recommendation must remain source-bound and generation-locked';
 END IF;
 INSERT INTO recommendation(tenant_id,analysis_run_id,id,version,source_digest,recommended_type,rationale,candidate_ids,
  risks,required_reviews,supported_generation,availability_reason)
 VALUES(ident.tenant_id,p_analysis,(rec->>'id')::uuid,(rec->>'version')::integer,analysis_row.source_digest,
  rec->>'recommended_type',rec->>'rationale',
  (SELECT coalesce(array_agg(value::uuid),ARRAY[]::uuid[]) FROM jsonb_array_elements_text(rec->'candidate_ids')),
  rec->'risks',rec->'required_reviews',false,rec->>'availability_reason');
 RETURN jsonb_build_object('analysis_id',p_analysis,'candidates',backend_get_candidates(p_analysis)->'items',
  'recommendation',backend_get_recommendation(p_analysis));
END $$;

ALTER FUNCTION backend_get_candidates(uuid) OWNER TO studio_kernel_owner;
ALTER FUNCTION backend_get_recommendation(uuid) OWNER TO studio_kernel_owner;
ALTER FUNCTION backend_store_discovery(uuid,jsonb) OWNER TO studio_kernel_owner;
REVOKE ALL ON FUNCTION backend_get_candidates(uuid),backend_get_recommendation(uuid),backend_store_discovery(uuid,jsonb) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION backend_get_candidates(uuid),backend_get_recommendation(uuid),backend_store_discovery(uuid,jsonb) TO studio_backend;
COMMIT;
