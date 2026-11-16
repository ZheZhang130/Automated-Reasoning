$ErrorActionPreference = 'Stop'
. "$PSScriptRoot\env.ps1"
[Environment]::SetEnvironmentVariable('OLLAMA_MODELS', $env:OLLAMA_MODELS, 'User')
try {
    $null = Invoke-RestMethod 'http://127.0.0.1:11435/api/version'
    Write-Host 'Project endpoint already running. Verify its startup log before pulling.'
    exit 0
} catch {}
$env:OLLAMA_NO_CLOUD = '1'
$env:OLLAMA_NOPRUNE = '1'
New-Item -ItemType Directory -Force "$env:CSC2108_ROOT\logs" | Out-Null
Start-Process -FilePath (Get-Command ollama).Source -ArgumentList 'serve' -WindowStyle Hidden `
    -RedirectStandardOutput "$env:CSC2108_ROOT\logs\ollama-project.stdout.log" `
    -RedirectStandardError "$env:CSC2108_ROOT\logs\ollama-project.stderr.log"
