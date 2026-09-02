import pytest

from prdy.cli import build_parser, main


def test_crawl_flags_parse():
    args = build_parser().parse_args(
        ["crawl", "product requirements", "--topic", "prd", "--topic", "docs",
         "--stars", ">50", "--language", "Python", "--pushed", ">2025-01-01",
         "--org", "acme", "--limit", "5", "--out", "./c", "--llm", "--model", "m"]
    )
    assert args.command == "crawl"
    assert args.keywords == "product requirements"
    assert args.topic == ["prd", "docs"]
    assert args.stars == ">50"
    assert args.language == "Python"
    assert args.pushed == ">2025-01-01"
    assert args.org == "acme"
    assert args.limit == 5
    assert args.out == "./c"
    assert args.llm is True
    assert args.model == "m"


def test_crawl_defaults():
    args = build_parser().parse_args(["crawl", "prd"])
    assert args.topic == []
    assert args.limit == 30
    assert args.out == "./corpus"
    assert args.llm is False
    assert args.model is None


def test_grade_and_list_parse():
    parser = build_parser()
    g = parser.parse_args(["grade", "x.md"])
    assert g.command == "grade" and g.file == "x.md" and g.llm is False
    lst = parser.parse_args(["list", "--min-grade", "B", "--sort", "stars", "--json"])
    assert lst.command == "list" and lst.min_grade == "B" and lst.sort == "stars" and lst.json is True
    assert parser.parse_args(["list"]).sort == "score"


def test_usage_error_exits_1():
    assert main([]) == 1
    assert main(["crawl"]) == 1


def test_help_exits_0():
    assert main(["--help"]) == 0
