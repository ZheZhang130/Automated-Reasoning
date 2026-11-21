"""Paper-inspired semi-formal contracts generated solely from public requirements."""
import hashlib
import json
from pathlib import Path

from planning_frontier.planner import OllamaPlanner, FrontierPlanner

DEFAULT_CONTRACT_OUTPUT_TOKENS = 3000
DEFAULT_CONTRACT_CONTEXT_TOKENS = 8192

PROMPT = """Document a semi-formal behavioral contract for the supplied programming
task. Use exactly these headings:
## Description
Summarize intended externally observable behavior.
## Preconditions
Assign PRE-1 etc to input/state requirements. Mark each Unverified.
## Postconditions
Assign POST-1 etc to guaranteed outputs and state transitions. Mark each Unverified.
Cover boundary cases, multiplicity, ordering and invariants only when relevant.
## Test suggestions
Suggest behavioral checks referencing PRE/POST IDs. Do not claim tests were run.
## Unspecified behavior
List behavior outside the task's guarantees, without inventing validation rules.
Use natural language. Do not provide code, pseudocode, algorithms or data structures.
No existing implementation or tests have been inspected. Do not mark any condition
Tested or Verified. Keep the contract within about 400 words.
"""


class OllamaContract(OllamaPlanner):
    def __init__(self, endpoint, model, context=DEFAULT_CONTRACT_CONTEXT_TOKENS, output_tokens=DEFAULT_CONTRACT_OUTPUT_TOKENS):
        super().__init__(endpoint, model, context, output_tokens=output_tokens)
        self.prompt = PROMPT


class FrontierContract(FrontierPlanner):
    def __init__(self, model, output_tokens=DEFAULT_CONTRACT_OUTPUT_TOKENS):
        super().__init__(model, output_tokens=output_tokens)
        self.prompt = PROMPT


class SavedContract:
    """Task-bound replay for Codex-authored contract smoke tests."""
    def __init__(self, path):
        self.path = Path(path).resolve(strict=True)
        raw = self.path.read_bytes()
        self.source_sha256 = hashlib.sha256(raw).hexdigest()
        self.artifact = json.loads(raw)
        for field in ("text", "statement_sha256", "contract_prompt", "author"):
            if not isinstance(self.artifact.get(field), str) or not self.artifact[field].strip():
                raise ValueError("Saved contract requires " + field)
        self.model = self.artifact["author"]
        self.prompt = self.artifact["contract_prompt"]

    def __call__(self, statement, timeout):
        if hashlib.sha256(statement.encode()).hexdigest() != self.artifact["statement_sha256"]:
            raise ValueError("Saved contract belongs to a different task statement")
        if timeout <= 0:
            raise TimeoutError("No remaining guidance time")
        return self.artifact["text"], None

    def provenance(self):
        return {"path": str(self.path), "source_sha256": self.source_sha256,
                "author": self.model, "provider_calls_in_runner": 0,
                "note": "Codex-authored contract replay. Authoring latency and cost unavailable."}


def generate_contract(provider, statement, timeout):
    text, usage = provider(statement, timeout)
    headings = ("## Description", "## Preconditions", "## Postconditions",
                "## Test suggestions", "## Unspecified behavior")
    if not isinstance(text, str) or not all(h in text for h in headings):
        raise ValueError("Contract is missing a required specification section")
    result = {"text": text, "usage": usage, "system_prompt": provider.prompt,
              "verification": "Unverified; generation does not prove correctness"}
    if isinstance(provider, SavedContract):
        result["provenance"] = provider.provenance()
    return result
