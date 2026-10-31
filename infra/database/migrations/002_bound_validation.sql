-- Second foundation slice; apply after 001 in an isolated review database first.
BEGIN;
SET LOCAL search_path=studio_admission,pg_catalog;
CREATE FUNCTION frozen_record() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN RAISE check_violation USING MESSAGE='immutable record'; END $$;
CREATE FUNCTION unique_check_names(v text[]) RETURNS boolean LANGUAGE sql IMMUTABLE AS $$
 SELECT cardinality(v)>0 AND array_position(v,NULL) IS NULL
 AND NOT EXISTS(SELECT 1 FROM unnest(v) x WHERE length(trim(x))=0)
 AND cardinality(v)=(SELECT count(DISTINCT x) FROM unnest(v) x)
$$;
CREATE TABLE validation_policy(tenant_id uuid NOT NULL REFERENCES tenant,id uuid NOT NULL,version integer NOT NULL CHECK(version>0),
 required_checks text[] NOT NULL CHECK(unique_check_names(required_checks)),
 PRIMARY KEY(tenant_id,id,version));
CREATE TRIGGER frozen_policy BEFORE UPDATE OR DELETE ON validation_policy FOR EACH ROW EXECUTE FUNCTION frozen_record();
CREATE TABLE candidate(tenant_id uuid NOT NULL,analysis_id uuid NOT NULL,id uuid NOT NULL,
 eligible boolean NOT NULL,source_reference text NOT NULL CHECK(length(trim(source_reference))>0),
 PRIMARY KEY(tenant_id,analysis_id,id),FOREIGN KEY(tenant_id,analysis_id) REFERENCES analysis);
CREATE TRIGGER frozen_candidate BEFORE UPDATE OR DELETE ON candidate FOR EACH ROW EXECUTE FUNCTION frozen_record();
CREATE TABLE plan_binding(tenant_id uuid NOT NULL,plan_id uuid NOT NULL,policy_id uuid NOT NULL,policy_version integer NOT NULL,
 canonical_payload bytea NOT NULL,source_digest digest NOT NULL,
 PRIMARY KEY(tenant_id,plan_id),UNIQUE(tenant_id,plan_id,policy_id,policy_version),
 FOREIGN KEY(tenant_id,plan_id) REFERENCES plan,
 FOREIGN KEY(tenant_id,policy_id,policy_version) REFERENCES validation_policy);
CREATE TABLE plan_candidate(tenant_id uuid NOT NULL,plan_id uuid NOT NULL,analysis_id uuid NOT NULL,candidate_id uuid NOT NULL,
 PRIMARY KEY(tenant_id,plan_id,candidate_id),
 FOREIGN KEY(tenant_id,plan_id) REFERENCES plan_binding,
 FOREIGN KEY(tenant_id,analysis_id,candidate_id) REFERENCES candidate);
CREATE FUNCTION bind_payload() RETURNS trigger LANGUAGE plpgsql SET search_path=studio_admission,pg_catalog AS $$
DECLARE p plan; a analysis; body jsonb; ids uuid[];
BEGIN
 SELECT * INTO p FROM plan WHERE tenant_id=NEW.tenant_id AND id=NEW.plan_id FOR UPDATE;
 SELECT * INTO a FROM analysis WHERE tenant_id=p.tenant_id AND id=p.analysis_id;
 body=convert_from(NEW.canonical_payload,'UTF8')::jsonb;
 IF encode(sha256(NEW.canonical_payload),'hex') IS DISTINCT FROM p.plan_hash
 OR NEW.source_digest IS DISTINCT FROM a.source_digest
 OR body->>'analysis_id' IS DISTINCT FROM p.analysis_id::text
 OR body->>'source_digest' IS DISTINCT FROM a.source_digest::text
 OR body->>'policy_id' IS DISTINCT FROM NEW.policy_id::text
 OR body->>'policy_version' IS DISTINCT FROM NEW.policy_version::text
 OR body->>'mode' IS DISTINCT FROM 'server'
 OR body->>'transport' IS DISTINCT FROM 'stdio'
 OR jsonb_typeof(body->'candidate_ids') IS DISTINCT FROM 'array' THEN
  RAISE check_violation USING MESSAGE='plan payload hash or scope mismatch'; END IF;
 SELECT array_agg(value::uuid) INTO ids FROM jsonb_array_elements_text(body->'candidate_ids');
 IF ids IS NULL OR cardinality(ids)<>(SELECT count(DISTINCT x) FROM unnest(ids) x)
 OR EXISTS(SELECT 1 FROM unnest(ids) x WHERE NOT EXISTS(SELECT 1 FROM candidate c
 WHERE c.tenant_id=NEW.tenant_id AND c.analysis_id=p.analysis_id AND c.id=x AND c.eligible)) THEN
  RAISE check_violation USING MESSAGE='candidate set unavailable or ineligible'; END IF;
 RETURN NEW;
