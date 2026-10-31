BEGIN;
SET LOCAL ROLE studio_kernel_owner;
SET LOCAL search_path=studio_admission,pg_catalog,pg_temp;
CREATE FUNCTION portable_artifact_path(p text) RETURNS boolean LANGUAGE sql IMMUTABLE
SET search_path=pg_catalog,studio_admission,pg_temp AS $$
 SELECT length(p) BETWEEN 1 AND 240 AND p ~ '^[-A-Za-z0-9_.@()+/]+$'
 AND NOT EXISTS(SELECT 1 FROM unnest(string_to_array(p,'/')) s
 WHERE s IN ('','.','..') OR s ~ '[. ]$' OR s ~* '^(con|prn|aux|nul|com[1-9]|lpt[1-9])([.]|$)')
$$;
CREATE TABLE artifact(tenant_id uuid NOT NULL,id uuid NOT NULL,generation_run_id uuid NOT NULL,
 path text NOT NULL CHECK(portable_artifact_path(path)),storage_key text NOT NULL CHECK(length(trim(storage_key))>0),
 sha256 digest NOT NULL,media_type text NOT NULL CHECK(length(trim(media_type))>0),size_bytes bigint NOT NULL CHECK(size_bytes>=0),
 path_folded text GENERATED ALWAYS AS (lower(path COLLATE "C")) STORED,
 PRIMARY KEY(tenant_id,id),UNIQUE(tenant_id,generation_run_id,path_folded),
 FOREIGN KEY(tenant_id,generation_run_id) REFERENCES run);
CREATE FUNCTION artifact_open_run() RETURNS trigger LANGUAGE plpgsql SET search_path=pg_catalog,studio_admission,pg_temp AS $$
DECLARE state text;
BEGIN
 SELECT status INTO state FROM run WHERE tenant_id=NEW.tenant_id AND id=NEW.generation_run_id FOR UPDATE;
 IF state IS DISTINCT FROM 'queued' AND state IS DISTINCT FROM 'running' THEN
 RAISE check_violation USING MESSAGE='artifact run unavailable or finalized'; END IF;
 RETURN NEW;
END $$;
CREATE TRIGGER open_artifact BEFORE INSERT ON artifact FOR EACH ROW EXECUTE FUNCTION artifact_open_run();
CREATE TRIGGER frozen_artifact BEFORE UPDATE OR DELETE ON artifact FOR EACH ROW EXECUTE FUNCTION frozen_record();
ALTER TABLE artifact_set ADD COLUMN canonical_manifest bytea NOT NULL;
CREATE FUNCTION manifest_matches_artifacts() RETURNS trigger LANGUAGE plpgsql SET search_path=pg_catalog,studio_admission,pg_temp AS $$
DECLARE expected jsonb; state text;
BEGIN
 SELECT status INTO state FROM run WHERE tenant_id=NEW.tenant_id AND id=NEW.run_id FOR UPDATE;
 SELECT jsonb_agg(jsonb_build_object('path',path,'sha256',sha256,'size_bytes',size_bytes) ORDER BY path COLLATE "C")
 INTO expected FROM artifact WHERE tenant_id=NEW.tenant_id AND generation_run_id=NEW.run_id;
 IF state IS DISTINCT FROM 'succeeded' OR expected IS NULL
 OR convert_from(NEW.canonical_manifest,'UTF8')::jsonb IS DISTINCT FROM expected
 OR encode(sha256(NEW.canonical_manifest),'hex') IS DISTINCT FROM NEW.artifact_digest::text THEN
 RAISE check_violation USING MESSAGE='artifact manifest does not match finalized records'; END IF;
 RETURN NEW;
END $$;
CREATE TRIGGER verified_manifest BEFORE INSERT ON artifact_set FOR EACH ROW EXECUTE FUNCTION manifest_matches_artifacts();

CREATE TABLE finding(tenant_id uuid NOT NULL,id uuid NOT NULL,generation_run_id uuid NOT NULL,
 stable_key text NOT NULL CHECK(length(trim(stable_key))>0),severity text NOT NULL CHECK(severity IN ('info','warning','blocking')),
 code text NOT NULL CHECK(length(trim(code))>0),message text NOT NULL CHECK(length(trim(message))>0),
 evidence jsonb NOT NULL CHECK(jsonb_typeof(evidence)='array'),
 PRIMARY KEY(tenant_id,id),UNIQUE(tenant_id,generation_run_id,stable_key),UNIQUE(tenant_id,generation_run_id,id),
 FOREIGN KEY(tenant_id,generation_run_id) REFERENCES run);
