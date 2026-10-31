param()
$ErrorActionPreference = 'Continue'
$projectActivation = Join-Path $PSScriptRoot 'Use-ProjectToolchain.ps1'
if (Test-Path -LiteralPath $projectActivation) { . $projectActivation }
$problems = [Collections.Generic.List[string]]::new()
foreach ($name in @('node','npm','go','docker','wsl')) {
    $command = Get-Command $name -ErrorAction SilentlyContinue | Select-Object -First 1
    if (-not $command) { $problems.Add("Missing command: $name") }
    else { Write-Output "$name available at $($command.Source)" }
}
if (Get-Command node -ErrorAction SilentlyContinue) {
    $actual = (& node --version | Out-String).Trim()
    if ($actual -ne 'v26.13.0') { $problems.Add("Node version $actual differs from selected v26.13.0") }
}
if (Get-Command docker -ErrorAction SilentlyContinue) {
    & docker info --format '{{.OSType}}'
    if ($LASTEXITCODE -ne 0) { $problems.Add('Docker engine not reachable') }
    & docker compose version
    if ($LASTEXITCODE -ne 0) { $problems.Add('Docker Compose unavailable') }
}
if (Get-Command wsl -ErrorAction SilentlyContinue) {
    $wslOutput = (& wsl --status 2>&1 | Out-String)
    if ($LASTEXITCODE -ne 0) { $problems.Add('WSL is not installed or status cannot be established; executable presence is insufficient') }
}
Write-Output 'This check installs nothing and does not prove worker isolation, exact image versions or service compatibility.'
if ($problems.Count) { $problems | ForEach-Object { Write-Output "BLOCKED: $_" }; exit 1 }
Write-Output 'Basic tool discovery passed. Run M0.3 runtime/security checks before declaring readiness.'
