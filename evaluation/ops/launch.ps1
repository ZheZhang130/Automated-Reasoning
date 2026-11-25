# Start one detached `evaluation <command> <plan>` process with persistent logs; refuses if one already runs for the study.
#   & E:\CSC2108Local\ops\launch.ps1 -Study E:\CSC2108Local\final-eval-smoke -Plan <plan.json> [-Command run|score]
[CmdletBinding(PositionalBinding = $false)]
param(
    [Parameter(Mandatory = $true)][string]$Study,
    [Parameter(Mandatory = $true)][string]$Plan,
    [string]$Command = 'run'
)
$ErrorActionPreference = 'Stop'
$active = Get-CimInstance Win32_Process | Where-Object {
    $_.CommandLine -and $_.CommandLine -match 'evaluation|guided_agent' -and $_.CommandLine -match [regex]::Escape($Study) }
if ($active) {
    $active | Select-Object ProcessId, Name, CommandLine | Format-List | Out-String | Write-Host
    throw "a process for $Study is already running; refusing to start a duplicate"
}
$logs = Join-Path $Study 'ops-logs'
New-Item -ItemType Directory -Force $logs | Out-Null
$stamp = (Get-Date).ToUniversalTime().ToString('yyyyMMddTHHmmssZ')
$out = Join-Path $logs "$Command-$stamp.stdout.log"
$err = Join-Path $logs "$Command-$stamp.stderr.log"
$p = Start-Process -FilePath powershell.exe -WindowStyle Hidden -PassThru `
    -ArgumentList @('-NoProfile', '-ExecutionPolicy', 'Bypass', '-File', 'E:\CSC2108Local\ops\ev.ps1',
                    $Study, $Command, $Plan) `
    -RedirectStandardOutput $out -RedirectStandardError $err
$record = [ordered]@{ utc = (Get-Date).ToUniversalTime().ToString('o'); pid = $p.Id; command = $Command; plan = $Plan;
                      study = $Study; stdout = $out; stderr = $err }
($record | ConvertTo-Json -Compress) | Add-Content -Encoding utf8 (Join-Path $logs 'launches.jsonl')
$record | ConvertTo-Json
