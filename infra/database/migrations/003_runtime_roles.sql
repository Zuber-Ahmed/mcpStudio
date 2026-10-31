-- Administrative, one-time foundation migration; creates NOLOGIN capability groups.
BEGIN;
CREATE ROLE studio_kernel_owner NOLOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOREPLICATION NOBYPASSRLS;
CREATE ROLE studio_backend NOLOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOREPLICATION NOBYPASSRLS;
CREATE ROLE studio_worker NOLOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOREPLICATION NOBYPASSRLS;
SET LOCAL search_path=pg_catalog,studio_admission,pg_temp;
CREATE TABLE studio_admission.runtime_principal(
 login_name name PRIMARY KEY,tenant_id uuid NOT NULL REFERENCES studio_admission.tenant,
 actor_id uuid NOT NULL REFERENCES studio_admission.actor,
 capability text NOT NULL CHECK(capability IN ('backend','worker')),enabled boolean NOT NULL DEFAULT true,
 FOREIGN KEY(tenant_id,actor_id) REFERENCES studio_admission.membership);
CREATE TABLE studio_admission.worker_assignment(
 login_name name NOT NULL REFERENCES studio_admission.runtime_principal,
 tenant_id uuid NOT NULL,run_id uuid NOT NULL,enabled boolean NOT NULL DEFAULT true,
 PRIMARY KEY(login_name,tenant_id,run_id),FOREIGN KEY(tenant_id,run_id) REFERENCES studio_admission.run);

CREATE FUNCTION studio_admission.runtime_identity(kind text) RETURNS studio_admission.runtime_principal
LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog,studio_admission,pg_temp AS $$
DECLARE p studio_admission.runtime_principal;
BEGIN
 SELECT * INTO p FROM studio_admission.runtime_principal WHERE login_name=session_user AND enabled AND capability=kind FOR SHARE;
 IF p.login_name IS NULL THEN RAISE insufficient_privilege USING MESSAGE='runtime identity unavailable'; END IF;
 PERFORM 1 FROM studio_admission.membership WHERE tenant_id=p.tenant_id AND actor_id=p.actor_id AND active FOR SHARE;
 IF NOT FOUND THEN RAISE insufficient_privilege USING MESSAGE='runtime rights unavailable'; END IF;
 RETURN p;
END $$;
CREATE FUNCTION studio_admission.backend_submit(p_plan uuid,p_approval uuid,p_key text,p_digest text) RETURNS uuid
LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog,studio_admission,pg_temp AS $$
DECLARE p studio_admission.runtime_principal;
BEGIN
 p=studio_admission.runtime_identity('backend');
 RETURN studio_admission.admit(p.tenant_id,p.actor_id,p_plan,p_approval,p_key,p_digest::studio_admission.digest);
END $$;
CREATE FUNCTION studio_admission.backend_run_status(p_run uuid) RETURNS text
LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog,studio_admission,pg_temp AS $$
DECLARE p studio_admission.runtime_principal; result text;
BEGIN
 p=studio_admission.runtime_identity('backend');
 SELECT status INTO result FROM studio_admission.run WHERE tenant_id=p.tenant_id AND id=p_run AND actor_id=p.actor_id;
 IF NOT FOUND THEN RAISE insufficient_privilege USING MESSAGE='resource unavailable'; END IF;
 RETURN result;
END $$;
CREATE FUNCTION studio_admission.worker_scope(p_run uuid) RETURNS studio_admission.runtime_principal
LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog,studio_admission,pg_temp AS $$
DECLARE p studio_admission.runtime_principal;
BEGIN
 p=studio_admission.runtime_identity('worker');
 PERFORM 1 FROM studio_admission.worker_assignment WHERE login_name=session_user AND tenant_id=p.tenant_id AND run_id=p_run AND enabled FOR SHARE;
 IF NOT FOUND THEN RAISE insufficient_privilege USING MESSAGE='worker assignment unavailable'; END IF;
 RETURN p;
END $$;
CREATE FUNCTION studio_admission.worker_publish(p_run uuid,p_artifact_digest text) RETURNS void
LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog,studio_admission,pg_temp AS $$
DECLARE p studio_admission.runtime_principal;
BEGIN
 p=studio_admission.worker_scope(p_run);
 UPDATE studio_admission.run SET status='succeeded',completed_at=clock_timestamp() WHERE tenant_id=p.tenant_id AND id=p_run AND status IN ('queued','running');
 IF NOT FOUND THEN RAISE check_violation USING MESSAGE='run unavailable or terminal'; END IF;
 INSERT INTO studio_admission.artifact_set VALUES(p.tenant_id,p_run,p_artifact_digest::studio_admission.digest);
END $$;
CREATE FUNCTION studio_admission.backend_validate(p_run uuid) RETURNS uuid
LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog,studio_admission,pg_temp AS $$
DECLARE p studio_admission.runtime_principal; r studio_admission.run; b studio_admission.plan_binding; d studio_admission.digest; v uuid;
BEGIN
 p=studio_admission.runtime_identity('backend');
 SELECT * INTO r FROM studio_admission.run WHERE tenant_id=p.tenant_id AND id=p_run AND actor_id=p.actor_id;
 IF NOT FOUND THEN RAISE insufficient_privilege USING MESSAGE='resource unavailable'; END IF;
 SELECT * INTO b FROM studio_admission.plan_binding WHERE tenant_id=p.tenant_id AND plan_id=r.plan_id;
 SELECT artifact_digest INTO d FROM studio_admission.artifact_set WHERE tenant_id=p.tenant_id AND run_id=p_run;
 v=gen_random_uuid();
 INSERT INTO studio_admission.validation(tenant_id,id,run_id,artifact_digest,policy_id,policy_version)
 VALUES(p.tenant_id,v,p_run,d,b.policy_id,b.policy_version);
 RETURN v;
