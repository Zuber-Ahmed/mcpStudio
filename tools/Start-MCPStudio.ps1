$ErrorActionPreference='Stop'
$root=(Resolve-Path (Join-Path $PSScriptRoot '..')).Path
& (Join-Path $root 'tools\app\initialize-app.ps1') -ResetBootstrap
Get-Content (Join-Path $root '.local\api\runtime.env') | ForEach-Object {
 if($_ -match '^([^=]+)=(.*)$'){[Environment]::SetEnvironmentVariable($matches[1],$matches[2],'Process')}
}
$go=Join-Path $root 'work\runtimes\go1.27.3\go\bin\go.exe'
$binary=Join-Path $root '.local\api\mcpstudio-api.exe'
Push-Location (Join-Path $root 'apps\api')
try{& $go build -o $binary .;if($LASTEXITCODE -ne 0){exit $LASTEXITCODE}}finally{Pop-Location}
Write-Host 'MCP Studio: http://127.0.0.1:8080'
Write-Host 'Bootstrap code: .local/api/bootstrap-code.txt'
& $binary
