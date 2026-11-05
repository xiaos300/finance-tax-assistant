param([Parameter(Mandatory = $true)][ValidateSet('InspectConfig', 'InspectAdmin', 'BootstrapTest', 'BootstrapDev', 'PrepareExistingTest', 'PrepareExistingDev', 'Init', 'Seed', 'GrantRuntime', 'Inspect', 'ResetTest')][string]$Action, [switch]$TestTarget, [string]$TestAcceptance, [string]$ApprovalRef)
$ErrorActionPreference = 'Stop'
$actions = @{ InspectConfig='inspect-config'; InspectAdmin='inspect-admin'; BootstrapTest='bootstrap-test'; BootstrapDev='bootstrap-dev'; PrepareExistingTest='prepare-existing-test'; PrepareExistingDev='prepare-existing-dev'; Init='migrate'; Seed='seed'; GrantRuntime='grant-runtime'; Inspect='inspect'; ResetTest='reset-test' }
$backend = Join-Path $PSScriptRoot '../backend'
$uv = Get-Command uv -ErrorAction SilentlyContinue
$uvPath = if ($uv) { $uv.Source } else { Join-Path $PSScriptRoot '../.tools/bin/uv.exe' }
if (-not (Test-Path -LiteralPath $uvPath)) { Write-Output 'uv unavailable'; exit 2 }
$savedMigration = [Environment]::GetEnvironmentVariable('MIGRATION_DATABASE_URL', 'Process')
$result = 4
if ($TestAcceptance) { $TestAcceptance = (Resolve-Path -LiteralPath $TestAcceptance).Path }
Push-Location $backend
try {
    $cliArgs = @('run', '--frozen', '--no-sync', 'python', '-m', 'app.cli', $actions[$Action], '--maintenance')
    if ($TestTarget) { $cliArgs += '--test' }
    if ($TestAcceptance) { $cliArgs += @('--test-acceptance', $TestAcceptance) }
    if ($ApprovalRef) { $cliArgs += @('--approval-ref', $ApprovalRef) }
    & $uvPath @cliArgs
    $result = $LASTEXITCODE
} finally {
    [Environment]::SetEnvironmentVariable('MIGRATION_DATABASE_URL', $savedMigration, 'Process')
    Pop-Location
}
exit $result
