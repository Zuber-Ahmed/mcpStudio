-- One-time foundation migration. Existing unlinked rows must be explicitly reconciled first.
-- NOT NULL/FK validation intentionally fails rather than inventing provenance/backfills.
BEGIN;
SET LOCAL ROLE studio_kernel_owner;
SET LOCAL search_path=studio_admission,pg_catalog,pg_temp;
CREATE TABLE source_snapshot(tenant_id uuid NOT NULL,project_id uuid NOT NULL,id uuid NOT NULL,
 source_digest digest NOT NULL,storage_key text NOT NULL CHECK(length(trim(storage_key))>0),
 resolved_revision text NOT NULL CHECK(length(trim(resolved_revision))>0),created_at timestamptz NOT NULL DEFAULT clock_timestamp(),
 PRIMARY KEY(tenant_id,id),UNIQUE(tenant_id,project_id,id,source_digest,resolved_revision),
 FOREIGN KEY(tenant_id,project_id) REFERENCES project);
CREATE TRIGGER frozen_snapshot BEFORE UPDATE OR DELETE ON source_snapshot FOR EACH ROW EXECUTE FUNCTION frozen_record();
ALTER TABLE analysis ADD COLUMN snapshot_id uuid NOT NULL, ADD COLUMN resolved_revision text NOT NULL,
 ADD COLUMN status text NOT NULL DEFAULT 'queued' CHECK(status IN ('queued','running','succeeded','failed','cancelled')),
 ADD COLUMN created_at timestamptz NOT NULL DEFAULT clock_timestamp(),ADD COLUMN completed_at timestamptz,
 ADD COLUMN diagnostics jsonb NOT NULL DEFAULT '[]' CHECK(jsonb_typeof(diagnostics)='array'),
 ADD COLUMN analyzer_versions jsonb NOT NULL DEFAULT '{}' CHECK(jsonb_typeof(analyzer_versions)='object'),
 ADD COLUMN scope jsonb NOT NULL DEFAULT '{}' CHECK(jsonb_typeof(scope)='object'),
 ADD COLUMN semantic_mode text NOT NULL DEFAULT 'disabled' CHECK(semantic_mode IN ('disabled','consented')),
 ADD COLUMN consent_id uuid,ADD COLUMN previous_run_id uuid,
 ADD CONSTRAINT analysis_terminal_time CHECK((status IN ('succeeded','failed','cancelled'))=(completed_at IS NOT NULL)),
 ADD CONSTRAINT analysis_snapshot_scope FOREIGN KEY(tenant_id,project_id,snapshot_id,source_digest,resolved_revision)
 REFERENCES source_snapshot(tenant_id,project_id,id,source_digest,resolved_revision),
 ADD CONSTRAINT analysis_consent_reference FOREIGN KEY(tenant_id,consent_id) REFERENCES consent,
 ADD CONSTRAINT analysis_previous_scope FOREIGN KEY(tenant_id,project_id,previous_run_id) REFERENCES analysis(tenant_id,project_id,id),
 ADD CONSTRAINT analysis_snapshot_identity UNIQUE(tenant_id,id,snapshot_id),
 ADD CONSTRAINT analysis_digest_identity UNIQUE(tenant_id,id,source_digest),
 ADD CONSTRAINT analysis_consent_required CHECK((semantic_mode='disabled' AND consent_id IS NULL) OR (semantic_mode='consented' AND consent_id IS NOT NULL));
CREATE OR REPLACE FUNCTION keep_analysis_identity() RETURNS trigger LANGUAGE plpgsql
SET search_path=pg_catalog,studio_admission,pg_temp AS $$
BEGIN
 IF (to_jsonb(OLD)-'next_version'-'status'-'completed_at'-'diagnostics') IS DISTINCT FROM
 (to_jsonb(NEW)-'next_version'-'status'-'completed_at'-'diagnostics') OR
 (OLD.status IN ('succeeded','failed','cancelled') AND (to_jsonb(OLD)-'next_version') IS DISTINCT FROM (to_jsonb(NEW)-'next_version')) THEN
 RAISE check_violation USING MESSAGE='analysis source identity or terminal result immutable'; END IF;
 RETURN NEW;
END $$;
CREATE TABLE graph_node(tenant_id uuid NOT NULL,analysis_run_id uuid NOT NULL,id uuid NOT NULL,
 kind text NOT NULL CHECK(length(trim(kind))>0),label text NOT NULL CHECK(length(trim(label))>0),
 evidence jsonb NOT NULL CHECK(CASE WHEN jsonb_typeof(evidence)='array' THEN jsonb_array_length(evidence)>0 ELSE false END),
 provenance text NOT NULL CHECK(length(trim(provenance))>0),confidence jsonb NOT NULL CHECK(jsonb_typeof(confidence)='object'),
 PRIMARY KEY(tenant_id,id),UNIQUE(tenant_id,analysis_run_id,id),FOREIGN KEY(tenant_id,analysis_run_id) REFERENCES analysis);
