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


_LIST_ITEM = re.compile(r"^\s*(?:[-*+]|\d+[.)])\s+\S")
_TABLE_SEPARATOR = re.compile(r"^\s*\|?\s*:?-{3,}:?\s*(?:\|\s*:?-{3,}:?\s*)+\|?\s*$")
_ISO_DATE = re.compile(r"\b\d{4}-\d{2}-\d{2}\b")
_MONTH_YEAR = re.compile(
    r"\b(?:jan|feb|mar|apr|may|jun|jul|aug|sep|sept|oct|nov|dec)[a-z]*\.?,?\s+\d{4}\b",
    re.IGNORECASE,
)
_OWNER_LINE = re.compile(
    r"^\s*(?:[-*+]\s+|\|\s*)?(?:\*\*|__)?\s*"
    r"(?:authors?|owners?|status|dri|pm|product managers?|created by|maintainers?)"
    r"\s*(?:\*\*|__)?\s*[:|]",
    re.IGNORECASE | re.MULTILINE,
)

RUBRIC_TEXT = """\
| Check | Points | How |
|---|---|---|
| Sections present, 8 x 8 | 64 | Headings or bold lead-ins for: problem/background; goals/objectives; users/personas; requirements/user stories; success metrics/KPIs; non-goals/out of scope; timeline/milestones; open questions/risks |
| Length band | 12 | Under 200 words 0; 200-600 words 6; 600-4000 words 12; over 4000 words 8 |
| Heading structure | 8 | At least three headings using at least two levels |
| Lists or tables | 8 | At least one bullet list and one table, or two lists |
| Ownership signals | 8 | A date (4 points) and an author/owner/status line (4 points) |
Total: 100. Letters: A >= 85, B >= 70, C >= 55, D >= 40, F below.
"""


def word_count(text: str) -> int:
    return len(re.findall(r"\S+", text))


def count_lists(text: str) -> int:
    """Number of contiguous list runs. Blank lines keep a run open; a paragraph closes it."""
    runs, in_list = 0, False
    for line in text.splitlines():
        if _LIST_ITEM.match(line):
            if not in_list:
                runs += 1
                in_list = True
        elif line.strip() and not line[0].isspace():
            in_list = False
    return runs


def count_tables(text: str) -> int:
    return sum(1 for line in text.splitlines() if _TABLE_SEPARATOR.match(line))


def has_date(text: str) -> bool:
    return bool(_ISO_DATE.search(text) or _MONTH_YEAR.search(text))


def has_owner_line(text: str) -> bool:
    return bool(_OWNER_LINE.search(text))


def letter_for(score: int) -> str:
    for floor, letter in ((85, "A"), (70, "B"), (55, "C"), (40, "D")):
        if score >= floor:
            return letter
    return "F"


def grade(text: str) -> Grade:
    score = 0
    reasons: list[str] = []

    found = find_sections(text)
    for key, (label, _) in SECTIONS.items():
        if key in found:
            score += 8
        else:
            reasons.append(f"no {label} section")

    words = word_count(text)
    if words < 200:
        reasons.append("under 200 words")
    elif words < 600:
        score += 6
        reasons.append("between 200 and 600 words")
    elif words <= 4000:
        score += 12
    else:
        score += 8
        reasons.append("over 4000 words")

    headings = find_headings(text)
    if len(headings) >= 3 and len({level for level, _ in headings}) >= 2:
        score += 8
    else:
        reasons.append("fewer than three headings across two levels")

    lists, tables = count_lists(text), count_tables(text)
    if (lists >= 1 and tables >= 1) or lists >= 2:
        score += 8
    else:
        reasons.append("needs a list and a table, or two lists")

    if has_date(text):
        score += 4
    else:
        reasons.append("no date")
    if has_owner_line(text):
        score += 4
    else:
        reasons.append("no author, owner, or status line")

    return Grade(score=score, letter=letter_for(score), reasons=reasons)
