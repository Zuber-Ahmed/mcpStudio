-- M0.3 disposable constraint prototype. NOT the application's production migration.
CREATE SCHEMA fixture;
SET search_path=fixture;
CREATE FUNCTION ident(n integer) RETURNS uuid LANGUAGE sql IMMUTABLE AS $$
 SELECT ('00000000-0000-4000-8000-' || lpad(n::text,12,'0'))::uuid $$;
CREATE TABLE results(name text PRIMARY KEY, passed boolean NOT NULL);
CREATE FUNCTION assert_rejected(label text, statement text, expected text) RETURNS void LANGUAGE plpgsql AS $$
DECLARE accepted boolean:=false;
BEGIN
 BEGIN
  EXECUTE statement; accepted:=true;
 EXCEPTION WHEN OTHERS THEN
  IF SQLSTATE<>expected THEN RAISE EXCEPTION 'Unexpected SQLSTATE % for %: %',SQLSTATE,label,SQLERRM; END IF;
  INSERT INTO results VALUES(label,true);
 END;
 IF accepted THEN RAISE EXCEPTION 'Expected rejection did not occur: %',label; END IF;
END $$;
CREATE TABLE tenant(id uuid PRIMARY KEY);
CREATE TABLE actor(id uuid PRIMARY KEY);
CREATE TABLE membership(tenant_id uuid REFERENCES tenant,actor_id uuid REFERENCES actor,PRIMARY KEY(tenant_id,actor_id));
CREATE TABLE project(id uuid PRIMARY KEY,tenant_id uuid NOT NULL REFERENCES tenant,UNIQUE(tenant_id,id));
CREATE TABLE snapshot(id uuid PRIMARY KEY,tenant_id uuid NOT NULL,project_id uuid NOT NULL,digest text NOT NULL CHECK(digest ~ '^[a-f0-9]{64}$'),
 UNIQUE(tenant_id,id),FOREIGN KEY(tenant_id,project_id) REFERENCES project(tenant_id,id));
CREATE TABLE analysis(id uuid PRIMARY KEY,tenant_id uuid NOT NULL,project_id uuid NOT NULL,snapshot_id uuid NOT NULL,
 UNIQUE(tenant_id,id),UNIQUE(tenant_id,id,snapshot_id),FOREIGN KEY(tenant_id,project_id) REFERENCES project(tenant_id,id),
 FOREIGN KEY(tenant_id,snapshot_id) REFERENCES snapshot(tenant_id,id));
CREATE TABLE node(id uuid PRIMARY KEY,tenant_id uuid NOT NULL,analysis_id uuid NOT NULL,
 UNIQUE(tenant_id,analysis_id,id),FOREIGN KEY(tenant_id,analysis_id) REFERENCES analysis(tenant_id,id));
CREATE TABLE edge(id uuid PRIMARY KEY,tenant_id uuid NOT NULL,analysis_id uuid NOT NULL,source_id uuid NOT NULL,target_id uuid NOT NULL,
 FOREIGN KEY(tenant_id,analysis_id,source_id) REFERENCES node(tenant_id,analysis_id,id),
 FOREIGN KEY(tenant_id,analysis_id,target_id) REFERENCES node(tenant_id,analysis_id,id));
CREATE TABLE recommendation(id uuid PRIMARY KEY,tenant_id uuid NOT NULL,analysis_id uuid NOT NULL,
 UNIQUE(tenant_id,analysis_id,id),FOREIGN KEY(tenant_id,analysis_id) REFERENCES analysis(tenant_id,id));
CREATE FUNCTION unique_names(names text[]) RETURNS boolean LANGUAGE sql IMMUTABLE AS $$
 SELECT cardinality(names)>0 AND cardinality(names)=(SELECT count(DISTINCT n) FROM unnest(names) n) $$;
CREATE TABLE policy(id uuid PRIMARY KEY,tenant_id uuid NOT NULL REFERENCES tenant,version integer NOT NULL,required_checks text[] NOT NULL CHECK(unique_names(required_checks)),
 UNIQUE(tenant_id,id,version));
