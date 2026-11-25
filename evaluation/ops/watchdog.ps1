# Overnight watchdog for one official batch: launches `evaluation run PLAN`, logs progress, keeps the project Ollama
# server (127.0.0.1:11435 only) alive, stops failure cascades, resumes after routine stops, then scores and reports.
# It never touches the user's Ollama app (11434), other Docker containers, prompts, budgets or the plan.
#
#   start (detached): & E:\CSC2108Local\ops\detach.ps1 "powershell.exe -NoProfile -ExecutionPolicy Bypass -File E:\CSC2108Local\ops\watchdog.ps1 -Study <S> -Plan <P>"
#   pause relaunching/killing (monitor only): New-Item <S>\ops-logs\watchdog.pause     resume: delete it
#   stop the watchdog (batch keeps running):   New-Item <S>\ops-logs\watchdog.stop
param([string]$Study, [string]$Plan, [int]$PollSeconds = 120, [int]$ProgressMinutes = 10, [int]$MaxRecoveries = 3)
$ErrorActionPreference = 'Continue'
$ops = Join-Path $Study 'ops-logs'
New-Item -ItemType Directory -Force $ops | Out-Null
$wlog = Join-Path $ops 'watchdog.log'
$progressLog = Join-Path $Study 'PROGRESS.log'
$stateFile = Join-Path $ops 'watchdog-state.json'
$ev = 'E:\CSC2108Local\ops\ev.ps1'
$repo = 'E:\VS Code Projects\CSC2108Project\Automated-Reasoning'
$planData = Get-Content $Plan -Raw | ConvertFrom-Json
$batch = $planData.batch
$batchDir = Join-Path $Study "runs\$batch"
$scheduled = @($planData.attempts).Count
$ledgerPath = Join-Path $Study 'api-ledger.json'
$providerFaults = @('transport_error', 'provider_error', 'timeout', 'isolation_violation')

function Now { (Get-Date).ToUniversalTime().ToString('yyyy-MM-ddTHH:mm:ssZ') }
function Log([string]$m) { "$(Now) $m" | Add-Content -Encoding utf8 $wlog }
function Progress([string]$m) { "$(Now) $m" | Add-Content -Encoding utf8 $progressLog; Log "PROGRESS $m" }

# single instance per study
$others = Get-CimInstance Win32_Process | Where-Object { $_.ProcessId -ne $PID -and $_.CommandLine -and
    $_.CommandLine -match 'watchdog\.ps1' -and $_.CommandLine -match [regex]::Escape($Study) }
if ($others) { Log "another watchdog is running for this study (pid $($others.ProcessId -join ',')); exiting"; exit 0 }

