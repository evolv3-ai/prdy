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


import json

import httpx

from prdy.github import API_URL, GitHubClient
from prdy.llm import LlmGrade
from prdy.store import Row, upsert
from tests.test_crawl import FakeGitHub


@pytest.fixture
def patched_github(monkeypatch, fixtures):
    fake = FakeGitHub(fixtures)
    http = httpx.Client(transport=httpx.MockTransport(fake), base_url=API_URL)
    monkeypatch.setattr("prdy.cli.resolve_token", lambda: "tok")
    monkeypatch.setattr("prdy.cli.GitHubClient", lambda token: GitHubClient(token, http=http, sleep=lambda s: None))
    return fake


def test_crawl_refuses_without_token(monkeypatch, capsys):
    monkeypatch.setattr("prdy.cli.resolve_token", lambda: None)
    assert main(["crawl", "prd"]) == 1
    assert "GITHUB_TOKEN" in capsys.readouterr().err


def test_crawl_llm_requires_openrouter_key(monkeypatch, capsys):
    monkeypatch.setattr("prdy.cli.resolve_token", lambda: "tok")
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    assert main(["crawl", "prd", "--llm"]) == 1
    assert "OPENROUTER_API_KEY" in capsys.readouterr().err


def test_crawl_runs_and_prints_summary(patched_github, tmp_path, capsys):
    assert main(["crawl", "prd", "--limit", "5", "--out", str(tmp_path)]) == 0
    out = capsys.readouterr().out
    assert "Repos examined: 2" in out and "Saved: 1" in out and "Skipped: 3" in out
    assert "docs/prd/login.md" in out and "Widget Login PRD" in out
    assert (tmp_path / "index.jsonl").exists()


def test_crawl_exit_2_on_unrecoverable_api_error(patched_github, tmp_path, capsys):
    patched_github.fail_search_after = 1
    assert main(["crawl", "prd", "--limit", "200", "--out", str(tmp_path)]) == 2
    captured = capsys.readouterr()
    assert "crawl aborted" in captured.err and "Saved: 1" in captured.out


from prdy.github import AuthError


def test_crawl_auth_error_exits_1(monkeypatch, tmp_path, capsys):
    monkeypatch.setattr("prdy.cli.resolve_token", lambda: "tok")
    monkeypatch.setattr("prdy.cli.GitHubClient", lambda token: object())

    def raise_auth_error(*args, **kwargs):
        raise AuthError("GitHub rejected the token (401)")

    monkeypatch.setattr("prdy.cli.run_crawl", raise_auth_error)
    assert main(["crawl", "prd", "--out", str(tmp_path)]) == 1
    assert "auth error" in capsys.readouterr().err


def test_grade_prints_score_letter_reasons(fixtures, capsys):
    assert main(["grade", str(fixtures / "good_prd.md")]) == 0
    out = capsys.readouterr().out
    assert out.splitlines()[0] == "94 A"
    assert "between 200 and 600 words" in out


def test_grade_missing_file(tmp_path, capsys):
    assert main(["grade", str(tmp_path / "nope.md")]) == 1
    assert "nope.md" in capsys.readouterr().err


def test_grade_with_llm(monkeypatch, fixtures, capsys):
    monkeypatch.setattr("prdy.cli.grade_with_model", lambda text, model: LlmGrade(70, "fine", model))
    assert main(["grade", str(fixtures / "weak_prd.md"), "--llm", "--model", "m/x"]) == 0
    out = capsys.readouterr().out
    assert "model m/x: 70" in out and "fine" in out


def test_grade_llm_without_key_exits_1(monkeypatch, fixtures, capsys):
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    assert main(["grade", str(fixtures / "weak_prd.md"), "--llm"]) == 1
    captured = capsys.readouterr()
    assert "OPENROUTER_API_KEY" in captured.err
    assert captured.out.startswith("8 F")


def seed(tmp_path):
    upsert(tmp_path, Row(repo="a/b", path="prd.md", title="Alpha", stars=10, grade_score=94, grade_letter="A", fetched_at="2026-01-02T00:00:00+00:00"))
    upsert(tmp_path, Row(repo="c/d", path="docs/prd.md", title="Charlie", stars=500, grade_score=60, grade_letter="C", fetched_at="2026-01-03T00:00:00+00:00"))
    upsert(tmp_path, Row(repo="e/f", path="x.md", skipped="content sniff"))


def test_list_table_sorted_by_score_and_hides_skipped(tmp_path, capsys):
    seed(tmp_path)
    assert main(["list", "--out", str(tmp_path)]) == 0
    lines = capsys.readouterr().out.splitlines()
    assert lines[0].split() == ["score", "grade", "stars", "repo", "path", "title"]
    assert lines[1].startswith("94") and lines[2].startswith("60")
    assert len(lines) == 3


def test_list_sort_stars_and_min_grade(tmp_path, capsys):
    seed(tmp_path)
    main(["list", "--out", str(tmp_path), "--sort", "stars"])
    assert capsys.readouterr().out.splitlines()[1].startswith("60")
    main(["list", "--out", str(tmp_path), "--min-grade", "B"])
    lines = capsys.readouterr().out.splitlines()
    assert len(lines) == 2 and lines[1].startswith("94")


def test_list_json(tmp_path, capsys):
    seed(tmp_path)
    assert main(["list", "--out", str(tmp_path), "--json", "--sort", "fetched"]) == 0
    data = json.loads(capsys.readouterr().out)
    assert [d["repo"] for d in data] == ["c/d", "a/b"]


def test_list_empty_corpus(tmp_path, capsys):
    assert main(["list", "--out", str(tmp_path / "missing")]) == 0
    assert "no PRDs" in capsys.readouterr().out
