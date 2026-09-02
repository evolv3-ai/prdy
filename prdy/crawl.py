"""The crawl loop: search -> tree -> filter -> fetch -> grade -> store. No printing."""
from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import quote

from prdy import discover, store
from prdy.github import GitHubClient, GitHubError, SkipRepo
from prdy.grade import grade
from prdy.llm import LlmGrade

Grader = Callable[[str], LlmGrade]


@dataclass
class CrawlSummary:
    repos: int = 0
    candidates: int = 0
    saved: int = 0
    skipped: int = 0
    unchanged: int = 0
    top: list[store.Row] = field(default_factory=list)
    error: str | None = None


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def run_crawl(
    client: GitHubClient,
    query: str,
    limit: int,
    out: Path,
    llm_grader: Grader | None = None,
    now: Callable[[], str] = utc_now,
) -> CrawlSummary:
    out = Path(out)
    summary = CrawlSummary()
    index = {(r.repo, r.path): r for r in store.read_index(out)}
    saved_rows: list[store.Row] = []

    def record(row: store.Row) -> None:
        store.upsert(out, row)
        index[(row.repo, row.path)] = row
        if row.skipped:
            summary.skipped += 1
        else:
            summary.saved += 1
            saved_rows.append(row)

    try:
        for item in client.search_repos(query, limit):
            summary.repos += 1
            full_name = item["full_name"]
            owner, name = full_name.split("/", 1)
            branch = item.get("default_branch") or "main"
            license_info = item.get("license") or {}
            base = dict(
                repo=full_name,
                default_branch=branch,
                stars=item.get("stargazers_count"),
                topics=list(item.get("topics") or []),
                repo_license=license_info.get("spdx_id"),
            )

            try:
                entries, truncated = client.get_tree(owner, name, branch)
            except SkipRepo:
                continue
            if truncated:
                record(store.Row(path="", fetched_at=now(), skipped="tree truncated", **base))
                continue

            for entry in entries:
                path = entry.get("path", "")
                if entry.get("type") != "blob" or not discover.is_prd_path(path):
                    continue
                summary.candidates += 1
                sha = entry.get("sha")
                size = int(entry.get("size") or 0)

                existing = index.get((full_name, path))
                wants_llm = (
                    llm_grader is not None
                    and existing is not None
                    and existing.skipped is None
                    and existing.llm_score is None
                )
                if existing is not None and existing.blob_sha == sha and not wants_llm:
                    summary.unchanged += 1
                    continue

                row = store.Row(
                    path=path,
                    url=entry.get("url"),
                    html_url=f"https://github.com/{full_name}/blob/{branch}/{quote(path, safe='/')}",
                    blob_sha=sha,
                    size=size,
                    fetched_at=now(),
                    **base,
                )
                if size > discover.MAX_BLOB_SIZE:
                    row.skipped = "over 1 MB"
                    record(row)
                    continue

                try:
                    content = client.get_blob(owner, name, path, branch)
                except SkipRepo as exc:
                    row.skipped = f"fetch failed: {exc}"
                    record(row)
                    continue
                if not discover.looks_like_prd(content):
                    row.skipped = "content sniff"
                    record(row)
                    continue

                text = content.decode("utf-8", errors="replace")
                result = grade(text)
                row.title = discover.extract_title(text, path.rsplit("/", 1)[-1])
                row.inline_license = discover.find_inline_license(text)
                row.grade_score, row.grade_letter, row.grade_reasons = result.score, result.letter, result.reasons
                if llm_grader is not None:
                    llm = llm_grader(text)
                    row.llm_score, row.llm_critique, row.llm_model = llm.score, llm.critique, llm.model
                try:
                    store.write_document(out, row, text)
                except OSError as exc:
                    row.skipped = f"write failed: {exc}"
                    record(row)
                    continue
                record(row)
    except GitHubError as exc:
        summary.error = str(exc)

    summary.top = sorted(saved_rows, key=lambda r: r.grade_score or 0, reverse=True)[:5]
    return summary