CREATE TABLE plan(id uuid PRIMARY KEY,tenant_id uuid NOT NULL,analysis_id uuid NOT NULL,snapshot_id uuid NOT NULL,recommendation_id uuid NOT NULL,
 version integer NOT NULL CHECK(version>0),current boolean NOT NULL,hash text NOT NULL CHECK(hash ~ '^[a-f0-9]{64}$'),policy_id uuid NOT NULL,policy_version integer NOT NULL,
 UNIQUE(tenant_id,id),UNIQUE(tenant_id,analysis_id,version),
 FOREIGN KEY(tenant_id,analysis_id,snapshot_id) REFERENCES analysis(tenant_id,id,snapshot_id),
 FOREIGN KEY(tenant_id,analysis_id,recommendation_id) REFERENCES recommendation(tenant_id,analysis_id,id),
 FOREIGN KEY(tenant_id,policy_id,policy_version) REFERENCES policy(tenant_id,id,version));
CREATE UNIQUE INDEX one_current_plan ON plan(tenant_id,analysis_id) WHERE current;
CREATE TABLE approval(id uuid PRIMARY KEY,tenant_id uuid NOT NULL,plan_id uuid NOT NULL,actor_id uuid NOT NULL REFERENCES actor,
 plan_hash text NOT NULL,plan_version integer NOT NULL,revoked boolean NOT NULL DEFAULT false,
 UNIQUE(tenant_id,plan_id,id),FOREIGN KEY(tenant_id,plan_id) REFERENCES plan(tenant_id,id));
CREATE TABLE generation(id uuid PRIMARY KEY,tenant_id uuid NOT NULL,plan_id uuid NOT NULL,approval_id uuid NOT NULL,actor_id uuid NOT NULL,
 plan_hash text NOT NULL,artifact_digest text NOT NULL CHECK(artifact_digest ~ '^[a-f0-9]{64}$'),
 policy_id uuid NOT NULL,policy_version integer NOT NULL,UNIQUE(tenant_id,id,artifact_digest,policy_id,policy_version),
 FOREIGN KEY(tenant_id,plan_id,approval_id) REFERENCES approval(tenant_id,plan_id,id));
CREATE FUNCTION admit_generation() RETURNS trigger LANGUAGE plpgsql AS $$
DECLARE p plan; a approval;
BEGIN
 SELECT * INTO p FROM plan WHERE tenant_id=NEW.tenant_id AND id=NEW.plan_id FOR UPDATE;
 SELECT * INTO a FROM approval WHERE tenant_id=NEW.tenant_id AND plan_id=NEW.plan_id AND id=NEW.approval_id;
 IF p.id IS NULL OR a.id IS NULL THEN RAISE foreign_key_violation USING MESSAGE='approval reference missing'; END IF;
 IF NOT p.current OR a.revoked OR a.actor_id<>NEW.actor_id OR p.hash<>NEW.plan_hash OR a.plan_hash<>p.hash OR a.plan_version<>p.version
  OR p.policy_id<>NEW.policy_id OR p.policy_version<>NEW.policy_version
  OR NOT EXISTS(SELECT FROM membership WHERE tenant_id=NEW.tenant_id AND actor_id=NEW.actor_id)
 THEN RAISE check_violation USING MESSAGE='stale approval, policy or current rights'; END IF;
 RETURN NEW;
END $$;
CREATE TRIGGER generation_admission BEFORE INSERT ON generation FOR EACH ROW EXECUTE FUNCTION admit_generation();
CREATE TABLE validation(id uuid PRIMARY KEY,tenant_id uuid NOT NULL,generation_id uuid NOT NULL,artifact_digest text NOT NULL,policy_id uuid NOT NULL,policy_version integer NOT NULL,
 UNIQUE(tenant_id,id),FOREIGN KEY(tenant_id,generation_id,artifact_digest,policy_id,policy_version) REFERENCES generation(tenant_id,id,artifact_digest,policy_id,policy_version));
