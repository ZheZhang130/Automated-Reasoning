# Overnight ops helper: run `python -m evaluation` (or another module) with the project environment.
#   & E:\CSC2108Local\ops\ev.ps1 <study-root> status <plan>
#   & E:\CSC2108Local\ops\ev.ps1 <study-root> module=local_agent verify
# No param block on purpose: every argument after the study root is passed through verbatim (e.g. --out).
$Study = $args[0]
$rest = @($args | Select-Object -Skip 1)
$Module = 'evaluation'
if ($rest.Count -gt 0 -and "$($rest[0])" -like 'module=*') { $Module = "$($rest[0])".Substring(7); $rest = @($rest | Select-Object -Skip 1) }
if (-not $Study) { throw 'usage: ev.ps1 <study-root> [module=NAME] ARGS...' }
$repo = 'E:\VS Code Projects\CSC2108Project\Automated-Reasoning'
. "$repo\local_baseline\env.ps1"
$env:CSC2108_STUDY_ROOT = $Study
$env:LITELLM_LOCAL_MODEL_COST_MAP = 'True'
$env:PYTHONIOENCODING = 'utf-8'
$env:CSC2108_LCB_SHARD = 'E:\CSC2108Local\eval-v2\cache\test6.jsonl'
Set-Location $repo
& 'E:\CSC2108Local\.venv\Scripts\python.exe' -m $Module @rest
exit $LASTEXITCODE