END $$;
CREATE TRIGGER check_binding BEFORE INSERT ON plan_binding FOR EACH ROW EXECUTE FUNCTION bind_payload();
CREATE FUNCTION link_candidates() RETURNS trigger LANGUAGE plpgsql SET search_path=studio_admission,pg_catalog AS $$
BEGIN
 INSERT INTO plan_candidate
 SELECT NEW.tenant_id,NEW.plan_id,p.analysis_id,v.value::uuid FROM plan p,
 jsonb_array_elements_text(convert_from(NEW.canonical_payload,'UTF8')::jsonb->'candidate_ids') v
 WHERE p.tenant_id=NEW.tenant_id AND p.id=NEW.plan_id;
 RETURN NEW;
END $$;
CREATE TRIGGER link_binding AFTER INSERT ON plan_binding FOR EACH ROW EXECUTE FUNCTION link_candidates();
CREATE TRIGGER frozen_binding BEFORE UPDATE OR DELETE ON plan_binding FOR EACH ROW EXECUTE FUNCTION frozen_record();
CREATE TRIGGER frozen_selection BEFORE UPDATE OR DELETE ON plan_candidate FOR EACH ROW EXECUTE FUNCTION frozen_record();
CREATE FUNCTION protect_plan() RETURNS trigger LANGUAGE plpgsql SET search_path=studio_admission,pg_catalog AS $$
BEGIN
 IF TG_OP='DELETE' THEN RAISE check_violation USING MESSAGE='plan retained'; END IF;
 IF (to_jsonb(NEW)-'current') IS DISTINCT FROM (to_jsonb(OLD)-'current') THEN
 RAISE check_violation USING MESSAGE='plan revision immutable'; END IF;
 RETURN NEW;
END $$;
CREATE TRIGGER immutable_plan BEFORE UPDATE OR DELETE ON plan FOR EACH ROW EXECUTE FUNCTION protect_plan();
CREATE FUNCTION require_binding() RETURNS trigger LANGUAGE plpgsql SET search_path=studio_admission,pg_catalog AS $$
BEGIN
 PERFORM 1 FROM plan_binding WHERE tenant_id=NEW.tenant_id AND plan_id=NEW.plan_id;
 IF NOT FOUND THEN RAISE check_violation USING MESSAGE='generation requires bound payload'; END IF;
 RETURN NEW;
END $$;
CREATE TRIGGER bound_admission BEFORE INSERT ON run FOR EACH ROW EXECUTE FUNCTION require_binding();
CREATE FUNCTION keep_run_identity() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
 IF OLD.status IN ('succeeded','failed','cancelled') OR
 (to_jsonb(OLD)-'status'-'completed_at') IS DISTINCT FROM (to_jsonb(NEW)-'status'-'completed_at') THEN
 RAISE check_violation USING MESSAGE='run binding or terminal state immutable'; END IF;
 RETURN NEW;
END $$;
CREATE TRIGGER immutable_run BEFORE UPDATE ON run FOR EACH ROW EXECUTE FUNCTION keep_run_identity();
CREATE TRIGGER retain_run BEFORE DELETE ON run FOR EACH ROW EXECUTE FUNCTION frozen_record();
CREATE FUNCTION keep_approval_identity() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
 IF (to_jsonb(OLD)-'revoked_at') IS DISTINCT FROM (to_jsonb(NEW)-'revoked_at') OR OLD.revoked_at IS NOT NULL THEN
 RAISE check_violation USING MESSAGE='approval identity or revocation immutable'; END IF;
 RETURN NEW;