CREATE TABLE check_result(id uuid PRIMARY KEY,tenant_id uuid NOT NULL,validation_id uuid NOT NULL,name text NOT NULL,
 status text NOT NULL CHECK(status IN ('passed','failed','skipped','not_run')),command text,tool_version text,exit_code integer,started_at timestamptz,completed_at timestamptz,log_reference text,reason text,
 UNIQUE(tenant_id,validation_id,name),FOREIGN KEY(tenant_id,validation_id) REFERENCES validation(tenant_id,id),
 CHECK((status IN ('passed','failed') AND command IS NOT NULL AND tool_version IS NOT NULL AND exit_code IS NOT NULL AND started_at IS NOT NULL AND completed_at IS NOT NULL AND completed_at>=started_at AND log_reference IS NOT NULL)
    OR (status IN ('skipped','not_run') AND reason IS NOT NULL AND exit_code IS NULL AND started_at IS NULL AND completed_at IS NULL)),
 CHECK(status<>'passed' OR exit_code=0));
CREATE TABLE idempotency(tenant_id uuid NOT NULL,actor_id uuid NOT NULL,operation text NOT NULL,key text NOT NULL,digest text NOT NULL,
 PRIMARY KEY(tenant_id,actor_id,operation,key),FOREIGN KEY(tenant_id,actor_id) REFERENCES membership);
CREATE TABLE outbox(tenant_id uuid NOT NULL REFERENCES tenant,event_id uuid NOT NULL,PRIMARY KEY(tenant_id,event_id));
INSERT INTO tenant VALUES(ident(1)),(ident(2)); INSERT INTO actor VALUES(ident(3)); INSERT INTO membership VALUES(ident(1),ident(3));
INSERT INTO project VALUES(ident(10),ident(1)),(ident(11),ident(2));
INSERT INTO snapshot VALUES(ident(20),ident(1),ident(10),repeat('a',64)),(ident(21),ident(2),ident(11),repeat('b',64));
INSERT INTO analysis VALUES(ident(30),ident(1),ident(10),ident(20)),(ident(31),ident(1),ident(10),ident(20)),(ident(32),ident(2),ident(11),ident(21));
INSERT INTO node VALUES(ident(40),ident(1),ident(30)),(ident(41),ident(1),ident(31)),(ident(42),ident(2),ident(32));
INSERT INTO recommendation VALUES(ident(50),ident(1),ident(30)),(ident(51),ident(1),ident(31));
INSERT INTO policy VALUES(ident(60),ident(1),1,ARRAY['compile','auth']);
INSERT INTO plan VALUES(ident(70),ident(1),ident(30),ident(20),ident(50),1,true,repeat('c',64),ident(60),1),
 (ident(71),ident(1),ident(30),ident(20),ident(50),2,false,repeat('d',64),ident(60),1);
INSERT INTO approval VALUES(ident(80),ident(1),ident(70),ident(3),repeat('c',64),1,false),
 (ident(81),ident(1),ident(71),ident(3),repeat('d',64),2,false);
