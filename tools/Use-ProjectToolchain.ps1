# Dot-source this file in a project PowerShell session. Global PATH is unchanged.
$projectRoot = Split-Path $PSScriptRoot -Parent
$projectNode = Join-Path $projectRoot 'work\runtimes\node-v26.13.0-win-x64'
$projectGo = Join-Path $projectRoot 'work\runtimes\go1.27.3\go\bin'
foreach ($executable in @((Join-Path $projectNode 'node.exe'), (Join-Path $projectGo 'go.exe'))) {
    if (-not (Test-Path -LiteralPath $executable)) { throw "Missing project toolchain: $executable" }
}
$env:PATH = "$projectNode;$projectGo;$env:PATH"
Write-Output 'Project Node 26.13.0 and Go 1.27.3 activated for this PowerShell session.'
