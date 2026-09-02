"""Query building and PRD candidate heuristics. Pure functions only."""
from __future__ import annotations

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
