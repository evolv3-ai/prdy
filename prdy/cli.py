"""argparse entry point. The only module in prdy that prints."""
from __future__ import annotations

import argparse
import sys

from prdy import __version__


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


def cmd_crawl(args: argparse.Namespace) -> int:
    print("crawl: not implemented yet", file=sys.stderr)
    return 1


def cmd_grade(args: argparse.Namespace) -> int:
    print("grade: not implemented yet", file=sys.stderr)
    return 1


def cmd_list(args: argparse.Namespace) -> int:
    print("list: not implemented yet", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