CREATE TRIGGER frozen_finding BEFORE UPDATE OR DELETE ON finding FOR EACH ROW EXECUTE FUNCTION frozen_record();
ALTER TABLE validation ADD CONSTRAINT validation_run_identity UNIQUE(tenant_id,id,run_id);
CREATE TABLE validation_check_finding(tenant_id uuid NOT NULL,validation_id uuid NOT NULL,name text NOT NULL,
 generation_run_id uuid NOT NULL,finding_id uuid NOT NULL,
 PRIMARY KEY(tenant_id,validation_id,name,finding_id),
 FOREIGN KEY(tenant_id,validation_id,name) REFERENCES validation_check,
 FOREIGN KEY(tenant_id,validation_id,generation_run_id) REFERENCES validation(tenant_id,id,run_id),
 FOREIGN KEY(tenant_id,generation_run_id,finding_id) REFERENCES finding(tenant_id,generation_run_id,id));
CREATE TRIGGER frozen_finding_link BEFORE UPDATE OR DELETE ON validation_check_finding FOR EACH ROW EXECUTE FUNCTION frozen_record();
CREATE FUNCTION finding_link_open() RETURNS trigger LANGUAGE plpgsql SET search_path=pg_catalog,studio_admission,pg_temp AS $$
DECLARE state text;
BEGIN
 SELECT status INTO state FROM validation WHERE tenant_id=NEW.tenant_id AND id=NEW.validation_id FOR UPDATE;
 IF state IS DISTINCT FROM 'queued' AND state IS DISTINCT FROM 'running' THEN
 RAISE check_violation USING MESSAGE='validation findings finalized'; END IF;
 RETURN NEW;
END $$;
CREATE TRIGGER open_finding_link BEFORE INSERT ON validation_check_finding FOR EACH ROW EXECUTE FUNCTION finding_link_open();

CREATE TABLE plan_revocation(tenant_id uuid NOT NULL,id uuid NOT NULL,plan_id uuid NOT NULL,actor_id uuid NOT NULL REFERENCES actor,
 reason text NOT NULL CHECK(length(trim(reason))>0),revoked_at timestamptz NOT NULL DEFAULT clock_timestamp(),
 PRIMARY KEY(tenant_id,id),FOREIGN KEY(tenant_id,plan_id) REFERENCES plan);
CREATE FUNCTION serialize_revocation() RETURNS trigger LANGUAGE plpgsql SET search_path=pg_catalog,studio_admission,pg_temp AS $$
BEGIN
 PERFORM 1 FROM analysis a JOIN plan p ON p.tenant_id=a.tenant_id AND p.analysis_id=a.id
 WHERE p.tenant_id=NEW.tenant_id AND p.id=NEW.plan_id FOR UPDATE OF a;
 IF NOT FOUND THEN RAISE insufficient_privilege USING MESSAGE='plan unavailable'; END IF;
 PERFORM 1 FROM plan WHERE tenant_id=NEW.tenant_id AND id=NEW.plan_id FOR UPDATE;
 PERFORM 1 FROM membership WHERE tenant_id=NEW.tenant_id AND actor_id=NEW.actor_id AND active FOR SHARE;
 IF NOT FOUND THEN RAISE insufficient_privilege USING MESSAGE='revocation actor lacks rights'; END IF;
 RETURN NEW;
END $$;
CREATE TRIGGER serialized_revocation BEFORE INSERT ON plan_revocation FOR EACH ROW EXECUTE FUNCTION serialize_revocation();
CREATE TRIGGER frozen_revocation BEFORE UPDATE OR DELETE ON plan_revocation FOR EACH ROW EXECUTE FUNCTION frozen_record();
CREATE FUNCTION lock_live_plan(t uuid,p uuid) RETURNS void LANGUAGE plpgsql SET search_path=pg_catalog,studio_admission,pg_temp AS $$
BEGIN
 PERFORM 1 FROM analysis a JOIN plan q ON q.tenant_id=a.tenant_id AND q.analysis_id=a.id WHERE q.tenant_id=t AND q.id=p FOR UPDATE OF a;
 PERFORM 1 FROM plan WHERE tenant_id=t AND id=p FOR UPDATE;
 IF EXISTS(SELECT 1 FROM plan_revocation WHERE tenant_id=t AND plan_id=p) THEN
 RAISE check_violation USING MESSAGE='plan explicitly revoked'; END IF;