END $$;
CREATE TRIGGER immutable_approval BEFORE UPDATE ON approval FOR EACH ROW EXECUTE FUNCTION keep_approval_identity();
CREATE TRIGGER retain_approval BEFORE DELETE ON approval FOR EACH ROW EXECUTE FUNCTION frozen_record();
CREATE FUNCTION keep_analysis_identity() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
 IF (to_jsonb(OLD)-'next_version') IS DISTINCT FROM (to_jsonb(NEW)-'next_version') THEN
 RAISE check_violation USING MESSAGE='analysis source identity immutable'; END IF;
 RETURN NEW;
END $$;
CREATE TRIGGER immutable_analysis BEFORE UPDATE ON analysis FOR EACH ROW EXECUTE FUNCTION keep_analysis_identity();
CREATE FUNCTION selection_scope() RETURNS trigger LANGUAGE plpgsql SET search_path=studio_admission,pg_catalog AS $$
BEGIN
 PERFORM 1 FROM plan_binding b JOIN plan p ON p.tenant_id=b.tenant_id AND p.id=b.plan_id
 WHERE b.tenant_id=NEW.tenant_id AND b.plan_id=NEW.plan_id AND p.analysis_id=NEW.analysis_id
 AND (convert_from(b.canonical_payload,'UTF8')::jsonb->'candidate_ids') ? NEW.candidate_id::text;
 IF NOT FOUND THEN RAISE check_violation USING MESSAGE='selection not in bound payload'; END IF;
 RETURN NEW;
END $$;
CREATE TRIGGER selected_scope BEFORE INSERT ON plan_candidate FOR EACH ROW EXECUTE FUNCTION selection_scope();

-- Bytes are verified by object publication before inserting this immutable record.
-- This FK pins validation/export to the exact publication identity, not caller summaries.
CREATE TABLE artifact_set(tenant_id uuid NOT NULL,run_id uuid NOT NULL,artifact_digest digest NOT NULL,
 PRIMARY KEY(tenant_id,run_id),UNIQUE(tenant_id,run_id,artifact_digest),FOREIGN KEY(tenant_id,run_id) REFERENCES run);
CREATE TRIGGER frozen_artifacts BEFORE UPDATE OR DELETE ON artifact_set FOR EACH ROW EXECUTE FUNCTION frozen_record();
CREATE TABLE validation(tenant_id uuid NOT NULL,id uuid NOT NULL,run_id uuid NOT NULL,artifact_digest digest NOT NULL,
 policy_id uuid NOT NULL,policy_version integer NOT NULL,
 status text NOT NULL DEFAULT 'queued' CHECK(status IN ('queued','running','completed','failed','cancelled')),
 completed_at timestamptz,PRIMARY KEY(tenant_id,id),
 CHECK((status IN ('completed','failed','cancelled'))=(completed_at IS NOT NULL)),
 FOREIGN KEY(tenant_id,run_id,artifact_digest) REFERENCES artifact_set(tenant_id,run_id,artifact_digest),
 FOREIGN KEY(tenant_id,policy_id,policy_version) REFERENCES validation_policy);
CREATE FUNCTION validation_scope() RETURNS trigger LANGUAGE plpgsql SET search_path=studio_admission,pg_catalog AS $$
BEGIN
 IF TG_OP='UPDATE' THEN
  IF OLD.status IN ('completed','failed','cancelled') OR
  (to_jsonb(OLD)-'status'-'completed_at') IS DISTINCT FROM (to_jsonb(NEW)-'status'-'completed_at') THEN
   RAISE check_violation USING MESSAGE='validation binding immutable'; END IF;
 END IF;
 PERFORM 1 FROM run r JOIN plan_binding b ON b.tenant_id=r.tenant_id AND b.plan_id=r.plan_id
 WHERE r.tenant_id=NEW.tenant_id AND r.id=NEW.run_id AND r.status='succeeded'
 AND b.policy_id=NEW.policy_id AND b.policy_version=NEW.policy_version;
 IF NOT FOUND THEN RAISE check_violation USING MESSAGE='generation or policy mismatch'; END IF;
 RETURN NEW;
