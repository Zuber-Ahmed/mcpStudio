$ErrorActionPreference='Stop'
$root=(Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path
$credentialsPath=Join-Path $root '.local\services\credentials.json'
$credentials=Get-Content $credentialsPath -Raw|ConvertFrom-Json
$bytes=New-Object byte[] 32
[Security.Cryptography.RandomNumberGenerator]::Fill($bytes)
$next=[Convert]::ToBase64String($bytes).TrimEnd('=').Replace('+','-').Replace('/','_')
"ALTER ROLE mcpstudio_local PASSWORD '$next';" | docker exec -i -e "PGPASSWORD=$($credentials.db_password)" mcpstudio-local-postgres-1 psql -v ON_ERROR_STOP=1 -U mcpstudio_local -d postgres | Out-Null
$credentials.db_password=$next
$credentials|ConvertTo-Json -Compress|Set-Content -NoNewline $credentialsPath
"MCPSTUDIO_DB_PASSWORD=$next"|Set-Content -NoNewline (Join-Path $root '.local\services\services.env')
$temporalPath=Join-Path $root '.local\services\temporal.yaml'
$temporal=Get-Content $temporalPath -Raw|ConvertFrom-Json
$temporal.persistence.datastores.default.sql.password=$next
$temporal.persistence.datastores.visibility.sql.password=$next
$temporal|ConvertTo-Json -Depth 20|Set-Content $temporalPath
Write-Host 'Local database service credential rotated without printing the value.'
