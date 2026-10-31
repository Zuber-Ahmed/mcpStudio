BEGIN;
SET LOCAL ROLE studio_kernel_owner;
SET LOCAL search_path=studio_admission,pg_catalog,pg_temp;
ALTER TABLE tenant ADD COLUMN name text NOT NULL CHECK(length(trim(name))>0);
ALTER TABLE actor ADD COLUMN subject text NOT NULL CHECK(length(trim(subject))>0),ADD UNIQUE(subject);
CREATE TRIGGER frozen_actor_identity BEFORE UPDATE OR DELETE ON actor FOR EACH ROW EXECUTE FUNCTION frozen_record();
-- The approved initial topology has one local operator, not enterprise role administration.
ALTER TABLE membership ADD COLUMN role text NOT NULL CHECK(role='operator');
ALTER TABLE candidate ADD UNIQUE(tenant_id,id);
CREATE FUNCTION source_metadata_valid(v jsonb) RETURNS boolean LANGUAGE sql IMMUTABLE SET search_path=pg_catalog AS $$
 SELECT CASE WHEN jsonb_typeof(v)='object' THEN coalesce(
 jsonb_typeof(v->'kind')='string' AND v->>'kind' IN ('local','git')
 AND jsonb_typeof(v->'location')='string' AND length(trim(v->>'location'))>0
 AND NOT EXISTS(SELECT 1 FROM jsonb_object_keys(v) k WHERE k NOT IN ('kind','location','revision','credential_reference'))
 AND (NOT (v ? 'revision') OR (jsonb_typeof(v->'revision')='string' AND length(trim(v->>'revision'))>0))
 AND (NOT (v ? 'credential_reference') OR (jsonb_typeof(v->'credential_reference')='string' AND length(trim(v->>'credential_reference'))>0))
 AND (v->>'kind'<>'git' OR v ? 'revision')
 AND (v->>'location') !~* '^[a-z][a-z0-9+.-]*://[^/]*@'
 AND (v->>'location') !~* '[?&](access_token|token|password|secret|authorization)=',false) ELSE false END
$$;
ALTER TABLE project ADD COLUMN name text NOT NULL CHECK(length(trim(name)) BETWEEN 1 AND 200),
 ADD COLUMN source jsonb NOT NULL CHECK(source_metadata_valid(source)),
 ADD COLUMN created_at timestamptz NOT NULL DEFAULT statement_timestamp(),
 ADD COLUMN updated_at timestamptz NOT NULL DEFAULT statement_timestamp(),ADD CHECK(updated_at>=created_at);
CREATE FUNCTION retain_project_identity() RETURNS trigger LANGUAGE plpgsql SET search_path=pg_catalog,studio_admission,pg_temp AS $$
BEGIN
 IF (OLD.tenant_id,OLD.id,OLD.source,OLD.created_at) IS DISTINCT FROM (NEW.tenant_id,NEW.id,NEW.source,NEW.created_at) THEN
 RAISE check_violation USING MESSAGE='project identity/source immutable; acquire a new explicitly scoped project'; END IF;
 NEW.updated_at=greatest(clock_timestamp(),OLD.updated_at);RETURN NEW;
END $$;
CREATE TRIGGER guarded_project_metadata BEFORE UPDATE ON project FOR EACH ROW EXECUTE FUNCTION retain_project_identity();
CREATE TRIGGER audit_project AFTER INSERT OR UPDATE ON project FOR EACH ROW EXECUTE FUNCTION record_audit();
CREATE OR REPLACE FUNCTION runtime_identity(kind text) RETURNS runtime_principal LANGUAGE plpgsql SECURITY DEFINER
SET search_path=pg_catalog,studio_admission,pg_temp AS $$
DECLARE p runtime_principal;
BEGIN
 SELECT * INTO p FROM runtime_principal WHERE login_name=session_user AND enabled AND capability=kind FOR SHARE;
 IF p.login_name IS NULL THEN RAISE insufficient_privilege USING MESSAGE='runtime identity unavailable'; END IF;
 PERFORM 1 FROM membership WHERE tenant_id=p.tenant_id AND actor_id=p.actor_id AND active AND role='operator' FOR SHARE;
 IF NOT FOUND THEN RAISE insufficient_privilege USING MESSAGE='operator rights unavailable'; END IF;
 RETURN p;
END $$;
-- Foundation metadata read only: does not pretend to implement Project workflow projections.
CREATE FUNCTION backend_project_metadata(p_project uuid) RETURNS jsonb LANGUAGE plpgsql SECURITY DEFINER
SET search_path=pg_catalog,studio_admission,pg_temp AS $$
DECLARE ident runtime_principal; p project;
BEGIN
 ident=runtime_identity('backend');SELECT * INTO p FROM project WHERE tenant_id=ident.tenant_id AND id=p_project;
 IF p.id IS NULL THEN RAISE insufficient_privilege USING MESSAGE='project unavailable'; END IF;
 RETURN jsonb_build_object('id',p.id,'name',p.name,'source',p.source,'created_at',p.created_at,'updated_at',p.updated_at);
END $$;
GRANT EXECUTE ON FUNCTION backend_project_metadata(uuid) TO studio_backend;
REVOKE ALL ON ALL TABLES IN SCHEMA studio_admission FROM PUBLIC,studio_backend,studio_worker;
COMMIT;