END $$;
ALTER FUNCTION admit(uuid,uuid,uuid,uuid,text,digest,uuid,text,text[],text,text) RENAME TO admit_v1;
CREATE FUNCTION admit(t uuid,actor uuid,p uuid,approval uuid,k text,d digest,
 consent uuid DEFAULT NULL,provider text DEFAULT NULL,classes text[] DEFAULT NULL,redaction text DEFAULT NULL,retention text DEFAULT NULL)
RETURNS uuid LANGUAGE plpgsql SET search_path=pg_catalog,studio_admission,pg_temp AS $$
BEGIN
 PERFORM lock_live_plan(t,p);
 RETURN admit_v1(t,actor,p,approval,k,d,consent,provider,classes,redaction,retention);
END $$;
CREATE FUNCTION export_live_plan() RETURNS trigger LANGUAGE plpgsql SET search_path=pg_catalog,studio_admission,pg_temp AS $$
DECLARE p uuid;
BEGIN
 SELECT r.plan_id INTO p FROM validation v JOIN run r ON r.tenant_id=v.tenant_id AND r.id=v.run_id
 WHERE v.tenant_id=NEW.tenant_id AND v.id=NEW.validation_id;
 PERFORM lock_live_plan(NEW.tenant_id,p);
 RETURN NEW;
END $$;
CREATE TRIGGER revoked_export BEFORE INSERT ON export_record FOR EACH ROW EXECUTE FUNCTION export_live_plan();

CREATE OR REPLACE FUNCTION worker_publish(p_run uuid,p_artifact_digest text) RETURNS void LANGUAGE plpgsql SECURITY DEFINER
SET search_path=pg_catalog,studio_admission,pg_temp AS $$
BEGIN RAISE check_violation USING MESSAGE='publication requires exact manifest bytes'; END $$;
CREATE FUNCTION worker_artifact(p_run uuid,p_id uuid,p_path text,p_key text,p_sha text,p_media text,p_size bigint) RETURNS void
LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog,studio_admission,pg_temp AS $$
DECLARE p runtime_principal;
BEGIN
 p=worker_scope(p_run);
 INSERT INTO artifact(tenant_id,id,generation_run_id,path,storage_key,sha256,media_type,size_bytes)
 VALUES(p.tenant_id,p_id,p_run,p_path,p_key,p_sha::digest,p_media,p_size);
END $$;
CREATE FUNCTION worker_publish(p_run uuid,p_artifact_digest text,p_manifest bytea) RETURNS void
LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog,studio_admission,pg_temp AS $$
DECLARE p runtime_principal; pl uuid;
BEGIN
 p=worker_scope(p_run);
 SELECT plan_id INTO pl FROM run WHERE tenant_id=p.tenant_id AND id=p_run;
 PERFORM lock_live_plan(p.tenant_id,pl);
 UPDATE run SET status='succeeded',completed_at=clock_timestamp() WHERE tenant_id=p.tenant_id AND id=p_run AND status IN ('queued','running');
 IF NOT FOUND THEN RAISE check_violation USING MESSAGE='run unavailable or terminal'; END IF;
 INSERT INTO artifact_set(tenant_id,run_id,artifact_digest,canonical_manifest) VALUES(p.tenant_id,p_run,p_artifact_digest::digest,p_manifest);
END $$;
CREATE FUNCTION backend_revoke_plan(p_plan uuid,p_reason text) RETURNS uuid
LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog,studio_admission,pg_temp AS $$
DECLARE p runtime_principal; i uuid;
BEGIN
 p=runtime_identity('backend');i=gen_random_uuid();
 INSERT INTO plan_revocation(tenant_id,id,plan_id,actor_id,reason) VALUES(p.tenant_id,i,p_plan,p.actor_id,p_reason);
 RETURN i;
END $$;
CREATE TRIGGER audit_revocation AFTER INSERT ON plan_revocation FOR EACH ROW EXECUTE FUNCTION record_audit();
CREATE TRIGGER audit_artifact AFTER INSERT ON artifact FOR EACH ROW EXECUTE FUNCTION record_audit();
CREATE TRIGGER audit_finding AFTER INSERT ON finding FOR EACH ROW EXECUTE FUNCTION record_audit();
GRANT EXECUTE ON FUNCTION worker_artifact(uuid,uuid,text,text,text,text,bigint),worker_publish(uuid,text,bytea) TO studio_worker;
GRANT EXECUTE ON FUNCTION backend_revoke_plan(uuid,text) TO studio_backend;
REVOKE ALL ON ALL TABLES IN SCHEMA studio_admission FROM PUBLIC,studio_backend,studio_worker;
COMMIT;
