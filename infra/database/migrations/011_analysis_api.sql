BEGIN;
SET LOCAL ROLE studio_kernel_owner;
SET LOCAL search_path=studio_admission,pg_catalog,pg_temp;

CREATE FUNCTION backend_store_analysis(p_payload jsonb) RETURNS jsonb
LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog,studio_admission,pg_temp AS $$
DECLARE ident runtime_principal; project_row project; node jsonb; edge jsonb;
BEGIN
 ident=runtime_identity('backend');
 IF jsonb_typeof(p_payload)<>'object' OR jsonb_typeof(p_payload->'nodes')<>'array'
  OR jsonb_typeof(p_payload->'edges')<>'array' OR jsonb_array_length(p_payload->'nodes')>5000
  OR jsonb_array_length(p_payload->'edges')>10000 THEN
  RAISE check_violation USING MESSAGE='invalid or oversized analysis payload';
 END IF;
 SELECT * INTO project_row FROM project WHERE tenant_id=ident.tenant_id AND id=(p_payload->>'project_id')::uuid FOR SHARE;
 IF project_row.id IS NULL OR project_row.source->>'kind'<>'local' THEN
  RAISE insufficient_privilege USING MESSAGE='local project unavailable';
 END IF;
 INSERT INTO source_snapshot(tenant_id,project_id,id,source_digest,storage_key,resolved_revision)
 VALUES(ident.tenant_id,project_row.id,(p_payload->>'snapshot_id')::uuid,(p_payload->>'source_digest')::digest,
  p_payload->>'storage_key',p_payload->>'resolved_revision');
 INSERT INTO analysis(tenant_id,project_id,id,source_digest,snapshot_id,resolved_revision,status,completed_at,
  diagnostics,analyzer_versions,scope,semantic_mode)
 VALUES(ident.tenant_id,project_row.id,(p_payload->>'id')::uuid,(p_payload->>'source_digest')::digest,
  (p_payload->>'snapshot_id')::uuid,p_payload->>'resolved_revision','succeeded',clock_timestamp(),
  coalesce(p_payload->'diagnostics','[]'::jsonb),p_payload->'analyzer_versions',coalesce(p_payload->'scope','{}'::jsonb),'disabled');
 FOR node IN SELECT value FROM jsonb_array_elements(p_payload->'nodes') LOOP
  INSERT INTO graph_node(tenant_id,analysis_run_id,id,kind,label,evidence,provenance,confidence)
  VALUES(ident.tenant_id,(p_payload->>'id')::uuid,(node->>'id')::uuid,node->>'kind',node->>'label',node->'evidence',
   node->>'provenance',node->'confidence');
 END LOOP;
 FOR edge IN SELECT value FROM jsonb_array_elements(p_payload->'edges') LOOP
  INSERT INTO graph_edge(tenant_id,analysis_run_id,id,from_node_id,to_node_id,kind,provenance,evidence)
  VALUES(ident.tenant_id,(p_payload->>'id')::uuid,(edge->>'id')::uuid,(edge->>'from_node_id')::uuid,
   (edge->>'to_node_id')::uuid,edge->>'kind',edge->>'provenance',edge->'evidence');
 END LOOP;
 RETURN backend_get_analysis((p_payload->>'id')::uuid);
END $$;

CREATE FUNCTION backend_get_analysis(p_id uuid) RETURNS jsonb
LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog,studio_admission,pg_temp AS $$
DECLARE ident runtime_principal; item analysis; node_count integer; edge_count integer;
BEGIN
 ident=runtime_identity('backend');
 SELECT * INTO item FROM analysis WHERE tenant_id=ident.tenant_id AND id=p_id;
 IF item.id IS NULL THEN RAISE insufficient_privilege USING MESSAGE='analysis unavailable'; END IF;
 SELECT count(*) INTO node_count FROM graph_node WHERE tenant_id=ident.tenant_id AND analysis_run_id=item.id;
 SELECT count(*) INTO edge_count FROM graph_edge WHERE tenant_id=ident.tenant_id AND analysis_run_id=item.id;
 RETURN jsonb_build_object('id',item.id,'project_id',item.project_id,'snapshot_id',item.snapshot_id,
  'source_digest',item.source_digest,'resolved_revision',item.resolved_revision,'status',item.status,
  'created_at',item.created_at,'completed_at',item.completed_at,'diagnostics',item.diagnostics,
  'analyzer_versions',item.analyzer_versions,'scope',item.scope,'node_count',node_count,'edge_count',edge_count);
END $$;