INSERT INTO generation VALUES(ident(90),ident(1),ident(70),ident(80),ident(3),repeat('c',64),repeat('e',64),ident(60),1);
INSERT INTO validation VALUES(ident(100),ident(1),ident(90),repeat('e',64),ident(60),1);
INSERT INTO check_result VALUES(ident(110),ident(1),ident(100),'compile','passed','tsc','fixture',0,now(),now(),'fixture-log',NULL);
INSERT INTO results VALUES('same-tenant plan approval generation validation chain accepted',true);
SELECT assert_rejected('cross-tenant project child denied',$q$INSERT INTO snapshot VALUES(ident(201),ident(2),ident(10),repeat('a',64))$q$,'23503');
SELECT assert_rejected('cross-analysis graph edge denied',$q$INSERT INTO edge VALUES(ident(202),ident(1),ident(30),ident(40),ident(41))$q$,'23503');
SELECT assert_rejected('cross-tenant graph edge denied',$q$INSERT INTO edge VALUES(ident(203),ident(1),ident(30),ident(40),ident(42))$q$,'23503');
SELECT assert_rejected('duplicate plan version denied',$q$INSERT INTO plan VALUES(ident(204),ident(1),ident(30),ident(20),ident(50),1,false,repeat('f',64),ident(60),1)$q$,'23505');
SELECT assert_rejected('two current plans denied',$q$UPDATE plan SET current=true WHERE id=ident(71)$q$,'23505');
SELECT assert_rejected('foreign analysis recommendation denied',$q$INSERT INTO plan VALUES(ident(205),ident(1),ident(30),ident(20),ident(51),3,false,repeat('f',64),ident(60),1)$q$,'23503');
SELECT assert_rejected('cross-plan approval denied',$q$INSERT INTO generation VALUES(ident(206),ident(1),ident(70),ident(81),ident(3),repeat('c',64),repeat('e',64),ident(60),1)$q$,'23503');
SELECT assert_rejected('changed plan hash denied',$q$INSERT INTO generation VALUES(ident(207),ident(1),ident(70),ident(80),ident(3),repeat('f',64),repeat('e',64),ident(60),1)$q$,'23514');
UPDATE approval SET revoked=true WHERE id=ident(80);
SELECT assert_rejected('revoked approval denied',$q$INSERT INTO generation VALUES(ident(208),ident(1),ident(70),ident(80),ident(3),repeat('c',64),repeat('e',64),ident(60),1)$q$,'23514');
UPDATE approval SET revoked=false WHERE id=ident(80);
DELETE FROM membership WHERE tenant_id=ident(1) AND actor_id=ident(3);
SELECT assert_rejected('removed operator rights denied',$q$INSERT INTO generation VALUES(ident(209),ident(1),ident(70),ident(80),ident(3),repeat('c',64),repeat('e',64),ident(60),1)$q$,'23514');
INSERT INTO membership VALUES(ident(1),ident(3));
SELECT assert_rejected('changed artifact digest denied',$q$INSERT INTO validation VALUES(ident(210),ident(1),ident(90),repeat('f',64),ident(60),1)$q$,'23503');
SELECT assert_rejected('changed validation policy denied',$q$INSERT INTO validation VALUES(ident(211),ident(1),ident(90),repeat('e',64),ident(60),2)$q$,'23503');
SELECT assert_rejected('empty required-check policy denied',$q$INSERT INTO policy VALUES(ident(212),ident(1),1,ARRAY[]::text[])$q$,'23514');
SELECT assert_rejected('duplicate required checks denied',$q$INSERT INTO policy VALUES(ident(213),ident(1),1,ARRAY['compile','compile'])$q$,'23514');
SELECT assert_rejected('passed check without evidence denied',$q$INSERT INTO check_result(id,tenant_id,validation_id,name,status) VALUES(ident(214),ident(1),ident(100),'auth','passed')$q$,'23514');
SELECT assert_rejected('false passed exit denied',$q$INSERT INTO check_result VALUES(ident(215),ident(1),ident(100),'auth','passed','test','fixture',1,now(),now(),'log',NULL)$q$,'23514');
SELECT assert_rejected('skipped check with forged exit denied',$q$INSERT INTO check_result(id,tenant_id,validation_id,name,status,exit_code,reason) VALUES(ident(216),ident(1),ident(100),'auth','skipped',0,'unavailable')$q$,'23514');
SELECT assert_rejected('duplicate check record denied',$q$INSERT INTO check_result VALUES(ident(217),ident(1),ident(100),'compile','passed','test','fixture',0,now(),now(),'log',NULL)$q$,'23505');
INSERT INTO idempotency VALUES(ident(1),ident(3),'generate','fixture-key',repeat('c',64));
SELECT assert_rejected('duplicate idempotency key denied',$q$INSERT INTO idempotency VALUES(ident(1),ident(3),'generate','fixture-key',repeat('d',64))$q$,'23505');
INSERT INTO outbox VALUES(ident(1),ident(220));
SELECT assert_rejected('duplicate dispatch identity denied',$q$INSERT INTO outbox VALUES(ident(1),ident(220))$q$,'23505');
SELECT assert_rejected('referenced approval cannot cascade delete',$q$DELETE FROM approval WHERE id=ident(80)$q$,'23503');
SELECT json_build_object('passed',bool_and(passed),'checks',json_agg(json_build_object('name',name,'passed',passed) ORDER BY name)) FROM results;
