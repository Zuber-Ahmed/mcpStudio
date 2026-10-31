param()
$ErrorActionPreference = 'Stop'
$root = $PSScriptRoot
$checks = [Collections.Generic.List[object]]::new()
function Check([string]$Name, [bool]$Passed, [string]$Detail) {
    $checks.Add([pscustomobject]@{ name=$Name; passed=$Passed; detail=$Detail })
}
$required = @('README.md','inventory.md','requirements-traceability.md','gaps-and-risks.md','decisions.md','status-tracker.md','validation.md','source-conversation.json')
foreach ($name in $required) { Check "artifact:$name" (Test-Path -LiteralPath (Join-Path $root $name)) 'Required review artifact' }
$zip = Join-Path $root 'sources/final_mcp_studio_workspace.zip'
$zipHash = (Get-FileHash -LiteralPath $zip -Algorithm SHA256).Hash
Check 'source ZIP identity' ($zipHash -eq '9F05120102A9017D118492E3ADCD02B5C4F4459858DCCBCCC787421B6E0B7319') $zipHash
$sourceRoot = Join-Path $root 'sources/stitch'
$files = @(Get-ChildItem -LiteralPath $sourceRoot -Recurse -File)
Check 'source file count' ($files.Count -eq 11) "Observed $($files.Count); expected 11"
$screens = @('dashboard','project_setup','architecture_explorer','mcp_studio','results_validation')
foreach ($screen in $screens) {
    $htmlPath = Join-Path $sourceRoot "$screen/code.html"
    $pngPath = Join-Path $sourceRoot "$screen/screen.png"
    Check "HTML:$screen" (Test-Path -LiteralPath $htmlPath) 'Source screen HTML exists'
    $bytes = [IO.File]::ReadAllBytes($pngPath)
    Check "PNG:$screen" ([BitConverter]::ToString($bytes[0..7]) -eq '89-50-4E-47-0D-0A-1A-0A') 'PNG signature checked; visual review recorded separately'
}
$matrix = Get-Content -LiteralPath (Join-Path $root 'requirements-traceability.md') -Raw
$gaps = Get-Content -LiteralPath (Join-Path $root 'gaps-and-risks.md') -Raw
$adrs = Get-Content -LiteralPath (Join-Path $root 'decisions.md') -Raw
$rows = [regex]::Matches($matrix, '(?m)^\| R\d{2} \|')
Check '18 unique requirement rows' (($rows.Count -eq 18) -and (@($rows.Value | Select-Object -Unique).Count -eq 18)) "Observed $($rows.Count) rows"
foreach ($n in 1..18) {
    $r = 'R{0:00}' -f $n
    $t = 'T{0:00}' -f $n
    $row = [regex]::Match($matrix, "(?m)^\| $r \|.*$").Value
    Check "trace:$r" (($row -match $t) -and (($row.Split('|').Count - 2) -eq 8)) "Eight columns with planned $t; does not validate runtime behavior"
}
foreach ($n in 1..15) {
    $g = 'G{0:00}' -f $n
    Check "gap:$g" (($gaps -match "(?m)^\| $g \|") -and ($matrix -match $g)) 'Gap defined and referenced by requirement'
}
foreach ($n in 1..9) {
    $a = 'ADR-{0:000}' -f $n
    Check "decision:$a" ($adrs -match "(?m)^\| $a \|") 'Decision inventory record exists'
}
foreach ($n in 1..5) { Check "screen:S$n" ($matrix -match "S$n") 'Screen included in traceability' }
$dashboard = Get-Content -LiteralPath (Join-Path $sourceRoot 'dashboard/code.html') -Raw
Check 'dashboard mismatch anchors' (($dashboard -match 'data-filter="ready"') -and ($dashboard -match "activeFilter === 'integrated'")) 'Conflicting UI/script filter values present'
$studio = Get-Content -LiteralPath (Join-Path $sourceRoot 'mcp_studio/code.html') -Raw
Check 'generation prototype anchor' (($studio -match 'function triggerGenerate') -and ($studio -match 'setTimeout')) 'Timer prototype exists; not a generation test'
$results = Get-Content -LiteralPath (Join-Path $sourceRoot 'results_validation/code.html') -Raw
Check 'export distinction anchors' (($results -match 'Export Approved Bundle') -and ($results -match 'Download Draft') -and ($results -match 'Skipped')) 'Blocked/draft/skip source text present'
$conversation = Get-Content -LiteralPath (Join-Path $root 'source-conversation.json') -Raw | ConvertFrom-Json
Check 'conversation provenance' (($conversation.thread.id -eq '6adf8000-7004-83ed-b840-4aee7adb5739') -and ($conversation.turns.Count -eq 5) -and (-not $conversation.page.hasMore)) 'Five available turns; no older cursor'
$manifest = @($files | Sort-Object FullName | ForEach-Object { [pscustomobject]@{ path=[IO.Path]::GetRelativePath($sourceRoot,$_.FullName); bytes=$_.Length; sha256=(Get-FileHash -LiteralPath $_.FullName -Algorithm SHA256).Hash } })
$failed = @($checks | Where-Object { -not $_.passed })
$report = [ordered]@{ generatedUtc=[DateTime]::UtcNow.ToString('o'); scope='M0.1 inventory integrity only'; passed=($failed.Count -eq 0); checkCount=$checks.Count; failedCount=$failed.Count; checks=$checks; sourceManifest=$manifest; runtimeTestsExecuted=0; verifiedStudioEndpoints=0; verifiedDatabaseEntities=0; gate='Blocked: missing authoritative inputs and unresolved conflicts' }
$report | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath (Join-Path $root 'validation-results.json') -Encoding utf8
Write-Output "Inventory checks: $($checks.Count); failed: $($failed.Count). Runtime tests: 0. M0.1 approval gate remains blocked."
if ($failed.Count -gt 0) { $failed | Format-Table; exit 1 }
