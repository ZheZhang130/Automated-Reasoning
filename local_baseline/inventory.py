"""Record installed versions, endpoint metadata, and physical E: blob evidence."""
import argparse
import importlib.metadata
import json
import os
import re
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import urlopen

ENDPOINT = "http://127.0.0.1:11435"
STORAGE = Path("E:/OllamaModels")


def get(route):
    with urlopen(ENDPOINT + route, timeout=15) as response:
        return json.load(response)


def storage_evidence():
    log = Path("E:/CSC2108Local/logs/ollama-project.stderr.log").read_text(encoding="utf-8")
    configs = [line for line in log.splitlines() if 'msg="server config"' in line]
    line = configs[-1]
    match = re.search(r"OLLAMA_MODELS:(.*?) OLLAMA_", line)
    effective = Path(match.group(1).replace("\\\\", "\\")) if match else None
    if effective != STORAGE or "127.0.0.1:11435" not in line:
        raise RuntimeError("Project Ollama startup storage/port not verified")
    if STORAGE.resolve().drive.upper() != "E:" or STORAGE.is_symlink():
        raise RuntimeError("Model storage must resolve directly onto E:")
    models = get("/api/tags")["models"]
    manifests = []
    for model in models:
        name, tag = model["name"].split(":", 1)
        path = STORAGE / "manifests/registry.ollama.ai/library" / name / tag
        manifest = json.loads(path.read_text())
        layers = [manifest["config"], *manifest["layers"]]
        files = []
        for layer in layers:
            blob = STORAGE / "blobs" / layer["digest"].replace(":", "-")
            actual = blob.stat().st_size
            if actual != layer["size"]:
                raise RuntimeError("Blob size differs from manifest")
            files.append({"path": str(blob), "bytes": actual, "digest": layer["digest"]})
        manifests.append({"model": model, "manifest": str(path), "blobs": files})
    return {"effective_path": str(effective), "startup_log": str(Path("E:/CSC2108Local/logs/ollama-project.stderr.log")),
            "startup_config": line, "models": manifests}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--output", type=Path, default=Path("E:/CSC2108Local/artifacts/environment.json"))
    args = p.parse_args()
    record = {"captured_utc": datetime.now(timezone.utc).isoformat(),
              "python": subprocess.run([os.sys.executable, "--version"], capture_output=True, text=True).stdout.strip(),
              "versions": {d.metadata["Name"]: d.version for d in importlib.metadata.distributions()},
              "ollama": get("/api/version"), "storage": storage_evidence(),
              "disk": {drive: dict(zip(("total", "used", "free"), shutil.disk_usage(drive))) for drive in ("C:/", "E:/")},
              "gpu": subprocess.run(["nvidia-smi", "--query-gpu=name,memory.total,driver_version", "--format=csv,noheader"], capture_output=True, text=True).stdout.strip()}
    result = subprocess.run(["docker", "info", "--format", "{{json .}}"], capture_output=True, text=True, timeout=20)
    if result.returncode == 0:
        info = json.loads(result.stdout)
        settings = json.loads((Path(os.environ["APPDATA"]) / "Docker/settings-store.json").read_text())
        disk_root = Path(settings["CustomWslDistroDir"])
        record["docker"] = {"version": info["ServerVersion"], "guest_data_root": info["DockerRootDir"],
                            "wsl_data_root": str(disk_root),
                            "virtual_disks": [{"path": str(p), "bytes": p.stat().st_size} for p in disk_root.rglob("*.vhdx")],
                            "wsl_config": (Path.home() / ".wslconfig").read_text()}
    else:
        record["docker"] = {"status": "unavailable", "error": result.stderr}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(record, indent=2), encoding="utf-8")
    print(json.dumps({"output": str(args.output), "storage": record["storage"]["effective_path"],
                      "models": [m["model"]["name"] for m in record["storage"]["models"]], "gpu": record["gpu"]}))


if __name__ == "__main__":
    main()
