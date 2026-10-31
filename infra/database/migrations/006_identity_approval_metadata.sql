BEGIN;
SET LOCAL ROLE studio_kernel_owner;
SET LOCAL search_path=studio_admission,pg_catalog,pg_temp;
-- UUIDs become the externally stable audit identity; retain the old ordinal for ordering.
ALTER TABLE audit_event RENAME COLUMN id TO sequence_no;
ALTER TABLE audit_event ADD COLUMN id uuid NOT NULL DEFAULT gen_random_uuid(),
 ADD COLUMN actor_id uuid REFERENCES actor,
 ADD COLUMN resource_id text GENERATED ALWAYS AS
 (coalesce(entity_key->>'id',entity_key->>'plan_id',entity_key->>'run_id')) STORED NOT NULL;
ALTER TABLE audit_event DROP CONSTRAINT audit_event_pkey,
 ADD PRIMARY KEY(tenant_id,id),ADD UNIQUE(tenant_id,sequence_no);
CREATE OR REPLACE FUNCTION record_audit() RETURNS trigger LANGUAGE plpgsql SET search_path=pg_catalog,studio_admission,pg_temp AS $$
DECLARE caller uuid;
BEGIN
 SELECT p.actor_id INTO caller FROM runtime_principal p WHERE p.login_name=session_user AND p.tenant_id=NEW.tenant_id AND p.enabled;
 INSERT INTO audit_event(tenant_id,actor_id,entity,entity_key,event_type)
 VALUES(NEW.tenant_id,caller,TG_TABLE_NAME,
 jsonb_build_object('id',to_jsonb(NEW)->'id','plan_id',to_jsonb(NEW)->'plan_id','run_id',to_jsonb(NEW)->'run_id'),TG_OP);
 RETURN NEW;
END $$;
ALTER TABLE validation_check ADD COLUMN id uuid NOT NULL DEFAULT gen_random_uuid(),ADD UNIQUE(tenant_id,id);
CREATE OR REPLACE FUNCTION lock_check_parent() RETURNS trigger LANGUAGE plpgsql SET search_path=pg_catalog,studio_admission,pg_temp AS $$
DECLARE state text;
BEGIN
 SELECT status INTO state FROM validation WHERE tenant_id=NEW.tenant_id AND id=NEW.validation_id FOR UPDATE;
 IF state IS DISTINCT FROM 'queued' AND state IS DISTINCT FROM 'running' THEN
 RAISE check_violation USING MESSAGE='validation checks finalized'; END IF;
 IF TG_OP='UPDATE' AND (OLD.tenant_id,OLD.validation_id,OLD.name,OLD.id) IS DISTINCT FROM (NEW.tenant_id,NEW.validation_id,NEW.name,NEW.id) THEN
 RAISE check_violation USING MESSAGE='check identity immutable'; END IF;
 RETURN NEW;
END $$;
CREATE VIEW validation_check_contract AS
 SELECT c.id,c.tenant_id,c.validation_id AS validation_run_id,c.name,c.name=ANY(p.required_checks) AS mandatory,
 c.status,c.command,c.tool_version,c.exit_code,c.started_at,c.completed_at,c.log_reference,c.reason,
 coalesce((SELECT jsonb_agg(f.stable_key ORDER BY f.stable_key COLLATE "C") FROM validation_check_finding l
 JOIN finding f ON f.tenant_id=l.tenant_id AND f.id=l.finding_id
 WHERE l.tenant_id=c.tenant_id AND l.validation_id=c.validation_id AND l.name=c.name),'[]'::jsonb) AS finding_ids
 FROM validation_check c JOIN validation v ON v.tenant_id=c.tenant_id AND v.id=c.validation_id
 JOIN validation_policy p ON p.tenant_id=v.tenant_id AND p.id=v.policy_id AND p.version=v.policy_version;

ALTER TABLE approval ADD COLUMN approved_at timestamptz NOT NULL DEFAULT clock_timestamp(),
 ADD COLUMN plan_version integer NOT NULL CHECK(plan_version>0),
 ADD COLUMN security_confirmed boolean NOT NULL CHECK(security_confirmed);
