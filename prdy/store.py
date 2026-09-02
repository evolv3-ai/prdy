"""Corpus layout, sidecars, and the JSONL index."""
from __future__ import annotations

import json
import os
from dataclasses import asdict, dataclass, field, fields
from pathlib import Path

INDEX_NAME = "index.jsonl"


@dataclass
class Row:
    repo: str
    path: str
    url: str | None = None
    html_url: str | None = None
    blob_sha: str | None = None
    default_branch: str | None = None
    fetched_at: str | None = None
    stars: int | None = None
    topics: list[str] = field(default_factory=list)
    repo_license: str | None = None
    inline_license: str | None = None
    size: int | None = None
    title: str | None = None
    grade_score: int | None = None
    grade_letter: str | None = None
    grade_reasons: list[str] = field(default_factory=list)
    llm_score: int | None = None
    llm_critique: str | None = None
    llm_model: str | None = None
    skipped: str | None = None

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "Row":
        known = {f.name for f in fields(cls)}
        return cls(**{k: v for k, v in data.items() if k in known})


def index_path(out: Path) -> Path:
    return Path(out) / INDEX_NAME


def read_index(out: Path) -> list[Row]:
    path = index_path(out)
    if not path.exists():
        return []
    rows = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            rows.append(Row.from_dict(json.loads(line)))
    return rows


def find_row(rows: list[Row], repo: str, path: str) -> Row | None:
    for row in rows:
        if row.repo == repo and row.path == path:
            return row
    return None


def upsert(out: Path, row: Row) -> None:
    """Rewrite index.jsonl with `row` replacing any row with the same (repo, path)."""
    rows = read_index(out)
    for i, existing in enumerate(rows):
        if existing.repo == row.repo and existing.path == row.path:
            rows[i] = row
            break
    else:
        rows.append(row)
    target = index_path(out)
    target.parent.mkdir(parents=True, exist_ok=True)
    tmp = target.with_suffix(".jsonl.tmp")
    with tmp.open("w", encoding="utf-8") as fh:
        for r in rows:
            fh.write(json.dumps(r.to_dict(), ensure_ascii=False) + "\n")
    os.replace(tmp, target)


def repo_dir(out: Path, repo: str) -> Path:
    return Path(out) / repo.replace("/", "__")


def document_paths(out: Path, repo: str, path: str) -> tuple[Path, Path]:
    """`docs/prd/login.txt` -> (`docs__prd__login.md`, `docs__prd__login.meta.json`)."""
    flat = path.replace("/", "__")
    stem = flat.rsplit(".", 1)[0] if "." in flat.rsplit("__", 1)[-1] else flat
    folder = repo_dir(out, repo)
    return folder / f"{stem}.md", folder / f"{stem}.meta.json"


def write_document(out: Path, row: Row, text: str) -> Path:
    md, meta = document_paths(out, row.repo, row.path)
    md.parent.mkdir(parents=True, exist_ok=True)
    md.write_text(text, encoding="utf-8")
    meta.write_text(json.dumps(row.to_dict(), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return md