function OllamaOk {
    try { $null = Invoke-RestMethod 'http://127.0.0.1:11435/api/version' -TimeoutSec 15; return $true } catch { return $false }
}
function DockerOk {
    $j = Start-Job { docker version --format '{{.Server.Version}}' 2>$null }
    if (Wait-Job $j -Timeout 45) { $o = Receive-Job $j; Remove-Job $j -Force; return [bool]$o }
    Stop-Job $j; Remove-Job $j -Force; return $false
}
function RunProcs {
    Get-CimInstance Win32_Process | Where-Object { $_.CommandLine -and $_.ProcessId -ne $PID -and
        $_.CommandLine -match [regex]::Escape($Study) -and $_.CommandLine -notmatch 'watchdog\.ps1' -and
        ($_.CommandLine -match 'guided_agent' -or $_.CommandLine -match 'evaluation' -or $_.CommandLine -match 'ev\.ps1') }
}
function KillRun([string]$why) {
    Log "KILL run tree: $why"
    foreach ($p in @(RunProcs)) { Log "  stop pid $($p.ProcessId) $($p.Name)"; Stop-Process -Id $p.ProcessId -Force -ErrorAction SilentlyContinue }
    $rows = docker ps -a --filter 'label=csc2108.eval-v2.run' --format '{{.ID}} {{.Label "csc2108.eval-v2.run"}}' 2>$null
    foreach ($row in @($rows)) {
        $id, $label = "$row" -split ' ', 2
        if ($label -like "agent-$batch-*") { Log "  remove sandbox $id ($label)"; docker rm -f $id 2>$null | Out-Null }
    }
}
function RestartOllama {
    $listen = Get-NetTCPConnection -LocalPort 11435 -State Listen -ErrorAction SilentlyContinue
    foreach ($l in @($listen)) {
        $proc = Get-CimInstance Win32_Process -Filter "ProcessId=$($l.OwningProcess)"
        if ($proc -and $proc.Name -eq 'ollama.exe') { Log "  stop unresponsive project Ollama pid $($proc.ProcessId)"; Stop-Process -Id $proc.ProcessId -Force -ErrorAction SilentlyContinue }
    }
    Start-Sleep 5
    & powershell.exe -NoProfile -ExecutionPolicy Bypass -File "$repo\local_baseline\start_ollama.ps1" *>> (Join-Path $ops 'ollama-restarts.log')
    for ($i = 0; $i -lt 24; $i++) { if (OllamaOk) { break }; Start-Sleep 5 }
    try {
        $tags = Invoke-RestMethod 'http://127.0.0.1:11435/api/tags' -TimeoutSec 15
        $d = ($tags.models | Where-Object { $_.name -eq 'qwen3.5:9b' }).digest
        Log "  Ollama restarted: up=$(OllamaOk) qwen3.5:9b digest=$d"
    } catch { Log "  Ollama restart failed: $_" }
}
function LaunchRun {
    $stamp = (Get-Date).ToUniversalTime().ToString('yyyyMMddTHHmmssZ')
    $out = Join-Path $ops "run-$stamp.stdout.log"; $err = Join-Path $ops "run-$stamp.stderr.log"
    $p = Start-Process -FilePath powershell.exe -WindowStyle Hidden -PassThru -RedirectStandardOutput $out -RedirectStandardError $err `
        -ArgumentList @('-NoProfile', '-ExecutionPolicy', 'Bypass', '-File', $ev, $Study, 'run', $Plan)
    $rec = [ordered]@{ utc = (Get-Date).ToUniversalTime().ToString('o'); pid = $p.Id; command = 'run'; plan = $Plan; study = $Study;
                       stdout = $out; stderr = $err; by = 'watchdog' }
    ($rec | ConvertTo-Json -Compress) | Add-Content -Encoding utf8 (Join-Path $ops 'launches.jsonl')
    Log "LAUNCH run pid $($p.Id) logs $out"
    return $p
}
function RunAndWait([string[]]$a, [string]$name) {
    $stamp = (Get-Date).ToUniversalTime().ToString('yyyyMMddTHHmmssZ')
    $out = Join-Path $ops "$name-$stamp.stdout.log"; $err = Join-Path $ops "$name-$stamp.stderr.log"
    $p = Start-Process -FilePath powershell.exe -WindowStyle Hidden -PassThru -Wait -RedirectStandardOutput $out -RedirectStandardError $err `
        -ArgumentList (@('-NoProfile', '-ExecutionPolicy', 'Bypass', '-File', $ev, $Study) + $a)
    Log "$name exited $($p.ExitCode) (logs $out)"
    return $p.ExitCode
}
function Finished {
    if (-not (Test-Path $batchDir)) { return @() }
    @(Get-ChildItem $batchDir -Directory | Where-Object { $_.Name -notmatch '\.incomplete-' -and (Test-Path (Join-Path $_.FullName 'result.json')) })
}
$seen = @{}
function Classify($dir) {
    # quick operational classification (the report's own classification is authoritative)
    try { $r = Get-Content (Join-Path $dir 'result.json') -Raw | ConvertFrom-Json } catch { return 'unreadable' }
    $err = "$($r.frozen_error.error)"
    if ($r.setup_error) { return 'infra:setup' }
    if ($r.raw_exit_status -eq 'OuterTimeout') { return 'infra:outer_timeout' }
    if ($err -match 'FrontierCoderError') { if ($err -match 'ceiling|spending bound') { return 'budget' }; return 'frontier' }
    if ($r.diagnosis -and $r.diagnosis.error_category) {
        if ($r.diagnosis.error_category -eq 'budget_exhausted') { return 'budget' }
        if ($providerFaults -contains $r.diagnosis.error_category) { return 'frontier' }
    }
    if ($r.exit_status -eq 'infra_error') {
        $m = $null; try { $m = Get-Content (Join-Path $dir 'measurement.json') -Raw | ConvertFrom-Json } catch {}
        if ($err -match 'litellm\.Timeout' -or ($m -and $m.correctness.context_overflow)) { return 'model' }
        if ($m -and -not $m.correctness.infrastructure_failure) { return 'model' }
        return 'infra:runner'
    }
    return 'ok'
}
function LedgerSummary {
    if (-not (Test-Path $ledgerPath)) { return 'ledger=none' }
    try {
        $l = Get-Content $ledgerPath -Raw | ConvertFrom-Json
        $req = @($l.requests); $std = 0.0; $res = 0.0
        foreach ($q in $req) {
            if ($q.cost_usd_standard) { $std += [double]$q.cost_usd_standard }
            if ($q.usage) { $res += ([double]$q.usage.prompt_tokens * 12 + [double]$q.usage.completion_tokens * 60) / 1e6 }
            elseif ($q.state -ne 'completed' -and $q.bound_usd_conservative) { $res += [double]$q.bound_usd_conservative }
        }
        $states = ($req | Group-Object state | ForEach-Object { "$($_.Name)=$($_.Count)" }) -join ','
        return ('requests={0}/{1} std_cost=${2:N3} reservation~${3:N2}/{4} states[{5}]' -f $req.Count, $l.max_requests, $std, $res, $l.max_usd, $states)
    } catch { return "ledger=unreadable" }
}

