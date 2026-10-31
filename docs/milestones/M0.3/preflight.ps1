param()
$ErrorActionPreference = 'Continue'
$items = [Collections.Generic.List[object]]::new()
foreach ($name in @('node','npm','go','docker','wsl','psql')) {
    $cmd = Get-Command $name -ErrorAction SilentlyContinue | Select-Object -First 1
    $items.Add([pscustomobject]@{tool=$name;found=($null -ne $cmd);path=$cmd.Source})
}
$nodeVersion = if (Get-Command node -ErrorAction SilentlyContinue) { (& node --version 2>&1 | Out-String).Trim() } else { 'missing' }
$docker = Get-Command docker -ErrorAction SilentlyContinue
$dockerOutput = if ($docker) { (& docker version --format '{{json .}}' 2>&1 | Out-String).Trim() } else { 'docker command unavailable; engine/Compose/Linux sandbox not tested' }
$report = [ordered]@{timeUtc=[DateTime]::UtcNow.ToString('o');tools=$items;observedNode=$nodeVersion;docker=$dockerOutput;
    repository='C:/Users/ADMIN/mcpStudio';repositoryWriteAccess='not established; outside current writable roots';
    sandboxProof='not run';databaseProof='not run';serviceImageDigests='not resolved';readyForInitialization=$false}
$report | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath (Join-Path $PSScriptRoot 'preflight-results.json') -Encoding utf8
$report | ConvertTo-Json -Depth 6
