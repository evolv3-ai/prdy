"""Query building and PRD candidate heuristics. Pure functions only."""
from __future__ import annotations

import re
from collections.abc import Sequence

from prdy.grade import strip_fences


def build_query(
    keywords: str,
    topics: Sequence[str] = (),
    stars: str | None = None,
    language: str | None = None,
    pushed: str | None = None,
    org: str | None = None,
) -> str:
    """Keywords verbatim, then one GitHub search qualifier per filter."""
    parts = [keywords.strip()]
    parts += [f"topic:{t}" for t in topics if t]
    for name, value in (("stars", stars), ("language", language), ("pushed", pushed), ("org", org)):
        if value:
            parts.append(f"{name}:{value}")
    return " ".join(p for p in parts if p)


MAX_BLOB_SIZE = 1_000_000

_PRD_EXTENSIONS = {".md", ".mdx", ".markdown", ".rst", ".txt"}
_PRD_WORD = re.compile(r"(?<![a-z0-9])prd(?![a-z0-9])")
_REQUIREMENT_NAMES = ("product-requirements", "product_requirements", "requirements")
_PRD_DIRS = {"prd", "prds"}


def is_prd_path(path: str) -> bool:
    """Case-insensitive path heuristic from the spec."""
    lowered = path.lower()
    dirs, _, name = lowered.rpartition("/")
    stem, dot, ext = name.rpartition(".")
    if not dot or f".{ext}" not in _PRD_EXTENSIONS:
        return False
    if name == "requirements.txt":
        return False
    if _PRD_WORD.search(stem):
        return True
    if any(segment in _PRD_DIRS for segment in dirs.split("/")):
        return True
    return any(token in stem for token in _REQUIREMENT_NAMES)


SNIFF_BYTES = 2048
_LICENSE_LINE = re.compile(r"licen[cs]e|copyright|©|spdx-license-identifier|cc by", re.IGNORECASE)
_H1 = re.compile(r"^#[ \t]+(.+?)[ \t]*#*[ \t]*$", re.MULTILINE)


def looks_like_prd(head: bytes) -> bool:
    """True when the first 2 KB mention 'requirement' or 'prd' (case-insensitive)."""
    text = head[:SNIFF_BYTES].decode("utf-8", errors="replace").lower()
    return "requirement" in text or "prd" in text


def find_inline_license(text: str) -> str | None:
    """First line mentioning a license/copyright marker, trimmed to 200 chars."""
    for line in text.splitlines():
        if _LICENSE_LINE.search(line):
            return line.strip()[:200]
    return None


def extract_title(text: str, fallback: str) -> str:
    """First ATX H1, else the fallback (the filename)."""
    match = _H1.search(strip_fences(text))
    return match.group(1).strip() if match else fallback
