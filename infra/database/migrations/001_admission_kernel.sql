-- Foundation admission kernel v1. Partial physical model; not the full application schema.
BEGIN;
CREATE SCHEMA studio_admission;
REVOKE ALL ON SCHEMA studio_admission FROM PUBLIC;
SET LOCAL search_path=studio_admission,pg_catalog;
CREATE DOMAIN digest AS text CHECK(VALUE ~ '^[a-f0-9]{64}$');
CREATE TABLE tenant(id uuid PRIMARY KEY);
CREATE TABLE actor(id uuid PRIMARY KEY);
CREATE TABLE membership(tenant_id uuid REFERENCES tenant,actor_id uuid REFERENCES actor,
 active boolean NOT NULL DEFAULT true, PRIMARY KEY(tenant_id,actor_id));
CREATE TABLE project(tenant_id uuid NOT NULL REFERENCES tenant,id uuid NOT NULL,PRIMARY KEY(tenant_id,id));
CREATE TABLE analysis(tenant_id uuid NOT NULL,project_id uuid NOT NULL,id uuid NOT NULL,
 source_digest digest NOT NULL,next_version integer NOT NULL DEFAULT 1 CHECK(next_version>0),
 PRIMARY KEY(tenant_id,id), UNIQUE(tenant_id,project_id,id),
 FOREIGN KEY(tenant_id,project_id) REFERENCES project);
CREATE TABLE plan(tenant_id uuid NOT NULL,analysis_id uuid NOT NULL,id uuid NOT NULL,
 version integer NOT NULL CHECK(version>0),plan_hash digest NOT NULL,current boolean NOT NULL,
 PRIMARY KEY(tenant_id,id),UNIQUE(tenant_id,analysis_id,version),
 FOREIGN KEY(tenant_id,analysis_id) REFERENCES analysis);
CREATE UNIQUE INDEX one_current_plan ON plan(tenant_id,analysis_id) WHERE current;
CREATE TABLE approval(tenant_id uuid NOT NULL,id uuid NOT NULL,plan_id uuid NOT NULL,actor_id uuid NOT NULL REFERENCES actor,
 plan_hash digest NOT NULL,revoked_at timestamptz,PRIMARY KEY(tenant_id,id),
 FOREIGN KEY(tenant_id,plan_id) REFERENCES plan);
CREATE TABLE consent(tenant_id uuid NOT NULL,id uuid NOT NULL,project_id uuid NOT NULL,actor_id uuid NOT NULL REFERENCES actor,
 source_digest digest NOT NULL,provider_id text NOT NULL CHECK(length(provider_id)>0),
 payload_classes text[] NOT NULL CHECK(cardinality(payload_classes)>0 AND array_position(payload_classes,NULL) IS NULL),
 redaction_policy text NOT NULL CHECK(length(redaction_policy)>0),retention_disclosure text NOT NULL CHECK(length(retention_disclosure)>0),
 expires_at timestamptz NOT NULL,revoked_at timestamptz,PRIMARY KEY(tenant_id,id),
 FOREIGN KEY(tenant_id,project_id) REFERENCES project);
CREATE TABLE run(tenant_id uuid NOT NULL,id uuid NOT NULL,actor_id uuid NOT NULL REFERENCES actor,
 plan_id uuid NOT NULL,approval_id uuid NOT NULL,consent_id uuid,request_digest digest NOT NULL,
 status text NOT NULL DEFAULT 'queued' CHECK(status IN ('queued','running','succeeded','failed','cancelled')),
 completed_at timestamptz,PRIMARY KEY(tenant_id,id),
 CHECK((status IN ('succeeded','failed','cancelled'))=(completed_at IS NOT NULL)),
 FOREIGN KEY(tenant_id,plan_id) REFERENCES plan,FOREIGN KEY(tenant_id,approval_id) REFERENCES approval,
 FOREIGN KEY(tenant_id,consent_id) REFERENCES consent);
CREATE TABLE idempotency(tenant_id uuid NOT NULL,actor_id uuid NOT NULL,operation text NOT NULL,
 key text NOT NULL CHECK(length(key) BETWEEN 1 AND 200),request_digest digest NOT NULL,request_body jsonb NOT NULL,
 run_id uuid NOT NULL,PRIMARY KEY(tenant_id,actor_id,operation,key),
 FOREIGN KEY(tenant_id,run_id) REFERENCES run);
CREATE TABLE outbox(tenant_id uuid NOT NULL,event_id uuid NOT NULL,run_id uuid NOT NULL,event_type text NOT NULL,
 PRIMARY KEY(tenant_id,event_id),UNIQUE(tenant_id,run_id,event_type),FOREIGN KEY(tenant_id,run_id) REFERENCES run);