CREATE TABLE graph_edge(tenant_id uuid NOT NULL,analysis_run_id uuid NOT NULL,id uuid NOT NULL,
 from_node_id uuid NOT NULL,to_node_id uuid NOT NULL,kind text NOT NULL CHECK(length(trim(kind))>0),
 provenance text NOT NULL CHECK(length(trim(provenance))>0),
 evidence jsonb NOT NULL CHECK(CASE WHEN jsonb_typeof(evidence)='array' THEN jsonb_array_length(evidence)>0 ELSE false END),
 PRIMARY KEY(tenant_id,id),FOREIGN KEY(tenant_id,analysis_run_id,from_node_id) REFERENCES graph_node(tenant_id,analysis_run_id,id),
 FOREIGN KEY(tenant_id,analysis_run_id,to_node_id) REFERENCES graph_node(tenant_id,analysis_run_id,id));
CREATE TRIGGER frozen_node BEFORE UPDATE OR DELETE ON graph_node FOR EACH ROW EXECUTE FUNCTION frozen_record();
CREATE TRIGGER frozen_edge BEFORE UPDATE OR DELETE ON graph_edge FOR EACH ROW EXECUTE FUNCTION frozen_record();
ALTER TABLE candidate ADD COLUMN graph_node_id uuid NOT NULL,
 ADD CONSTRAINT candidate_node_scope FOREIGN KEY(tenant_id,analysis_id,graph_node_id) REFERENCES graph_node(tenant_id,analysis_run_id,id);
CREATE TABLE recommendation(tenant_id uuid NOT NULL,analysis_run_id uuid NOT NULL,id uuid NOT NULL,
 version integer NOT NULL CHECK(version>0),source_digest digest NOT NULL,
 recommended_type text NOT NULL CHECK(recommended_type IN ('server','client','both','none')),
 rationale text NOT NULL CHECK(length(trim(rationale))>0),candidate_ids uuid[] NOT NULL,
 risks jsonb NOT NULL CHECK(jsonb_typeof(risks)='array'),required_reviews jsonb NOT NULL CHECK(jsonb_typeof(required_reviews)='array'),
 supported_generation boolean NOT NULL,availability_reason text NOT NULL CHECK(length(trim(availability_reason))>0),
 PRIMARY KEY(tenant_id,id),UNIQUE(tenant_id,analysis_run_id,version),UNIQUE(tenant_id,analysis_run_id,id,version),
 FOREIGN KEY(tenant_id,analysis_run_id,source_digest) REFERENCES analysis(tenant_id,id,source_digest),
 CHECK(array_position(candidate_ids,NULL) IS NULL),
 CHECK(NOT supported_generation OR (recommended_type='server' AND cardinality(candidate_ids)>0)));
CREATE FUNCTION recommendation_scope() RETURNS trigger LANGUAGE plpgsql SET search_path=pg_catalog,studio_admission,pg_temp AS $$
DECLARE state text; v integer;
BEGIN
 SELECT status INTO state FROM analysis WHERE tenant_id=NEW.tenant_id AND id=NEW.analysis_run_id FOR UPDATE;
 IF state IS DISTINCT FROM 'succeeded' THEN RAISE check_violation USING MESSAGE='recommendation requires succeeded analysis'; END IF;
 SELECT coalesce(max(version),0)+1 INTO v FROM recommendation WHERE tenant_id=NEW.tenant_id AND analysis_run_id=NEW.analysis_run_id;
 IF NEW.version<>v OR cardinality(NEW.candidate_ids)<>(SELECT count(DISTINCT x) FROM unnest(NEW.candidate_ids) x)
 OR EXISTS(SELECT 1 FROM unnest(NEW.candidate_ids) x WHERE NOT EXISTS(SELECT 1 FROM candidate c
 WHERE c.tenant_id=NEW.tenant_id AND c.analysis_id=NEW.analysis_run_id AND c.id=x AND (NOT NEW.supported_generation OR c.eligible))) THEN
 RAISE check_violation USING MESSAGE='recommendation version or candidate scope invalid'; END IF;
 RETURN NEW;