END $$;
CREATE TRIGGER check_validation_scope BEFORE INSERT OR UPDATE ON validation FOR EACH ROW EXECUTE FUNCTION validation_scope();
CREATE TRIGGER retain_validation BEFORE DELETE ON validation FOR EACH ROW EXECUTE FUNCTION frozen_record();
CREATE TABLE validation_check(tenant_id uuid NOT NULL,validation_id uuid NOT NULL,name text NOT NULL,
 status text NOT NULL CHECK(status IN ('passed','failed','skipped','not_run')),
 command text,tool_version text,exit_code integer,started_at timestamptz,completed_at timestamptz,log_reference text,reason text,
 PRIMARY KEY(tenant_id,validation_id,name),FOREIGN KEY(tenant_id,validation_id) REFERENCES validation,
 CHECK((status IN ('passed','failed') AND length(trim(command))>0 AND command IS NOT NULL
 AND length(trim(tool_version))>0 AND tool_version IS NOT NULL AND exit_code IS NOT NULL
 AND started_at IS NOT NULL AND completed_at IS NOT NULL AND completed_at>=started_at
 AND log_reference IS NOT NULL AND length(trim(log_reference))>0 AND (status<>'passed' OR exit_code=0)
 AND (status<>'failed' OR (reason IS NOT NULL AND length(trim(reason))>0)))
 OR (status IN ('skipped','not_run') AND reason IS NOT NULL AND length(trim(reason))>0
 AND command IS NULL AND tool_version IS NULL AND exit_code IS NULL AND started_at IS NULL AND completed_at IS NULL AND log_reference IS NULL)));
CREATE FUNCTION lock_check_parent() RETURNS trigger LANGUAGE plpgsql SET search_path=studio_admission,pg_catalog AS $$
DECLARE state text;
BEGIN
 SELECT status INTO state FROM validation WHERE tenant_id=NEW.tenant_id AND id=NEW.validation_id FOR UPDATE;
 IF state IS DISTINCT FROM 'queued' AND state IS DISTINCT FROM 'running' THEN
 RAISE check_violation USING MESSAGE='validation checks finalized'; END IF;
 IF TG_OP='UPDATE' AND (OLD.tenant_id,OLD.validation_id,OLD.name) IS DISTINCT FROM (NEW.tenant_id,NEW.validation_id,NEW.name) THEN
 RAISE check_violation USING MESSAGE='check identity immutable'; END IF;
 RETURN NEW;
END $$;
CREATE TRIGGER guarded_check BEFORE INSERT OR UPDATE ON validation_check FOR EACH ROW EXECUTE FUNCTION lock_check_parent();
CREATE TRIGGER retain_check BEFORE DELETE ON validation_check FOR EACH ROW EXECUTE FUNCTION frozen_record();
CREATE FUNCTION seed_checks() RETURNS trigger LANGUAGE plpgsql SET search_path=studio_admission,pg_catalog AS $$
BEGIN
 INSERT INTO validation_check(tenant_id,validation_id,name,status,reason)
 SELECT NEW.tenant_id,NEW.id,unnest(required_checks),'not_run','queued; execution not yet recorded'
 FROM validation_policy WHERE tenant_id=NEW.tenant_id AND id=NEW.policy_id AND version=NEW.policy_version;
 RETURN NEW;
END $$;
CREATE TRIGGER initialize_checks AFTER INSERT ON validation FOR EACH ROW EXECUTE FUNCTION seed_checks();

CREATE TABLE export_record(tenant_id uuid NOT NULL,id uuid NOT NULL,validation_id uuid NOT NULL,actor_id uuid NOT NULL REFERENCES actor,
 artifact_digest digest NOT NULL,classification text NOT NULL CHECK(classification='APPROVED'),created_at timestamptz NOT NULL DEFAULT clock_timestamp(),
 PRIMARY KEY(tenant_id,id),FOREIGN KEY(tenant_id,validation_id) REFERENCES validation);