CREATE FUNCTION new_plan(t uuid,a uuid,i uuid,h digest) RETURNS integer
LANGUAGE plpgsql SET search_path=studio_admission,pg_catalog AS $$
DECLARE v integer;
BEGIN
 UPDATE analysis SET next_version=next_version+1 WHERE tenant_id=t AND id=a RETURNING next_version-1 INTO v;
 IF NOT FOUND THEN RAISE foreign_key_violation USING MESSAGE='analysis not found'; END IF;
 UPDATE plan SET current=false WHERE tenant_id=t AND analysis_id=a AND current;
 INSERT INTO plan VALUES(t,a,i,v,h,true);
 RETURN v;
END $$;

-- All supported admission calls lock analysis -> plan -> approval -> membership -> consent.
-- Ordinary UPDATE/DELETE of those rows therefore serializes with in-flight admission.
-- Caller identity must be server-derived; DB roles must never be issued to browsers.
CREATE FUNCTION admit(t uuid,actor uuid,p uuid,approval uuid,k text,d digest,
 consent uuid DEFAULT NULL,provider text DEFAULT NULL,classes text[] DEFAULT NULL,
 redaction text DEFAULT NULL,retention text DEFAULT NULL) RETURNS uuid
LANGUAGE plpgsql SET search_path=studio_admission,pg_catalog AS $$
#variable_conflict use_variable
DECLARE pl plan; ap studio_admission.approval; an analysis; co studio_admission.consent;
 prior idempotency; body jsonb; rid uuid;
BEGIN
 SELECT a.* INTO an FROM analysis a JOIN plan q ON q.tenant_id=a.tenant_id AND q.analysis_id=a.id
 WHERE q.tenant_id=t AND q.id=p FOR UPDATE OF a;
 IF NOT FOUND THEN RAISE foreign_key_violation USING MESSAGE='plan not found'; END IF;
 SELECT * INTO pl FROM plan WHERE tenant_id=t AND id=p FOR UPDATE;
 SELECT * INTO ap FROM studio_admission.approval WHERE tenant_id=t AND id=approval FOR UPDATE;
 IF ap.id IS NULL OR ap.plan_id<>p OR ap.actor_id<>actor OR ap.plan_hash<>pl.plan_hash
 OR ap.revoked_at IS NOT NULL OR NOT pl.current THEN
 RAISE check_violation USING MESSAGE='approval unavailable or stale'; END IF;
 PERFORM 1 FROM membership WHERE tenant_id=t AND actor_id=actor AND active FOR SHARE;
 IF NOT FOUND THEN RAISE check_violation USING MESSAGE='actor has no current rights'; END IF;
 IF consent IS NOT NULL THEN
  SELECT * INTO co FROM studio_admission.consent WHERE tenant_id=t AND id=consent FOR UPDATE;
  IF co.id IS NULL OR co.project_id<>an.project_id OR co.actor_id<>actor OR co.source_digest<>an.source_digest
  OR co.revoked_at IS NOT NULL OR co.expires_at<=clock_timestamp()
  OR provider IS NULL OR provider IS DISTINCT FROM co.provider_id
  OR classes IS NULL OR cardinality(classes)=0 OR array_position(classes,NULL) IS NOT NULL
  OR NOT classes <@ co.payload_classes OR redaction IS DISTINCT FROM co.redaction_policy
  OR retention IS DISTINCT FROM co.retention_disclosure THEN
   RAISE check_violation USING MESSAGE='consent unavailable or out of scope'; END IF;
 ELSIF provider IS NOT NULL OR classes IS NOT NULL OR redaction IS NOT NULL OR retention IS NOT NULL THEN
  RAISE check_violation USING MESSAGE='inference requires explicit scoped consent';
 END IF;
 body=jsonb_build_object('plan',p,'approval',approval,'consent',consent,'provider',provider,
  'classes',classes,'redaction',redaction,'retention',retention);
 -- An actor row serializes the same idempotency key across different analyses as well.
 PERFORM 1 FROM studio_admission.actor WHERE id=actor FOR UPDATE;
 SELECT * INTO prior FROM idempotency WHERE tenant_id=t AND actor_id=actor AND operation='generate' AND key=k;
 IF FOUND THEN
  IF prior.request_digest<>d OR prior.request_body<>body THEN
   RAISE EXCEPTION USING ERRCODE='P0409',MESSAGE='idempotency body conflict'; END IF;
  RETURN prior.run_id;
 END IF;
 rid=gen_random_uuid();
 INSERT INTO run(tenant_id,id,actor_id,plan_id,approval_id,consent_id,request_digest) VALUES(t,rid,actor,p,approval,consent,d);
 INSERT INTO idempotency VALUES(t,actor,'generate',k,d,body,rid);
 INSERT INTO outbox VALUES(t,gen_random_uuid(),rid,'generation.admitted');
 RETURN rid;
END $$;
REVOKE ALL ON ALL TABLES IN SCHEMA studio_admission FROM PUBLIC;
REVOKE ALL ON ALL FUNCTIONS IN SCHEMA studio_admission FROM PUBLIC;
COMMIT;