END $$;
CREATE TRIGGER scoped_recommendation BEFORE INSERT ON recommendation FOR EACH ROW EXECUTE FUNCTION recommendation_scope();
CREATE TRIGGER frozen_recommendation BEFORE UPDATE OR DELETE ON recommendation FOR EACH ROW EXECUTE FUNCTION frozen_record();
ALTER TABLE plan ADD COLUMN snapshot_id uuid NOT NULL,ADD COLUMN recommendation_id uuid NOT NULL,ADD COLUMN recommendation_version integer NOT NULL,
 ADD CONSTRAINT plan_snapshot_scope FOREIGN KEY(tenant_id,analysis_id,snapshot_id) REFERENCES analysis(tenant_id,id,snapshot_id),
 ADD CONSTRAINT plan_recommendation_scope FOREIGN KEY(tenant_id,analysis_id,recommendation_id,recommendation_version)
 REFERENCES recommendation(tenant_id,analysis_run_id,id,version);
CREATE OR REPLACE FUNCTION new_plan(t uuid,a uuid,i uuid,h digest) RETURNS integer LANGUAGE plpgsql
SET search_path=pg_catalog,studio_admission,pg_temp AS $$
BEGIN RAISE check_violation USING MESSAGE='explicit recommendation ID/version required'; END $$;
CREATE FUNCTION new_plan(t uuid,a uuid,i uuid,h digest,r uuid,rv integer) RETURNS integer LANGUAGE plpgsql
SET search_path=pg_catalog,studio_admission,pg_temp AS $$
DECLARE an analysis; rec recommendation; v integer;
BEGIN
 SELECT * INTO an FROM analysis WHERE tenant_id=t AND id=a FOR UPDATE;
 SELECT * INTO rec FROM recommendation WHERE tenant_id=t AND id=r AND analysis_run_id=a AND version=rv;
 IF an.id IS NULL OR an.status<>'succeeded' OR rec.id IS NULL OR NOT rec.supported_generation THEN
 RAISE check_violation USING MESSAGE='analysis or recommendation unavailable for generation'; END IF;
 UPDATE analysis SET next_version=next_version+1 WHERE tenant_id=t AND id=a RETURNING next_version-1 INTO v;
 UPDATE plan SET current=false WHERE tenant_id=t AND analysis_id=a AND current;
 INSERT INTO plan(tenant_id,analysis_id,id,version,plan_hash,current,snapshot_id,recommendation_id,recommendation_version)
 VALUES(t,a,i,v,h,true,an.snapshot_id,r,rv);
 RETURN v;
END $$;
-- Keep migration-002 byte/candidate/policy checks, then add the ownership chain.
ALTER FUNCTION bind_payload() RENAME TO bind_payload_v2;
CREATE FUNCTION bind_payload() RETURNS trigger LANGUAGE plpgsql SET search_path=pg_catalog,studio_admission,pg_temp AS $$
DECLARE p plan; rec recommendation; body jsonb;
BEGIN
 SELECT * INTO p FROM plan WHERE tenant_id=NEW.tenant_id AND id=NEW.plan_id FOR UPDATE;
 SELECT * INTO rec FROM recommendation WHERE tenant_id=p.tenant_id AND id=p.recommendation_id AND version=p.recommendation_version;
 body=convert_from(NEW.canonical_payload,'UTF8')::jsonb;
 IF body->>'snapshot_id' IS DISTINCT FROM p.snapshot_id::text
 OR body->>'recommendation_id' IS DISTINCT FROM p.recommendation_id::text
 OR body->>'recommendation_version' IS DISTINCT FROM p.recommendation_version::text
 OR EXISTS(SELECT 1 FROM jsonb_array_elements_text(body->'candidate_ids') x WHERE NOT x.value::uuid=ANY(rec.candidate_ids)) THEN
 RAISE check_violation USING MESSAGE='plan recommendation/snapshot binding mismatch'; END IF;
 RETURN NEW;
END $$;
-- The existing check_binding trigger still refers to the renamed v2 function by OID.
CREATE TRIGGER check_binding_chain BEFORE INSERT ON plan_binding FOR EACH ROW EXECUTE FUNCTION bind_payload();
CREATE TRIGGER audit_snapshot AFTER INSERT ON source_snapshot FOR EACH ROW EXECUTE FUNCTION record_audit();
CREATE TRIGGER audit_recommendation AFTER INSERT ON recommendation FOR EACH ROW EXECUTE FUNCTION record_audit();
REVOKE ALL ON ALL TABLES IN SCHEMA studio_admission FROM PUBLIC,studio_backend,studio_worker;
REVOKE ALL ON FUNCTION new_plan(uuid,uuid,uuid,digest,uuid,integer),bind_payload(),recommendation_scope() FROM PUBLIC,studio_backend,studio_worker;
COMMIT;