$st = @{ recoveries = @{}; ollamaFails = 0; consecLocalInfra = 0; consecFrontier = 0; budgetLogged = $false;
         lastProgress = (Get-Date).AddYears(-1); lastRecoveryFinished = 0; done = $false; foreignWaits = 0 }
function Recovery([string]$kind) {
    $n = 0; if ($st.recoveries.ContainsKey($kind)) { $n = $st.recoveries[$kind] }
    $st.recoveries[$kind] = $n + 1
    return ($n + 1) -le $MaxRecoveries
}

Log "watchdog start pid $PID study=$Study plan=$Plan batch=$batch scheduled=$scheduled poll=${PollSeconds}s"
$run = $null
$existing = @(RunProcs)
if ($existing) { Log "adopting existing run processes: $($existing.ProcessId -join ',')" }
elseif (-not (Test-Path (Join-Path $ops 'watchdog.pause'))) { $run = LaunchRun }
$blocked = $false

while ($true) {
    if (Test-Path (Join-Path $ops 'watchdog.stop')) { Log 'watchdog.stop found: exiting (batch processes untouched)'; break }
    $paused = Test-Path (Join-Path $ops 'watchdog.pause')
    $fin = Finished
    $alive = @(RunProcs).Count -gt 0
    # classify newly finished attempts in completion order
    foreach ($d in ($fin | Sort-Object LastWriteTime)) {
        if ($seen.ContainsKey($d.Name)) { continue }
        $c = Classify $d.FullName; $seen[$d.Name] = $c
        if ($c -like 'infra:*') { $st.consecLocalInfra++; Log "INFRA-LIKE result $($d.Name): $c" } elseif ($c -ne 'frontier') { $st.consecLocalInfra = 0 }
        if ($c -eq 'frontier') { $st.consecFrontier++; Log "FRONTIER FAULT $($d.Name)" } elseif ($d.Name -match '-(B|E)-s\d+$') { $st.consecFrontier = 0 }
        if ($c -eq 'budget' -and -not $st.budgetLogged) { Progress "BLOCKER: ledger ceiling reached at $($d.Name); B/E runs now end budget-exhausted (A/C/D continue). Needs a deliberate user decision."; $st.budgetLogged = $true }
    }
    if ($fin.Count - $st.lastRecoveryFinished -ge 10) { $st.recoveries = @{}; $st.lastRecoveryFinished = $fin.Count }

    $ollama = OllamaOk
    if ($ollama) { $st.ollamaFails = 0 } else { $st.ollamaFails++; Log "Ollama 11435 not responding ($($st.ollamaFails))" }

    if (-not $paused -and -not $blocked -and -not $st.done) {
        if ($st.ollamaFails -ge 2) {
            if (Recovery 'ollama') {
                Progress "INCIDENT: project Ollama down; stopping batch to prevent infrastructure cascade, restarting Ollama"
                if ($alive) { KillRun 'project Ollama down' }
                RestartOllama; $st.ollamaFails = 0; $alive = $false; $run = $null; Start-Sleep 30
            } else { $blocked = $true; Progress "BLOCKER: project Ollama failed more than $MaxRecoveries times without progress; watchdog stopped relaunching" }
        }
        elseif ($st.consecLocalInfra -ge 3) {
            if (Recovery 'infra') {
                Progress "INCIDENT: $($st.consecLocalInfra) consecutive infrastructure-like results; stopping batch, checking services"
                if ($alive) { KillRun 'consecutive infrastructure failures' }
                if (-not (OllamaOk)) { RestartOllama }
                if (-not (DockerOk)) { Log 'Docker not responding; waiting' }
                $st.consecLocalInfra = 0; $alive = $false; $run = $null; Start-Sleep 60
            } else { $blocked = $true; Progress "BLOCKER: recurring infrastructure failures; watchdog stopped relaunching" }
        }
        elseif ($st.consecFrontier -ge 3) {
            if (Recovery 'frontier') {
                Progress "INCIDENT: $($st.consecFrontier) consecutive frontier provider faults; pausing batch 30 min (no extra API retries)"
                if ($alive) { KillRun 'frontier provider faults' }
                $st.consecFrontier = 0; $alive = $false; $run = $null; Start-Sleep 1800
            } else { $blocked = $true; Progress "BLOCKER: recurring frontier provider faults; watchdog stopped relaunching" }
        }
        if (-not $alive -and -not $blocked) {
            $code = $null; if ($run) { $run.WaitForExit(1000) | Out-Null; $code = $run.ExitCode }
            $fin = Finished
            if ($fin.Count -ge $scheduled) {
                Progress "BATCH EXECUTION COMPLETE: $($fin.Count)/$scheduled attempts have result.json; starting hidden scoring"
                $sc = RunAndWait @('score', $Plan) 'score'
                if ($sc -eq 0) {
                    $mc = RunAndWait @('--study', $Study, 'metrics', $batchDir, '--out', (Join-Path $Study 'report'), '--ledger', $ledgerPath) 'metrics'
                    if ($mc -ne 0) {
                        $null = RunAndWait @('--study', $Study, 'metrics', $batchDir, '--out', (Join-Path $Study 'report-preliminary'), '--ledger', $ledgerPath, '--preliminary') 'metrics-preliminary'
                        Progress "official report refused (exit $mc): wrote report-preliminary (PRELIMINARY); see $ops for the listed problems"
                    } else { Progress "OFFICIAL REPORT written to $Study\report" }
                } else { Progress "score exited $sc; see $ops (score-*.log)" }
                $st.done = $true
            } elseif ($code -eq 3) {
                $st.foreignWaits++
                if ($st.foreignWaits -le 12) { Progress "batch deferred: foreign model loaded on the user's Ollama app (11434); relaunching in 10 min"; Start-Sleep 600; if (-not (Test-Path (Join-Path $ops 'watchdog.pause'))) { $run = LaunchRun } }
                else { $blocked = $true; Progress 'BLOCKER: the user Ollama app kept a model loaded for hours; unload it and relaunch' }
            } else {
                if (Recovery 'exit') {
                    Progress "batch process exited (code $code) with $($fin.Count)/$scheduled finished; relaunching (resume) in 2 min"
                    Start-Sleep 120; if (OllamaOk) { $run = LaunchRun } else { RestartOllama; $run = LaunchRun }
                } else { $blocked = $true; Progress "BLOCKER: batch exited repeatedly without progress (last code $code); see $ops" }
            }
        }
    }

    if (((Get-Date) - $st.lastProgress).TotalMinutes -ge $ProgressMinutes) {
        $byCond = ($fin | ForEach-Object { if ($_.Name -match '-([A-E])-s\d+$') { $matches[1] } } | Group-Object | Sort-Object Name | ForEach-Object { "$($_.Name)=$($_.Count)" }) -join ' '
        $bySeed = ($fin | ForEach-Object { if ($_.Name -match '-s(\d+)$') { $matches[1] } } | Group-Object | Sort-Object Name | ForEach-Object { "$($_.Name)=$($_.Count)" }) -join ' '
        $infra = @($seen.Values | Where-Object { $_ -like 'infra:*' -or $_ -eq 'frontier' -or $_ -eq 'budget' }).Count
        $current = Get-ChildItem $batchDir -Directory -ErrorAction SilentlyContinue | Where-Object { $_.Name -match '-s\d+$' -and -not (Test-Path (Join-Path $_.FullName 'result.json')) } | Select-Object -ExpandProperty Name
        $free = [math]::Round((Get-PSDrive E).Free / 1GB, 1)
        $docker = DockerOk
        Progress ("finished={0}/{1} [{2}] seeds[{3}] infra_like={4} running={5} current={6} | {7} | ollama11435={8} docker={9} diskE={10}GB paused={11} blocked={12} done={13}" -f `
            $fin.Count, $scheduled, $byCond, $bySeed, $infra, (@(RunProcs).Count -gt 0), ($current -join ','), (LedgerSummary), $ollama, $docker, $free, $paused, $blocked, $st.done)
        $st.lastProgress = Get-Date
    }
    @{ utc = (Now); pid = $PID; finished = $fin.Count; scheduled = $scheduled; paused = $paused; blocked = $blocked; done = $st.done;
       recoveries = $st.recoveries; run_pid = $(if ($run) { $run.Id } else { $null }) } | ConvertTo-Json -Compress | Set-Content -Encoding utf8 $stateFile
    if ($st.done) { Log 'done: watchdog exiting'; break }
    Start-Sleep $PollSeconds
}
