param([switch]$ResetBootstrap)
$ErrorActionPreference='Stop'
$root=(Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path
$local=Join-Path $root '.local\api'
New-Item -ItemType Directory -Force -Path $local | Out-Null
$serviceCredentials=Get-Content (Join-Path $root '.local\services\credentials.json') -Raw | ConvertFrom-Json
$configFile=Join-Path $local 'config.json'
if(Test-Path $configFile){$config=Get-Content $configFile -Raw | ConvertFrom-Json}else{
 $config=[ordered]@{tenant_id=[guid]::NewGuid().ToString();actor_id=[guid]::NewGuid().ToString();database_password=[Convert]::ToBase64String((1..32|ForEach-Object{Get-Random -Maximum 256})).TrimEnd('=').Replace('+','-').Replace('/','_')}
 $config|ConvertTo-Json|Set-Content -NoNewline $configFile
}
function Psql([string]$database,[string]$sql){
 $sql | docker exec -i -e "PGPASSWORD=$($serviceCredentials.db_password)" mcpstudio-local-postgres-1 psql -v ON_ERROR_STOP=1 -U mcpstudio_local -d $database | Out-Null
}
$exists=[string](docker exec -e "PGPASSWORD=$($serviceCredentials.db_password)" mcpstudio-local-postgres-1 psql -At -U mcpstudio_local -d postgres -c "select 1 from pg_database where datname='mcpstudio'")
if($null -eq $exists){$exists=''}else{$exists=$exists.Trim()}
if($exists -ne '1'){Psql 'postgres' 'CREATE DATABASE mcpstudio;'}
$schema=[string](docker exec -e "PGPASSWORD=$($serviceCredentials.db_password)" mcpstudio-local-postgres-1 psql -At -U mcpstudio_local -d mcpstudio -c "select to_regnamespace('studio_admission') is not null")
if($null -eq $schema){$schema=''}else{$schema=$schema.Trim()}
if($schema -ne 't'){
 Get-ChildItem (Join-Path $root 'infra\database\migrations') -Filter '*.sql' | Sort-Object Name | ForEach-Object { Psql 'mcpstudio' (Get-Content $_.FullName -Raw) }
}
$projectApi=[string](docker exec -e "PGPASSWORD=$($serviceCredentials.db_password)" mcpstudio-local-postgres-1 psql -At -U mcpstudio_local -d mcpstudio -c "select to_regprocedure('studio_admission.backend_create_project(text,jsonb)') is not null")
if($null -eq $projectApi -or $projectApi.Trim() -ne 't'){Psql 'mcpstudio' (Get-Content (Join-Path $root 'infra\database\migrations\010_project_api.sql') -Raw)}
$analysisApi=[string](docker exec -e "PGPASSWORD=$($serviceCredentials.db_password)" mcpstudio-local-postgres-1 psql -At -U mcpstudio_local -d mcpstudio -c "select to_regprocedure('studio_admission.backend_store_analysis(jsonb)') is not null")
if($null -eq $analysisApi -or $analysisApi.Trim() -ne 't'){Psql 'mcpstudio' (Get-Content (Join-Path $root 'infra\database\migrations\011_analysis_api.sql') -Raw)}
$discoveryApi=[string](docker exec -e "PGPASSWORD=$($serviceCredentials.db_password)" mcpstudio-local-postgres-1 psql -At -U mcpstudio_local -d mcpstudio -c "select to_regprocedure('studio_admission.backend_store_discovery(uuid,jsonb)') is not null")
if($null -eq $discoveryApi -or $discoveryApi.Trim() -ne 't'){Psql 'mcpstudio' (Get-Content (Join-Path $root 'infra\database\migrations\012_candidate_discovery_api.sql') -Raw)}
$planApi=[string](docker exec -e "PGPASSWORD=$($serviceCredentials.db_password)" mcpstudio-local-postgres-1 psql -At -U mcpstudio_local -d mcpstudio -c "select to_regprocedure('studio_admission.backend_create_exact_plan(jsonb,bytea,text)') is not null")
if($null -eq $planApi -or $planApi.Trim() -ne 't'){Psql 'mcpstudio' (Get-Content (Join-Path $root 'infra\database\migrations\013_exact_plan_approval_api.sql') -Raw)}
$adjudicationApi=[string](docker exec -e "PGPASSWORD=$($serviceCredentials.db_password)" mcpstudio-local-postgres-1 psql -At -U mcpstudio_local -d mcpstudio -c "select to_regprocedure('studio_admission.backend_adjudicate_candidate(uuid,jsonb)') is not null")
if($null -eq $adjudicationApi -or $adjudicationApi.Trim() -ne 't'){Psql 'mcpstudio' (Get-Content (Join-Path $root 'infra\database\migrations\014_candidate_adjudication.sql') -Raw)}
$escapedPassword=$config.database_password.Replace("'","''")
$seed=@"
DO `$`$ BEGIN
 IF NOT EXISTS(SELECT 1 FROM pg_roles WHERE rolname='mcpstudio_api') THEN
  EXECUTE 'CREATE ROLE mcpstudio_api LOGIN PASSWORD ''$escapedPassword'' NOSUPERUSER NOCREATEDB NOCREATEROLE NOREPLICATION NOBYPASSRLS';
 END IF;
END `$`$;
GRANT studio_backend TO mcpstudio_api;
INSERT INTO studio_admission.tenant(id,name) VALUES('$($config.tenant_id)','Local workspace') ON CONFLICT DO NOTHING;
INSERT INTO studio_admission.actor(id,subject) VALUES('$($config.actor_id)','local-operator') ON CONFLICT DO NOTHING;
INSERT INTO studio_admission.membership(tenant_id,actor_id,active,role) VALUES('$($config.tenant_id)','$($config.actor_id)',true,'operator') ON CONFLICT DO NOTHING;
INSERT INTO studio_admission.runtime_principal(login_name,tenant_id,actor_id,capability,enabled)
VALUES('mcpstudio_api','$($config.tenant_id)','$($config.actor_id)','backend',true)
ON CONFLICT(login_name) DO UPDATE SET enabled=true;
"@
Psql 'mcpstudio' $seed
$bootstrapFile=Join-Path $local 'bootstrap-code.txt'
if($ResetBootstrap -or -not(Test-Path $bootstrapFile)){
 $bytes=New-Object byte[] 32;[Security.Cryptography.RandomNumberGenerator]::Fill($bytes)
 [Convert]::ToBase64String($bytes).TrimEnd('=').Replace('+','-').Replace('/','_')|Set-Content -NoNewline $bootstrapFile
}
$envFile=Join-Path $local 'runtime.env'
@(
 "MCPSTUDIO_DATABASE_URL=postgres://mcpstudio_api:$($config.database_password)@127.0.0.1:5432/mcpstudio?sslmode=disable"
 "MCPSTUDIO_TENANT_ID=$($config.tenant_id)"
 "MCPSTUDIO_ACTOR_ID=$($config.actor_id)"
 "MCPSTUDIO_BOOTSTRAP_CODE=$(Get-Content $bootstrapFile -Raw)"
 "MCPSTUDIO_WEB_DIR=$(Join-Path $root 'apps\web\out')"
 "MCPSTUDIO_LISTEN=127.0.0.1:8080"
)|Set-Content $envFile
Write-Host 'Application database and one-time bootstrap are ready.'