CREATE FUNCTION verify_approval_identity() RETURNS trigger LANGUAGE plpgsql SET search_path=pg_catalog,studio_admission,pg_temp AS $$
DECLARE p plan;
BEGIN
 PERFORM lock_live_plan(NEW.tenant_id,NEW.plan_id);
 SELECT * INTO p FROM plan WHERE tenant_id=NEW.tenant_id AND id=NEW.plan_id;
 PERFORM 1 FROM membership WHERE tenant_id=NEW.tenant_id AND actor_id=NEW.actor_id AND active FOR SHARE;
 IF NOT FOUND OR p.id IS NULL OR NOT p.current OR NEW.plan_version IS DISTINCT FROM p.version
 OR NEW.plan_hash IS DISTINCT FROM p.plan_hash OR NEW.security_confirmed IS DISTINCT FROM true
 OR NEW.revoked_at IS NOT NULL OR NOT EXISTS(SELECT 1 FROM plan_binding WHERE tenant_id=p.tenant_id AND plan_id=p.id) THEN
 RAISE check_violation USING MESSAGE='approval requires exact reviewed plan version/hash and confirmation'; END IF;
 RETURN NEW;
END $$;
CREATE TRIGGER verified_approval BEFORE INSERT ON approval FOR EACH ROW EXECUTE FUNCTION verify_approval_identity();
CREATE FUNCTION backend_approve_plan(p_plan uuid,p_version integer,p_hash text,p_security boolean) RETURNS uuid
LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog,studio_admission,pg_temp AS $$
DECLARE p runtime_principal; i uuid;
BEGIN
 p=runtime_identity('backend');i=gen_random_uuid();
 INSERT INTO approval(tenant_id,id,plan_id,actor_id,plan_hash,plan_version,security_confirmed)
 VALUES(p.tenant_id,i,p_plan,p.actor_id,p_hash::digest,p_version,p_security);
 RETURN i;
END $$;
ALTER TABLE run ADD COLUMN created_at timestamptz NOT NULL DEFAULT clock_timestamp(),
 ADD COLUMN plan_hash digest NOT NULL,ADD COLUMN previous_run_id uuid,
 ADD CHECK(previous_run_id IS NULL OR previous_run_id<>id),
 ADD UNIQUE(tenant_id,plan_id,actor_id,id),
 ADD FOREIGN KEY(tenant_id,plan_id,actor_id,previous_run_id) REFERENCES run(tenant_id,plan_id,actor_id,id);
CREATE FUNCTION bind_run_hash() RETURNS trigger LANGUAGE plpgsql SET search_path=pg_catalog,studio_admission,pg_temp AS $$
DECLARE h digest;
BEGIN
 SELECT plan_hash INTO h FROM plan WHERE tenant_id=NEW.tenant_id AND id=NEW.plan_id;
 IF NEW.plan_hash IS NOT NULL AND NEW.plan_hash IS DISTINCT FROM h THEN
 RAISE check_violation USING MESSAGE='generation plan hash mismatch'; END IF;
 NEW.plan_hash=h;RETURN NEW;
END $$;
CREATE TRIGGER bind_generation_hash BEFORE INSERT ON run FOR EACH ROW EXECUTE FUNCTION bind_run_hash();
ALTER TABLE validation ADD COLUMN created_at timestamptz NOT NULL DEFAULT clock_timestamp(),
 ADD COLUMN previous_run_id uuid,ADD UNIQUE(tenant_id,run_id,id),
 ADD CHECK(previous_run_id IS NULL OR previous_run_id<>id),
 ADD FOREIGN KEY(tenant_id,run_id,previous_run_id) REFERENCES validation(tenant_id,run_id,id);
ALTER TABLE idempotency ADD COLUMN id uuid NOT NULL DEFAULT gen_random_uuid(),ADD UNIQUE(tenant_id,id),
 ADD COLUMN status text NOT NULL DEFAULT 'admitted' CHECK(status='admitted'),
 ADD COLUMN response jsonb NOT NULL,ADD COLUMN created_at timestamptz NOT NULL DEFAULT clock_timestamp();
CREATE FUNCTION bind_idempotent_outcome() RETURNS trigger LANGUAGE plpgsql SET search_path=pg_catalog,studio_admission,pg_temp AS $$
DECLARE r run; expected jsonb;
BEGIN
 SELECT * INTO r FROM run WHERE tenant_id=NEW.tenant_id AND id=NEW.run_id AND actor_id=NEW.actor_id;
 expected=jsonb_build_object('id',r.id,'status',r.status);
 IF r.id IS NULL OR NEW.operation<>'generate' OR NEW.request_digest IS DISTINCT FROM r.request_digest
 OR (NEW.response IS NOT NULL AND NEW.response IS DISTINCT FROM expected) THEN
 RAISE check_violation USING MESSAGE='idempotent admission outcome mismatch'; END IF;
 NEW.response=expected;RETURN NEW;
