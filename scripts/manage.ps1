param([Parameter(Mandatory = $true)][ValidateSet('InspectConfig', 'Init', 'Seed', 'GrantRuntime')][string]$Action)
$ErrorActionPreference = 'Stop'
if ($Action -ne 'InspectConfig') {
    Write-Output 'Unavailable in D0: migrations, roles, seed and grants require D1 implementation and authorization.'
    exit 3
}
$backend = Join-Path $PSScriptRoot '../backend'
$uv = Get-Command uv -ErrorAction SilentlyContinue
$uvPath = if ($uv) { $uv.Source } else { Join-Path $PSScriptRoot '../.tools/bin/uv.exe' }
if (-not (Test-Path -LiteralPath $uvPath)) { Write-Output 'uv unavailable'; exit 2 }
Push-Location $backend
try {
    & $uvPath run --frozen --no-sync python -m app.cli inspect-config --maintenance
    $result = $LASTEXITCODE
} finally { Pop-Location }
exit $result
