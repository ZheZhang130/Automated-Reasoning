$env:OLLAMA_MODELS = 'E:\OllamaModels'
$env:OLLAMA_HOST = '127.0.0.1:11435'
$env:CSC2108_ROOT = 'E:\CSC2108Local'
$env:UV_CACHE_DIR = "$env:CSC2108_ROOT\cache\uv"
$env:PIP_CACHE_DIR = "$env:CSC2108_ROOT\cache\pip"
$env:HF_HOME = "$env:CSC2108_ROOT\cache\huggingface"
$env:HF_DATASETS_CACHE = "$env:HF_HOME\datasets"
$env:TIKTOKEN_CACHE_DIR = "$env:CSC2108_ROOT\cache\tiktoken"
$env:MSWEA_GLOBAL_CONFIG_DIR = "$env:CSC2108_ROOT\config"
$env:TEMP = "$env:CSC2108_ROOT\tmp"
$env:TMP = $env:TEMP
$env:PYTHONUTF8 = '1'
$env:LITELLM_LOCAL_MODEL_COST_MAP = 'True'
@($env:TEMP, $env:HF_HOME, $env:PIP_CACHE_DIR, $env:TIKTOKEN_CACHE_DIR, $env:MSWEA_GLOBAL_CONFIG_DIR) | ForEach-Object {
    New-Item -ItemType Directory -Force -Path $_ | Out-Null
}
