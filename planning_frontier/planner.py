"""Single-call PlanSearch-inspired guidance, with no execution feedback input."""
import hashlib
import json
from urllib.request import Request, urlopen
from pathlib import Path

PROMPT = """You are a programming problem planner. Produce a natural-language guide
with exactly these headings:
## Observations
Give numbered, useful observations derived from the problem specification.
## Solution sketch
Describe one coherent algorithm as numbered steps. Before each step quote the
relevant observation exactly, then explain how that observation supports the step.
Cover edge cases and time/space complexity in the sketch.
Return prose only, without Python implementation or command blocks.
The guide will be implemented by a separate coding agent.
"""

COMPACT_PROMPT = """Write a concise implementation guide for a separate coding agent.
Use at most 250 words total. Do not restate the problem or provide code.
Use exactly these headings:
## Observations
Give at most three numbered observations, each one short sentence.
## Solution sketch
Give at most four short numbered steps. Quote a short relevant phrase from
an observation before each step. Name the algorithm and essential state,
explain update/query behavior and edge cases, and end with one complexity line.
Choose one approach. Do not brainstorm alternatives or give examples.
"""


class OllamaPlanner:
    def __init__(self, endpoint, model, context=4096, compact=False, output_tokens=1200):
        if output_tokens < 1 or context <= output_tokens:
            raise ValueError("Planning context must exceed output allowance")
        self.output_tokens = output_tokens
        self.last_response = None
        self.endpoint, self.model, self.context = endpoint.rstrip("/"), model, context
        self.prompt = COMPACT_PROMPT if compact else PROMPT

    def __call__(self, statement, timeout):
        request = Request(self.endpoint + "/api/chat", headers={"Content-Type": "application/json"},
                          data=json.dumps({
                              "model": self.model, "stream": False, "think": False,
                              "messages": [{"role": "system", "content": self.prompt},
                                           {"role": "user", "content": statement}],
                              "options": {"num_ctx": self.context, "num_predict": self.output_tokens, "temperature": 0.2},
                          }).encode())
        with urlopen(request, timeout=timeout) as response:
            result = json.load(response)
        self.last_response = result
        if result.get("done_reason") == "length":
            raise ValueError("Planning response was truncated")
        return result["message"]["content"], {
            "prompt_tokens": result.get("prompt_eval_count"),
            "completion_tokens": result.get("eval_count"), "cost_usd": None}


class FrontierPlanner:
    def __init__(self, model, compact=False, output_tokens=None):
        self.model = model
        self.output_tokens = output_tokens or (1200 if compact else 1600)
        self.last_response = None
        self.prompt = COMPACT_PROMPT if compact else PROMPT

    def __call__(self, statement, timeout):
        import litellm
        response = litellm.completion(
            model=self.model, messages=[{"role": "system", "content": self.prompt},
                                       {"role": "user", "content": statement}],
            max_tokens=self.output_tokens, timeout=timeout, num_retries=0)
        self.last_response = response.model_dump(mode="json")
        if response.choices[0].finish_reason == "length":
            raise ValueError("Planning response was truncated")
        usage = response.usage
        try:
            cost = litellm.completion_cost(completion_response=response)
        except Exception:
            cost = None
        return response.choices[0].message.content, {
            "prompt_tokens": usage.prompt_tokens if usage else None,
            "completion_tokens": usage.completion_tokens if usage else None,
            "cost_usd": cost}



class SavedPlan:
    """Replay a separately authored plan only for its original public statement."""
    def __init__(self, path):
        self.path = Path(path).resolve(strict=True)
        raw = self.path.read_bytes()
        self.source_sha256 = hashlib.sha256(raw).hexdigest()
        self.artifact = json.loads(raw)
        for field in ("text", "statement_sha256", "planning_prompt", "author"):
            if not isinstance(self.artifact.get(field), str) or not self.artifact[field].strip():
                raise ValueError("Saved plan requires nonempty " + field)
        self.model = self.artifact["author"]
        self.prompt = self.artifact["planning_prompt"]

    def __call__(self, statement, timeout):
        digest = hashlib.sha256(statement.encode()).hexdigest()
        if digest != self.artifact["statement_sha256"]:
            raise ValueError("Saved plan belongs to a different task statement")
        if timeout <= 0:
            raise TimeoutError("No remaining planning time")
        return self.artifact["text"], None

    def provenance(self):
        return {"path": str(self.path), "source_sha256": self.source_sha256,
                "author": self.model, "provider_calls_in_runner": 0,
                "note": "Separately authored Codex plan replay; cost and generation latency unavailable."}


def generate_plan(planner, statement, timeout):
    text, usage = planner(statement, timeout)
    if not isinstance(text, str) or not all(
        heading in text for heading in ("## Observations", "## Solution sketch")
    ):
        raise ValueError("Plan must contain Observations and Solution sketch sections")
    result = {"text": text, "usage": usage, "system_prompt": getattr(planner, "prompt", PROMPT)}
    if isinstance(planner, SavedPlan):
        result["provenance"] = planner.provenance()
    return result
