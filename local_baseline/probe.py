"""Connection/protocol checks only; never executes model actions on the host."""
import argparse
import json
import os
import subprocess
import time
from pathlib import Path

os.environ.setdefault("MSWEA_MODEL_RETRY_STOP_AFTER_ATTEMPT", "1")
os.environ.setdefault("MSWEA_SILENT_STARTUP", "1")
from minisweagent.models.litellm_model import LitellmModel
from minisweagent.models.litellm_textbased_model import LitellmTextbasedModel
import requests

ROOT = Path(__file__).resolve().parent
ENDPOINT = "http://127.0.0.1:11435"
PROTOCOL_VERSION = "single-step-v3"


def system_prompt(protocol):
    if protocol == "native":
        return "You are a coding agent. Every response must contain exactly one bash tool call."
    return ("You operate the computer yourself by executing shell commands. "
            "Work ONE step at a time and wait for the command output before choosing the next action. "
            "Edit files yourself using noninteractive commands. "
            "Every response must contain exactly ONE command block and no additional command examples. "
            "formatted exactly like this example (including the newlines):\n"
            "```mswea_bash_command\npwd\n```\n"
            "Put your shell command on the line after mswea_bash_command. "
            "The closing triple backticks must be on a separate line. "
            "Execute the current step only. Wait for its output. "
            "You are responsible for making changes; do not ask a human to edit files. "
            "Use noninteractive file editing commands rather than an interactive editor.")


def unload_project_models():
    approved = json.loads((ROOT / "models.json").read_text())
    loaded = requests.get(ENDPOINT + "/api/ps", timeout=10).json()["models"]
    for item in loaded:
        if item["name"] not in approved:
            raise RuntimeError("Unexpected workload on the dedicated project endpoint")
        response = requests.post(ENDPOINT + "/api/generate", json={"model": item["name"], "keep_alive": 0}, timeout=30)
        response.raise_for_status()


def make_model(name, protocol="native", timeout=120):
    models = json.loads((ROOT / "models.json").read_text())
    if name not in models:
        raise ValueError("Only the three approved local models may be used")
    kwargs = dict(api_base=ENDPOINT, temperature=0.0, num_ctx=8192,
                  num_predict=2048, seed=2108, timeout=timeout, num_retries=0,
                  keep_alive="10m")
    thinking = models[name]["thinking"]
    if thinking is not None:
        kwargs["think"] = thinking
    cls = LitellmModel if protocol == "native" else LitellmTextbasedModel
    config = dict(model_name="ollama_chat/" + name, cost_tracking="ignore_errors", model_kwargs=kwargs)
    if protocol == "text":
        config["format_error_template"] = (
            "The response was rejected: found {{ actions|length }} command blocks. "
            "No command from that response was executed. Return exactly ONE command block for the current step, "
            "then wait for output. Make changes yourself with a noninteractive shell command. "
            "Use precisely this format, including newlines:\n```mswea_bash_command\npwd\n```\n"
            "Replace pwd with the one current action. Include no other command blocks.")
    return cls(**config)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--model", required=True)
    p.add_argument("--protocol", choices=["native", "text"], default="native")
    p.add_argument("--output", type=Path, required=True)
    args = p.parse_args()
    args.output.mkdir(parents=True, exist_ok=False)
    unload_project_models()
    model = make_model(args.model, args.protocol)
    messages = [model.format_message(role="system", content=system_prompt(args.protocol)),
        model.format_message(role="user", content="Produce the action to print CSC2108_CONNECTION_OK. Do not execute anything yourself.")]
    result = {"model": args.model, "protocol": args.protocol, "executed_actions": 0,
              "messages": messages, "config": model.serialize(), "protocol_version": PROTOCOL_VERSION}
    started = time.monotonic()
    try:
        result["response"] = model.query(messages)
        result["status"] = "parsed_action"
    except Exception as exc:
        result.update(status="error", error_type=type(exc).__name__, error=str(exc),
                      error_messages=getattr(exc, "messages", None))
    result["elapsed_seconds"] = time.monotonic() - started
    result["ollama_ps"] = requests.get(ENDPOINT + "/api/ps", timeout=10).json()
    result["model_metadata"] = requests.post(ENDPOINT + "/api/show", json={"model": args.model}, timeout=30).json()
    result["gpu"] = subprocess.run(["nvidia-smi", "--query-gpu=name,memory.total,memory.used,utilization.gpu", "--format=csv,noheader"], capture_output=True, text=True).stdout
    (args.output / "probe.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps({k: result[k] for k in ("model", "protocol", "status", "elapsed_seconds", "gpu")}))


if __name__ == "__main__":
    main()