CREATE FUNCTION backend_get_analysis_graph(p_id uuid) RETURNS jsonb
LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog,studio_admission,pg_temp AS $$
DECLARE ident runtime_principal; exists_id uuid; nodes jsonb; edges jsonb;
BEGIN
 ident=runtime_identity('backend');
 SELECT id INTO exists_id FROM analysis WHERE tenant_id=ident.tenant_id AND id=p_id;
 IF exists_id IS NULL THEN RAISE insufficient_privilege USING MESSAGE='analysis unavailable'; END IF;
 SELECT coalesce(jsonb_agg(jsonb_build_object('id',id,'kind',kind,'label',label,'evidence',evidence,
  'provenance',provenance,'confidence',confidence) ORDER BY label,id),'[]'::jsonb) INTO nodes
 FROM graph_node WHERE tenant_id=ident.tenant_id AND analysis_run_id=p_id;
 SELECT coalesce(jsonb_agg(jsonb_build_object('id',id,'from_node_id',from_node_id,'to_node_id',to_node_id,
  'kind',kind,'provenance',provenance,'evidence',evidence) ORDER BY kind,id),'[]'::jsonb) INTO edges
 FROM graph_edge WHERE tenant_id=ident.tenant_id AND analysis_run_id=p_id;
 RETURN jsonb_build_object('analysis_id',p_id,'nodes',nodes,'edges',edges,'truncated',false);
END $$;

CREATE OR REPLACE FUNCTION backend_list_projects(p_query text,p_limit integer) RETURNS jsonb
LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog,studio_admission,pg_temp AS $$
DECLARE ident runtime_principal; result jsonb;
BEGIN
 ident=runtime_identity('backend');
 IF p_limit<1 OR p_limit>100 OR length(coalesce(p_query,''))>200 THEN RAISE check_violation USING MESSAGE='invalid project query'; END IF;
 SELECT coalesce(jsonb_agg(jsonb_build_object('id',p.id,'name',p.name,'source',p.source,'created_at',p.created_at,
  'updated_at',p.updated_at,'workflow_status',CASE WHEN latest.id IS NULL THEN 'created' ELSE 'analyzed' END,
  'latest_analysis_id',latest.id,'latest_plan_id',NULL,'latest_generation_id',NULL,'latest_validation_id',NULL)
  ORDER BY p.updated_at DESC),'[]'::jsonb) INTO result
 FROM (SELECT * FROM project WHERE tenant_id=ident.tenant_id AND (coalesce(p_query,'')='' OR name ILIKE '%'||p_query||'%')
  ORDER BY updated_at DESC LIMIT p_limit) p
 LEFT JOIN LATERAL (SELECT a.id FROM analysis a WHERE a.tenant_id=p.tenant_id AND a.project_id=p.id ORDER BY a.created_at DESC,a.id DESC LIMIT 1) latest ON true;
 RETURN jsonb_build_object('items',result);
END $$;

CREATE OR REPLACE FUNCTION backend_get_project(p_id uuid) RETURNS jsonb
LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog,studio_admission,pg_temp AS $$
DECLARE ident runtime_principal; item project; latest uuid;
BEGIN
 ident=runtime_identity('backend'); SELECT * INTO item FROM project WHERE tenant_id=ident.tenant_id AND id=p_id;
 IF item.id IS NULL THEN RAISE insufficient_privilege USING MESSAGE='project unavailable'; END IF;
 SELECT id INTO latest FROM analysis WHERE tenant_id=ident.tenant_id AND project_id=item.id ORDER BY created_at DESC,id DESC LIMIT 1;
 RETURN jsonb_build_object('id',item.id,'name',item.name,'source',item.source,'created_at',item.created_at,
  'updated_at',item.updated_at,'workflow_status',CASE WHEN latest IS NULL THEN 'created' ELSE 'analyzed' END,
  'latest_analysis_id',latest,'latest_plan_id',NULL,'latest_generation_id',NULL,'latest_validation_id',NULL);
END $$;

ALTER FUNCTION backend_store_analysis(jsonb) OWNER TO studio_kernel_owner;
ALTER FUNCTION backend_get_analysis(uuid) OWNER TO studio_kernel_owner;
ALTER FUNCTION backend_get_analysis_graph(uuid) OWNER TO studio_kernel_owner;
REVOKE ALL ON FUNCTION backend_store_analysis(jsonb),backend_get_analysis(uuid),backend_get_analysis_graph(uuid) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION backend_store_analysis(jsonb),backend_get_analysis(uuid),backend_get_analysis_graph(uuid) TO studio_backend;
COMMIT;
