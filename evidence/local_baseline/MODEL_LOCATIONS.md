# Model locations and access — verified 2026-11-16

All three project models are installed in **E:\OllamaModels** and served locally by **Ollama 0.40.16** using the RTX 4080 SUPER. Their manifest digests still match the completed pilot. All are Q4_K_M quantizations.

The Ollama app's saved folder had become `E:\OllamaModels\ollama`, an empty subdirectory. It was corrected to `E:\OllamaModels` and the idle app restarted. The persistent account `OLLAMA_MODELS` already matched that root. No weights were moved, deleted, or downloaded again. The previous app-folder value is saved in `E:\CSC2108Local\artifacts\storage-recheck-20261116\app-path-before.json`.

| Model | Total installed size | Manifest | Main weights |
| --- | ---: | --- | --- |
| qwen3.5:9b | 6.55 GB | [manifest](E:/OllamaModels/manifests/registry.ollama.ai/library/qwen3.5/9b) | [5.63 GB weights](E:/OllamaModels/blobs/sha256-02d45dc1cf451ba2475ac33b301c2dd8f985abe4c182ce04a1f2f5bf0260278d) |
| qwen2.5-coder:14b | 8.99 GB | [manifest](E:/OllamaModels/manifests/registry.ollama.ai/library/qwen2.5-coder/14b) | [8.99 GB weights](E:/OllamaModels/blobs/sha256-ac9bc7a69dab38da1c790838955f1293420b55ab555ef6b4615efa1c1507b1ed) |
| qwen2.5-coder:7b | 4.68 GB | [manifest](E:/OllamaModels/manifests/registry.ollama.ai/library/qwen2.5-coder/7b) | [4.68 GB weights](E:/OllamaModels/blobs/sha256-60e05f2100071479f596b964f89f510f057ce397ea22f2833a0cfe029bfc2463) |

Qwen3.5 also includes a [0.92 GB vision projector](E:/OllamaModels/blobs/sha256-f836f08f921193f4d6b6a6952dba0a6fb116759d26a757bcb395d570d73976ca). Ollama stores weights as content-addressed files in `E:\OllamaModels\blobs`; the manifests map model names to those files.

Full main weight paths, for copying into Explorer:

```text
Qwen3.5 9B:
E:\OllamaModels\blobs\sha256-02d45dc1cf451ba2475ac33b301c2dd8f985abe4c182ce04a1f2f5bf0260278d

Qwen2.5-Coder 14B:
E:\OllamaModels\blobs\sha256-ac9bc7a69dab38da1c790838955f1293420b55ab555ef6b4615efa1c1507b1ed

Qwen2.5-Coder 7B:
E:\OllamaModels\blobs\sha256-60e05f2100071479f596b964f89f510f057ce397ea22f2833a0cfe029bfc2463
```

## Access

- **Ollama desktop app / ordinary CLI:** `http://127.0.0.1:11434`. The app now sees the same three models.
- **Project runner:** mini-SWE-agent → LiteLLM `ollama_chat/<model name>` → dedicated Ollama server at `http://127.0.0.1:11435` → local NVIDIA GPU.
- Both servers use the same existing E: files. The project does not use LM Studio, a frontier provider, or paid inference APIs.

For the ordinary CLI, in a terminal without the project's OLLAMA_HOST override:

```powershell
ollama list
ollama run qwen3.5:9b
ollama run qwen2.5-coder:14b
ollama run qwen2.5-coder:7b
```

Fresh checks passed for each model through both endpoints: the app endpoint generated the requested fixed response; the project endpoint produced an action accepted by mini-SWE-agent's text parser. API snapshots showed full GPU residency at an 8,192-token context. These checks verify loading, inference and action parsing; the earlier coding-pilot outcomes remain unchanged.

Evidence: `E:\CSC2108Local\artifacts\storage-recheck-20261116` contains manifest/blob-size verification, both endpoint inventories, complete inference responses, project protocol probes and GPU snapshots.
