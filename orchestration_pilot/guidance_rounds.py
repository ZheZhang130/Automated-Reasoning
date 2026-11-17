"""Guidance schedule and public feedback for one task execution."""
from dataclasses import dataclass
from typing import Optional

DEFAULT_SCHEDULE = ("plan", "diagnosis")
GUIDANCE_KINDS = frozenset(("plan", "contract", "diagnosis"))


def validate_schedule(schedule):
    schedule = tuple(schedule)
    if any(kind not in GUIDANCE_KINDS for kind in schedule):
        raise ValueError("Guidance kinds must be plan, contract, or diagnosis")
    return schedule


def failure_feedback(candidate, result, trace, *, actions_left, repairs_left):
    """Build an evidence packet from public observations in the current run."""
    return {
        "candidate_code": candidate,
        "public_failure": result,
        "recent_events": [
            {key: value for key, value in event.items() if key != "code"}
            for event in trace[-12:]
        ],
        "state": {"actions_left": actions_left, "repairs_left": repairs_left},
    }


@dataclass
class GuidanceRounds:
    schedule: tuple
    used: int = 0
    last_failed_candidate: Optional[str] = None

    def upfront(self):
        if not self.schedule or self.schedule[0] == "diagnosis":
            return None
        return self._consume()

    def after_failure(self, candidate):
        if self.used >= len(self.schedule) or candidate == self.last_failed_candidate:
            return None
        self.last_failed_candidate = candidate
        return self._consume()

    def _consume(self):
        self.used += 1
        return self.schedule[self.used - 1]
