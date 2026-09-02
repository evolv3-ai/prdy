"""argparse entry point. The only module in prdy that prints."""
from __future__ import annotations

import argparse
import functools
import json
import os
import sys
from pathlib import Path

import httpx

from prdy import __version__
from prdy.crawl import CrawlSummary, run_crawl
from prdy.discover import build_query
from prdy.github import AuthError, GitHubClient, resolve_token
from prdy.grade import grade
from prdy.llm import DEFAULT_MODEL, LlmError, grade_with_model
from prdy.store import Row, filter_rows, read_index


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="prdy",
        description="Crawl GitHub for product requirements documents and grade them.",
    )
    parser.add_argument("--version", action="version", version=f"prdy {__version__}")
    sub = parser.add_subparsers(dest="command", required=True)

    crawl = sub.add_parser("crawl", help="search repositories and save PRDs into a corpus")
    crawl.add_argument("keywords", help="search keywords, passed verbatim")
    crawl.add_argument("--topic", action="append", default=[], help="topic qualifier; repeatable")
    crawl.add_argument("--stars", help='stars qualifier, e.g. ">50"')
    crawl.add_argument("--language", help="language qualifier")
    crawl.add_argument("--pushed", help='pushed qualifier, e.g. ">2025-01-01"')
    crawl.add_argument("--org", help="org qualifier")
    crawl.add_argument("--limit", type=int, default=30, help="max repositories to examine")
    crawl.add_argument("--out", default="./corpus", help="corpus directory")
    crawl.add_argument("--llm", action="store_true", help="also grade with a model via OpenRouter")
    crawl.add_argument("--model", help="OpenRouter model id (with --llm)")

    grade = sub.add_parser("grade", help="print the rubric grade for a local file")
    grade.add_argument("file")
    grade.add_argument("--llm", action="store_true")
    grade.add_argument("--model")

    lst = sub.add_parser("list", help="list the corpus index")
    lst.add_argument("--out", default="./corpus")
    lst.add_argument("--min-grade", choices=["A", "B", "C", "D", "F"])
    lst.add_argument("--sort", choices=["score", "stars", "fetched"], default="score")
    lst.add_argument("--json", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    try:
        args = parser.parse_args(argv)
    except SystemExit as exc:  # argparse exits 2 on usage errors, 0 on --help
        return 0 if exc.code == 0 else 1
    handlers = {"crawl": cmd_crawl, "grade": cmd_grade, "list": cmd_list}
    return handlers[args.command](args)


def _openrouter_key_missing() -> bool:
    return not os.environ.get("OPENROUTER_API_KEY")


def cmd_crawl(args: argparse.Namespace) -> int:
    token = resolve_token()
    if not token:
        print("No GitHub token found. Run `gh auth login` or set GITHUB_TOKEN.", file=sys.stderr)
        return 1
    llm_grader = None
    llm_http = None
    if args.llm:
        if _openrouter_key_missing():
            print("--llm needs OPENROUTER_API_KEY (tip: uv run --env-file .env prdy ...).", file=sys.stderr)
            return 1
        llm_http = httpx.Client(timeout=120.0)
        llm_grader = functools.partial(grade_with_model, model=args.model or DEFAULT_MODEL, http=llm_http)

    query = build_query(args.keywords, args.topic, args.stars, args.language, args.pushed, args.org)
    try:
        with GitHubClient(token) as client:
            summary = run_crawl(client, query, args.limit, Path(args.out), llm_grader=llm_grader)
    except AuthError as exc:
        print(f"auth error: {exc}", file=sys.stderr)
        return 1
    finally:
        if llm_http is not None:
            llm_http.close()
    print(format_summary(summary))
    if summary.error:
        print(f"crawl aborted: {summary.error}", file=sys.stderr)
        return 2
    return 0


def format_summary(summary: CrawlSummary) -> str:
    lines = [
        f"Repos examined: {summary.repos}  Candidates: {summary.candidates}  "
        f"Saved: {summary.saved}  Skipped: {summary.skipped}  Unchanged: {summary.unchanged}"
    ]
    if summary.top:
        lines.append("Top by score:")
        for r in summary.top:
            lines.append(f"  {r.grade_score:>3} {r.grade_letter}  {r.repo}  {r.path}  {r.title or ''}".rstrip())
    return "\n".join(lines)


def cmd_grade(args: argparse.Namespace) -> int:
    path = Path(args.file)
    if not path.is_file():
        print(f"not a file: {path}", file=sys.stderr)
        return 1
    if args.llm and _openrouter_key_missing():
        print("--llm needs OPENROUTER_API_KEY (tip: uv run --env-file .env prdy ...).", file=sys.stderr)
        return 1
    text = path.read_text(encoding="utf-8", errors="replace")
    result = grade(text)
    print(f"{result.score} {result.letter}")
    for reason in result.reasons:
        print(f"  - {reason}")
    if args.llm:
        try:
            llm = grade_with_model(text, model=args.model or DEFAULT_MODEL)
        except LlmError as exc:
            print(str(exc), file=sys.stderr)
            return 1
        score = "null" if llm.score is None else llm.score
        print(f"model {llm.model}: {score}")
        print(f"  {llm.critique}")
    return 0


def format_table(rows: list[Row]) -> str:
    header = ("score", "grade", "stars", "repo", "path", "title")
    body = [(str(r.grade_score), str(r.grade_letter), str(r.stars or 0), r.repo, r.path, r.title or "") for r in rows]
    widths = [max(len(cell) for cell in column) for column in zip(header, *body)]
    return "\n".join(
        "  ".join(cell.ljust(width) for cell, width in zip(line, widths)).rstrip()
        for line in (header, *body)
    )


def cmd_list(args: argparse.Namespace) -> int:
    rows = filter_rows(read_index(Path(args.out)), args.min_grade, args.sort)
    if args.json:
        print(json.dumps([r.to_dict() for r in rows], ensure_ascii=False, indent=2))
        return 0
    if not rows:
        print("no PRDs in the index")
        return 0
    print(format_table(rows))
    return 0


if __name__ == "__main__":
    sys.exit(main())
