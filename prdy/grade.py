"""Deterministic PRD rubric. Points sum to 100."""
from __future__ import annotations

import re
from dataclasses import dataclass, field


@dataclass(frozen=True)
class Grade:
    score: int
    letter: str
    reasons: list[str] = field(default_factory=list)


# The one synonym table. key -> (label used in reasons, regex over a heading's text)
SECTIONS: dict[str, tuple[str, str]] = {
    "problem": ("problem", r"\b(problem|background|context|motivation)\b"),
    "goals": ("goals", r"(?<!non-)(?<!non )\b(goals?|objectives?)\b"),
    "users": ("users", r"\b(users?|personas?|audience|customers?|stakeholders?)\b(?!\s+stor)"),
    "requirements": ("requirements", r"\b(requirements?|user stor(?:y|ies)|features?|functional)\b"),
    "success-metrics": ("success metrics", r"\b(success metrics?|metrics?|kpis?|key results?)\b"),
    "non-goals": ("non-goals", r"\b(non[- ]?goals?|out of scope|not in scope)\b"),
    "timeline": ("timeline", r"\b(timeline|milestones?|roadmap|schedule)\b"),
    "open-questions": ("open questions", r"\b(open questions?|risks?|questions?)\b"),
}
_SECTION_PATTERNS = {key: re.compile(rx, re.IGNORECASE) for key, (_, rx) in SECTIONS.items()}

_ATX = re.compile(r"^(#{1,6})[ \t]+(.+?)[ \t]*#*[ \t]*$")
_SETEXT_UNDERLINE = re.compile(r"^(=+|-+|~+|\^+|\*+)$")
_LIST_OR_TABLE_START = re.compile(r"^\s*(?:[-*+]\s|\d+[.)]\s|\|)")
_BOLD_LEAD = re.compile(r"^\s*(?:\*\*|__)([^*_\n]{1,80}?)(?:\*\*|__)")


def find_headings(text: str) -> list[tuple[int, str]]:
    """ATX headings at any level plus setext headings (= is level 1, others level 2)."""
    lines = text.splitlines()
    found: list[tuple[int, str]] = []
    for i, line in enumerate(lines):
        atx = _ATX.match(line)
        if atx:
            found.append((len(atx.group(1)), atx.group(2).strip()))
            continue
        if i + 1 >= len(lines) or not line.strip() or _LIST_OR_TABLE_START.match(line):
            continue
        underline = lines[i + 1].strip()
        if len(underline) >= 3 and _SETEXT_UNDERLINE.match(underline):
            found.append((1 if underline[0] == "=" else 2, line.strip()))
    return found


def find_bold_leads(text: str) -> list[str]:
    """Lines that open with a bold phrase, e.g. '**Problem:** ...'."""
    return [m.group(1).strip().rstrip(":") for line in text.splitlines() if (m := _BOLD_LEAD.match(line))]


def find_sections(text: str) -> set[str]:
    titles = [title for _, title in find_headings(text)] + find_bold_leads(text)
    return {key for key, rx in _SECTION_PATTERNS.items() if any(rx.search(t) for t in titles)}