END $$;
CREATE TRIGGER verified_outcome BEFORE INSERT ON idempotency FOR EACH ROW EXECUTE FUNCTION bind_idempotent_outcome();
CREATE TRIGGER frozen_outcome BEFORE UPDATE OR DELETE ON idempotency FOR EACH ROW EXECUTE FUNCTION frozen_record();
ALTER TABLE outbox ADD COLUMN payload jsonb NOT NULL,ADD COLUMN created_at timestamptz NOT NULL DEFAULT clock_timestamp(),
 ADD COLUMN dispatched_at timestamptz,ADD COLUMN delivery_attempts integer NOT NULL DEFAULT 0 CHECK(delivery_attempts>=0),
 ADD CHECK(dispatched_at IS NULL OR delivery_attempts>0);
CREATE FUNCTION bind_outbox_payload() RETURNS trigger LANGUAGE plpgsql SET search_path=pg_catalog,studio_admission,pg_temp AS $$
DECLARE r run; expected jsonb;
BEGIN
 SELECT * INTO r FROM run WHERE tenant_id=NEW.tenant_id AND id=NEW.run_id;
 expected=jsonb_build_object('run_id',r.id,'plan_id',r.plan_id,'actor_id',r.actor_id,'request_digest',r.request_digest);
 IF r.id IS NULL OR NEW.event_type<>'generation.admitted' OR (NEW.payload IS NOT NULL AND NEW.payload IS DISTINCT FROM expected) THEN
 RAISE check_violation USING MESSAGE='outbox payload mismatch'; END IF;
 NEW.payload=expected;RETURN NEW;
END $$;
CREATE TRIGGER verified_outbox BEFORE INSERT ON outbox FOR EACH ROW EXECUTE FUNCTION bind_outbox_payload();
CREATE FUNCTION retain_outbox_identity() RETURNS trigger LANGUAGE plpgsql SET search_path=pg_catalog,studio_admission,pg_temp AS $$
BEGIN
 IF (to_jsonb(OLD)-'delivery_attempts'-'dispatched_at') IS DISTINCT FROM (to_jsonb(NEW)-'delivery_attempts'-'dispatched_at')
 OR NEW.delivery_attempts<OLD.delivery_attempts OR (OLD.dispatched_at IS NOT NULL AND NEW.dispatched_at IS DISTINCT FROM OLD.dispatched_at) THEN
 RAISE check_violation USING MESSAGE='outbox identity or delivery history immutable'; END IF;
 RETURN NEW;
END $$;
CREATE TRIGGER guarded_outbox BEFORE UPDATE ON outbox FOR EACH ROW EXECUTE FUNCTION retain_outbox_identity();
CREATE TRIGGER retained_outbox BEFORE DELETE ON outbox FOR EACH ROW EXECUTE FUNCTION frozen_record();
CREATE FUNCTION backend_validation_checks(p_validation uuid) RETURNS jsonb LANGUAGE plpgsql SECURITY DEFINER
SET search_path=pg_catalog,studio_admission,pg_temp AS $$
DECLARE p runtime_principal; output jsonb;
BEGIN
 p=runtime_identity('backend');
 PERFORM 1 FROM validation v JOIN run r ON r.tenant_id=v.tenant_id AND r.id=v.run_id
 WHERE v.tenant_id=p.tenant_id AND v.id=p_validation AND r.actor_id=p.actor_id;
 IF NOT FOUND THEN RAISE insufficient_privilege USING MESSAGE='resource unavailable'; END IF;
 SELECT coalesce(jsonb_agg(jsonb_strip_nulls(to_jsonb(c)-'tenant_id'-'id'-'validation_run_id') ORDER BY c.name COLLATE "C"),'[]'::jsonb) INTO output
 FROM validation_check_contract c WHERE c.tenant_id=p.tenant_id AND c.validation_run_id=p_validation;
 RETURN output;
END $$;
GRANT EXECUTE ON FUNCTION backend_approve_plan(uuid,integer,text,boolean),backend_validation_checks(uuid) TO studio_backend;
REVOKE ALL ON ALL TABLES IN SCHEMA studio_admission FROM PUBLIC,studio_backend,studio_worker;
COMMIT;