END $$;
CREATE FUNCTION studio_admission.worker_check(p_validation uuid,p_name text,p_status text,p_command text,p_tool text,
 p_exit integer,p_started timestamptz,p_completed timestamptz,p_log text,p_reason text) RETURNS void
LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog,studio_admission,pg_temp AS $$
DECLARE ident studio_admission.runtime_principal; p studio_admission.runtime_principal; r uuid;
BEGIN
 ident=studio_admission.runtime_identity('worker');
 SELECT run_id INTO r FROM studio_admission.validation WHERE tenant_id=ident.tenant_id AND id=p_validation;
 p=studio_admission.worker_scope(r);
 UPDATE studio_admission.validation_check SET status=p_status,command=p_command,tool_version=p_tool,
 exit_code=p_exit,started_at=p_started,completed_at=p_completed,log_reference=p_log,reason=p_reason
 WHERE tenant_id=p.tenant_id AND validation_id=p_validation AND name=p_name;
 IF NOT FOUND THEN RAISE insufficient_privilege USING MESSAGE='check unavailable'; END IF;
END $$;
CREATE FUNCTION studio_admission.worker_finish_validation(p_validation uuid) RETURNS void
LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog,studio_admission,pg_temp AS $$
DECLARE ident studio_admission.runtime_principal; p studio_admission.runtime_principal; r uuid;
BEGIN
 ident=studio_admission.runtime_identity('worker');
 SELECT run_id INTO r FROM studio_admission.validation WHERE tenant_id=ident.tenant_id AND id=p_validation;
 p=studio_admission.worker_scope(r);
 UPDATE studio_admission.validation SET status='completed',completed_at=clock_timestamp()
 WHERE tenant_id=p.tenant_id AND id=p_validation AND status IN ('queued','running');
 IF NOT FOUND THEN RAISE check_violation USING MESSAGE='validation unavailable or terminal'; END IF;
END $$;
CREATE FUNCTION studio_admission.backend_export(p_validation uuid) RETURNS uuid
LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog,studio_admission,pg_temp AS $$
DECLARE p studio_admission.runtime_principal; d studio_admission.digest; i uuid;
BEGIN
 p=studio_admission.runtime_identity('backend');
 SELECT artifact_digest INTO d FROM studio_admission.validation WHERE tenant_id=p.tenant_id AND id=p_validation;
 i=gen_random_uuid();
 INSERT INTO studio_admission.export_record(tenant_id,id,validation_id,actor_id,artifact_digest,classification)
 VALUES(p.tenant_id,i,p_validation,p.actor_id,d,'APPROVED');
 RETURN i;
END $$;

-- A dedicated non-login, non-superuser owns definer functions and their private data.
ALTER SCHEMA studio_admission OWNER TO studio_kernel_owner;
ALTER DOMAIN studio_admission.digest OWNER TO studio_kernel_owner;
DO $$ DECLARE item record; BEGIN
 FOR item IN SELECT c.relname,c.relkind FROM pg_class c JOIN pg_namespace n ON n.oid=c.relnamespace
 WHERE n.nspname='studio_admission' AND c.relkind IN ('r','S') ORDER BY c.relkind LOOP
  -- Identity sequence ownership follows its table; do not independently alter it.
  IF item.relkind='r' THEN EXECUTE format('ALTER TABLE studio_admission.%I OWNER TO studio_kernel_owner',item.relname); END IF;
 END LOOP;
 FOR item IN SELECT p.oid::regprocedure AS signature FROM pg_proc p JOIN pg_namespace n ON n.oid=p.pronamespace WHERE n.nspname='studio_admission' LOOP
  EXECUTE format('ALTER FUNCTION %s OWNER TO studio_kernel_owner',item.signature);
  EXECUTE format('ALTER FUNCTION %s SET search_path=pg_catalog,studio_admission,pg_temp',item.signature);
 END LOOP;
END $$;
REVOKE ALL ON ALL TABLES IN SCHEMA studio_admission FROM PUBLIC,studio_backend,studio_worker;
REVOKE ALL ON ALL SEQUENCES IN SCHEMA studio_admission FROM PUBLIC,studio_backend,studio_worker;
REVOKE ALL ON ALL FUNCTIONS IN SCHEMA studio_admission FROM PUBLIC,studio_backend,studio_worker;
GRANT USAGE ON SCHEMA studio_admission TO studio_backend,studio_worker;
GRANT EXECUTE ON FUNCTION studio_admission.backend_submit(uuid,uuid,text,text),studio_admission.backend_run_status(uuid),
 studio_admission.backend_validate(uuid),studio_admission.backend_export(uuid) TO studio_backend;
GRANT EXECUTE ON FUNCTION studio_admission.worker_publish(uuid,text),studio_admission.worker_check(uuid,text,text,text,text,integer,timestamptz,timestamptz,text,text),
 studio_admission.worker_finish_validation(uuid) TO studio_worker;
ALTER DEFAULT PRIVILEGES FOR ROLE studio_kernel_owner REVOKE EXECUTE ON FUNCTIONS FROM PUBLIC;
ALTER DEFAULT PRIVILEGES FOR ROLE studio_kernel_owner IN SCHEMA studio_admission REVOKE ALL ON TABLES FROM PUBLIC;
ALTER DEFAULT PRIVILEGES FOR ROLE studio_kernel_owner IN SCHEMA studio_admission REVOKE ALL ON SEQUENCES FROM PUBLIC;
COMMIT;