CREATE FUNCTION approve_export() RETURNS trigger LANGUAGE plpgsql SET search_path=studio_admission,pg_catalog AS $$
DECLARE v validation; r run; p plan; ap approval; required text[];
BEGIN
 SELECT * INTO v FROM validation WHERE tenant_id=NEW.tenant_id AND id=NEW.validation_id;
 SELECT * INTO r FROM run WHERE tenant_id=v.tenant_id AND id=v.run_id;
 -- Same parent-first order as admission/plan publication.
 PERFORM 1 FROM analysis WHERE tenant_id=r.tenant_id AND id=(SELECT analysis_id FROM plan WHERE tenant_id=r.tenant_id AND id=r.plan_id) FOR UPDATE;
 SELECT * INTO p FROM plan WHERE tenant_id=r.tenant_id AND id=r.plan_id FOR UPDATE;
 SELECT * INTO ap FROM approval WHERE tenant_id=r.tenant_id AND id=r.approval_id FOR UPDATE;
 PERFORM 1 FROM membership WHERE tenant_id=NEW.tenant_id AND actor_id=NEW.actor_id AND active FOR SHARE;
 IF NOT FOUND THEN RAISE check_violation USING MESSAGE='export actor lacks rights'; END IF;
 SELECT * INTO r FROM run WHERE tenant_id=v.tenant_id AND id=v.run_id FOR UPDATE;
 SELECT * INTO v FROM validation WHERE tenant_id=NEW.tenant_id AND id=NEW.validation_id FOR UPDATE;
 SELECT required_checks INTO required FROM validation_policy WHERE tenant_id=v.tenant_id AND id=v.policy_id AND version=v.policy_version;
 IF v.id IS NULL OR r.id IS NULL OR p.id IS NULL OR ap.id IS NULL OR NOT p.current
 OR ap.revoked_at IS NOT NULL OR ap.plan_id<>p.id OR ap.plan_hash<>p.plan_hash
 OR ap.actor_id<>NEW.actor_id OR r.actor_id<>NEW.actor_id OR r.status<>'succeeded'
 OR v.status<>'completed' OR v.artifact_digest IS DISTINCT FROM NEW.artifact_digest
 OR required IS NULL OR cardinality(required)=0
 OR EXISTS(SELECT 1 FROM unnest(required) n WHERE NOT EXISTS(SELECT 1 FROM validation_check c
 WHERE c.tenant_id=v.tenant_id AND c.validation_id=v.id AND c.name=n AND c.status='passed')) THEN
 RAISE check_violation USING MESSAGE='approved export gate denied'; END IF;
 RETURN NEW;
END $$;
CREATE TRIGGER gated_export BEFORE INSERT ON export_record FOR EACH ROW EXECUTE FUNCTION approve_export();
CREATE TRIGGER frozen_export BEFORE UPDATE OR DELETE ON export_record FOR EACH ROW EXECUTE FUNCTION frozen_record();
CREATE TABLE audit_event(tenant_id uuid NOT NULL REFERENCES tenant,id bigint GENERATED ALWAYS AS IDENTITY,
 entity text NOT NULL,entity_key jsonb NOT NULL,event_type text NOT NULL,recorded_at timestamptz NOT NULL DEFAULT clock_timestamp(),
 PRIMARY KEY(tenant_id,id));
CREATE TRIGGER frozen_audit BEFORE UPDATE OR DELETE ON audit_event FOR EACH ROW EXECUTE FUNCTION frozen_record();
CREATE TRIGGER no_truncate_audit BEFORE TRUNCATE ON audit_event FOR EACH STATEMENT EXECUTE FUNCTION frozen_record();
CREATE FUNCTION record_audit() RETURNS trigger LANGUAGE plpgsql SET search_path=studio_admission,pg_catalog AS $$
BEGIN
 INSERT INTO audit_event(tenant_id,entity,entity_key,event_type)
 VALUES(NEW.tenant_id,TG_TABLE_NAME,jsonb_build_object('id',to_jsonb(NEW)->'id','plan_id',to_jsonb(NEW)->'plan_id'),TG_OP);
 RETURN NEW;
END $$;
CREATE TRIGGER audit_bound AFTER INSERT ON plan_binding FOR EACH ROW EXECUTE FUNCTION record_audit();
CREATE TRIGGER audit_run AFTER INSERT OR UPDATE ON run FOR EACH ROW EXECUTE FUNCTION record_audit();
CREATE TRIGGER audit_approval AFTER INSERT OR UPDATE ON approval FOR EACH ROW EXECUTE FUNCTION record_audit();
CREATE TRIGGER audit_validation AFTER INSERT OR UPDATE ON validation FOR EACH ROW EXECUTE FUNCTION record_audit();
CREATE TRIGGER audit_export AFTER INSERT ON export_record FOR EACH ROW EXECUTE FUNCTION record_audit();
REVOKE ALL ON ALL TABLES IN SCHEMA studio_admission FROM PUBLIC;
REVOKE ALL ON ALL FUNCTIONS IN SCHEMA studio_admission FROM PUBLIC;
REVOKE ALL ON ALL SEQUENCES IN SCHEMA studio_admission FROM PUBLIC;
COMMIT;
