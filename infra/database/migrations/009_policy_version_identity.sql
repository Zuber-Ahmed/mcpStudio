-- A policy row is one immutable version resource. policy_key groups its lineage.
-- Never rewrite retained canonical references/approvals to make a legacy row fit.
BEGIN;
SET LOCAL ROLE studio_kernel_owner;
SET LOCAL search_path=studio_admission,pg_catalog,pg_temp;
DO $$
BEGIN
 IF EXISTS(SELECT 1 FROM validation_policy GROUP BY tenant_id,id HAVING count(*)>1) THEN
 RAISE check_violation USING MESSAGE='policy IDs must be revision-unique; explicit legacy re-publication/reapproval required'; END IF;
 IF EXISTS(SELECT 1 FROM validation_policy GROUP BY tenant_id,policy_key,version_label HAVING count(*)>1)
 OR EXISTS(SELECT 1 FROM validation_policy GROUP BY tenant_id,policy_key,version HAVING count(*)>1) THEN
 RAISE check_violation USING MESSAGE='policy lineage labels/revisions conflict; explicit reconciliation required'; END IF;
END $$;
ALTER TABLE validation_policy ADD UNIQUE(tenant_id,id),
 ADD UNIQUE(tenant_id,policy_key,version_label),ADD UNIQUE(tenant_id,policy_key,version);
COMMIT;
