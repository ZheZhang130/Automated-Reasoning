"""Output-comparison semantics of a task, decided from its PUBLIC statement before any selection or run.

Judge 0.2.1 (``judge/container/judge.py``) implements LiveCodeBench's ``grade_stdio`` rule: strip the output
and every line, require equal line counts, and accept a line only if it is identical or both sides parse to
equal lists of Decimals. That rule is correct only when the task has exactly one acceptable output text.
Other output semantics exist in AtCoder statements:

* ``tolerance``         - "absolute or relative error ... at most 10^{-k}": a correct value printed with
                          different digits is rejected (abc392_d, pass 1);
* ``multiple_answers``  - "if there are multiple ..., print any": a correct alternative is rejected
                          (abc396_e, pass 1);
* ``case_insensitive``  - "the judge is case-insensitive": ``fennec`` for ``Fennec`` is rejected (arc192_b);
* ``interactive``       - not a stdin/stdout batch task at all.

``classify`` collects signals from several independent cues (statement sentences in every category plus a
decimal-sample heuristic). It never decides alone: any signal, any conflict and any decimal sample requires
a recorded MANUAL review (``load_review``) that cites the deciding public sentence. Only tasks whose reviewed
category is ``exact`` are eligible for an experiment scored by judge 0.2.1.
"""
import json
import re
from pathlib import Path

CATEGORIES = ('exact', 'tolerance', 'multiple_answers', 'case_insensitive', 'interactive')
SUPPORTED_BY_JUDGE_0_2_1 = frozenset({'exact'})

SIGNALS = {
    'tolerance': [
        r'(?:absolute|relative)\s+(?:or\s+(?:absolute|relative)\s+)?error',
        r'\berror\b[^.\n]{0,60}(?:does not exceed|not exceeding|at most|is at most|or less|less than|within)',
        r'within\s+an?\s+(?:absolute|relative)?\s*error', r'\bprecision\b', r'\btolerance\b'],
    'multiple_answers': [
        r'if (?:there are|there exist|multiple|several)[^.\n]{0,60}(?:multiple|several|more than one)',
        r'multiple\s+(?:valid\s+|correct\s+|optimal\s+|possible\s+)?(?:answers|solutions|ways|sequences|outputs|choices)\s+exist',
        r'if multiple solutions exist', r'any (?:one )?of them', r'\b(?:print|output|printing|outputting|report)\s+any\b',
        r'any\s+(?:such|valid|correct|optimal)\b', r'(?:is|are|will be)\s+(?:all\s+)?accepted',
        r'(?:considered|judged)\s+correct',
        # constructive tasks that never say "any" (arc195_c: "If it exists, show one example."):
        r'\b(?:show|give|print|output|find|construct|report)\s+(?:one|an|a)\s+(?:example|such|way|solution|valid|possible)',
        r'\bprint\s+such\s+an?\b', r'\bone\s+example\b', r'\b(?:an|one)\s+example\s+of\b'],
    'case_insensitive': [r'case[- ]insensitive', r'(?:uppercase|lowercase)\s+(?:or|and)\s+(?:uppercase|lowercase)',
                         r'in any (?:letter )?case\b'],
    'interactive': [r'\binteractive\b', r'\bflush\b'],
}
# A sentence that only says the tolerance rule makes the answer "considered correct" is not a
# multiple-answer signal; it is attributed to tolerance instead.
_TOLERANCE_HINT = re.compile('|'.join(SIGNALS['tolerance']), re.I)
_DECIMAL = re.compile(r'(?<![\w.])-?\d+\.\d+(?![\w.])')


def _sentences(text):
    return [s.strip() for s in re.split(r'(?<=[.!?])\s+|\n+', text) if s.strip()]


def classify(statement, sample_outputs=()):
    """Signals per category from the public statement and the public sample outputs (no hidden data)."""
    signals = {}
    for sentence in _sentences(statement):
        for category, patterns in SIGNALS.items():
            if any(re.search(p, sentence, re.I) for p in patterns):
                if category == 'multiple_answers' and _TOLERANCE_HINT.search(sentence) and not re.search(
                        r'multiple|several|any of|print any|any one', sentence, re.I):
                    continue
                signals.setdefault(category, []).append(sentence[:300])
    decimals = sorted({m for out in sample_outputs for m in _DECIMAL.findall(out)})[:5]
    if decimals:
        signals.setdefault('decimal_sample_output', []).extend(decimals)
    categories = [c for c in CATEGORIES if c in signals]
    auto = categories[0] if len(categories) == 1 else ('exact' if not categories else 'conflict')
    return {'auto_category': auto, 'signals': signals,
            'needs_review': bool(signals)}  # any cue at all, including a decimal sample, needs a person


def load_review(path):
    """Manual review file: {task_id: {'category', 'evidence', 'note'}} (public statement quotes only)."""
    data = json.loads(Path(path).read_text(encoding='utf-8'))
    reviews = data.get('reviews', data)
    for task_id, item in reviews.items():
        if item.get('category') not in CATEGORIES:
            raise ValueError(f'{task_id}: unknown reviewed category {item.get("category")!r}')
    return reviews


def decide(task_id, auto, reviews):
    """Final category: a manual review always wins; an unreviewed cue makes the task ineligible."""
    review = reviews.get(task_id)
    if review is not None:
        return review['category'], 'manual'
    if auto['needs_review']:
        return 'unreviewed', 'auto-flagged'
    return 'exact', 'auto-no-signal'


def eligible_for_judge_0_2_1(category):
    return category in SUPPORTED_BY_JUDGE_0_2_1
