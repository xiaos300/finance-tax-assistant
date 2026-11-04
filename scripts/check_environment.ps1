$ErrorActionPreference = 'Stop'
$missing = @()
$dockerProbeConfig = Join-Path $PSScriptRoot '../.cache/docker-probe'
New-Item -ItemType Directory -Path $dockerProbeConfig -Force | Out-Null
foreach ($tool in @('python', 'node', 'npm.cmd', 'uv', 'docker', 'psql', 'pwsh')) {
    $command = Get-Command $tool -ErrorAction SilentlyContinue
    if ($command) {
        if ($tool -eq 'docker') {
            # Version probing needs no access to the operator's Docker credentials.
            $version = & $command.Source --config $dockerProbeConfig --version
        } else {
            $version = & $command.Source --version
        }
        if ($LASTEXITCODE -ne 0) { $missing += $tool }
        Write-Output ("{0}: {1}" -f $tool, ($version -join ' '))
    } elseif ($tool -eq 'uv' -and (Test-Path -LiteralPath "$PSScriptRoot/../.tools/bin/uv.exe")) {
        & "$PSScriptRoot/../.tools/bin/uv.exe" --version
    } else {
        $missing += $tool
        Write-Output ("{0}: unavailable" -f $tool)
    }
}
Write-Output ("PowerShell host: {0}" -f $PSVersionTable.PSVersion)
Write-Output 'No environment values or credentials inspected. Database/server connectivity not tested.'
if ($missing.Count) { exit 2 }
exit 0
