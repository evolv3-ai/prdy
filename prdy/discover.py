"""Query building and PRD candidate heuristics. Pure functions only."""
from __future__ import annotations

import re
from collections.abc import Sequence


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
