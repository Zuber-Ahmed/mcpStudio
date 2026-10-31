BEGIN;
SET LOCAL ROLE studio_kernel_owner;
SET LOCAL search_path=studio_admission,pg_catalog,pg_temp;

CREATE FUNCTION backend_create_project(p_name text,p_source jsonb) RETURNS jsonb
LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog,studio_admission,pg_temp AS $$
DECLARE ident runtime_principal; item project;
BEGIN
 ident=runtime_identity('backend');
 IF length(trim(p_name)) NOT BETWEEN 1 AND 200 OR NOT source_metadata_valid(p_source) THEN
  RAISE check_violation USING MESSAGE='invalid project input';
 END IF;
 INSERT INTO project(tenant_id,id,name,source) VALUES(ident.tenant_id,gen_random_uuid(),trim(p_name),p_source) RETURNING * INTO item;
 RETURN jsonb_build_object('id',item.id,'name',item.name,'source',item.source,'created_at',item.created_at,
  'updated_at',item.updated_at,'workflow_status','created','latest_analysis_id',NULL,'latest_plan_id',NULL,
  'latest_generation_id',NULL,'latest_validation_id',NULL);
END $$;

CREATE FUNCTION backend_list_projects(p_query text,p_limit integer) RETURNS jsonb
LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog,studio_admission,pg_temp AS $$
DECLARE ident runtime_principal; result jsonb;
BEGIN
 ident=runtime_identity('backend');
 IF p_limit NOT BETWEEN 1 AND 100 OR length(coalesce(p_query,''))>200 THEN RAISE check_violation USING MESSAGE='invalid project query'; END IF;
 SELECT coalesce(jsonb_agg(jsonb_build_object('id',p.id,'name',p.name,'source',p.source,'created_at',p.created_at,
  'updated_at',p.updated_at,'workflow_status','created','latest_analysis_id',NULL,'latest_plan_id',NULL,
  'latest_generation_id',NULL,'latest_validation_id',NULL) ORDER BY p.updated_at DESC),'[]'::jsonb)
 INTO result FROM (SELECT * FROM project WHERE tenant_id=ident.tenant_id
  AND (coalesce(p_query,'')='' OR name ILIKE '%'||p_query||'%') ORDER BY updated_at DESC LIMIT p_limit) p;
 RETURN jsonb_build_object('items',result);
END $$;

CREATE FUNCTION backend_get_project(p_id uuid) RETURNS jsonb
LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog,studio_admission,pg_temp AS $$
DECLARE ident runtime_principal; item project;
BEGIN
 ident=runtime_identity('backend');SELECT * INTO item FROM project WHERE tenant_id=ident.tenant_id AND id=p_id;
 IF item.id IS NULL THEN RAISE insufficient_privilege USING MESSAGE='project unavailable'; END IF;
 RETURN jsonb_build_object('id',item.id,'name',item.name,'source',item.source,'created_at',item.created_at,
  'updated_at',item.updated_at,'workflow_status','created','latest_analysis_id',NULL,'latest_plan_id',NULL,
  'latest_generation_id',NULL,'latest_validation_id',NULL);
END $$;

ALTER FUNCTION backend_create_project(text,jsonb) OWNER TO studio_kernel_owner;
ALTER FUNCTION backend_list_projects(text,integer) OWNER TO studio_kernel_owner;
ALTER FUNCTION backend_get_project(uuid) OWNER TO studio_kernel_owner;
REVOKE ALL ON FUNCTION backend_create_project(text,jsonb),backend_list_projects(text,integer),backend_get_project(uuid) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION backend_create_project(text,jsonb),backend_list_projects(text,integer),backend_get_project(uuid) TO studio_backend;
COMMIT;
