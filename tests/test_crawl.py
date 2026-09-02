import json
from pathlib import Path

import httpx
import pytest

from prdy.crawl import CrawlSummary, run_crawl
from prdy.github import API_URL, GitHubClient
from prdy.llm import LlmGrade
from prdy.store import read_index


class FakeGitHub:
    """Routes the fixture set: two repos, one truncated tree, one good PRD, one sniff failure."""

    def __init__(self, fixtures: Path):
        self.fixtures = fixtures
        self.requests: list[str] = []
        self.fail_search_after: int | None = None

    def __call__(self, request: httpx.Request) -> httpx.Response:
        path = request.url.path
        self.requests.append(path)
        if path == "/search/repositories":
            if self.fail_search_after is not None and len([p for p in self.requests if p == path]) > self.fail_search_after:
                return httpx.Response(500, json={"message": "boom"})
            if request.url.params["page"] == "1":
                return httpx.Response(200, json=json.loads((self.fixtures / "search_page.json").read_text()))
            return httpx.Response(200, json={"items": []})
        if path == "/repos/acme/widgets/git/trees/main":
            return httpx.Response(200, json=json.loads((self.fixtures / "tree_widgets.json").read_text()))
        if path == "/repos/beta/notes/git/trees/main":
            return httpx.Response(200, json=json.loads((self.fixtures / "tree_notes.json").read_text()))
        if path == "/repos/acme/widgets/contents/docs/prd/login.md":
            return httpx.Response(200, content=(self.fixtures / "good_prd.md").read_bytes())
        if path == "/repos/acme/widgets/contents/docs/requirements.md":
            return httpx.Response(200, content=(self.fixtures / "install_notes.md").read_bytes())
        return httpx.Response(404, json={"message": "Not Found"})

    def blob_requests(self) -> list[str]:
        return [p for p in self.requests if "/contents/" in p]


@pytest.fixture
def fake(fixtures):
    return FakeGitHub(fixtures)


@pytest.fixture
def client(fake):
    http = httpx.Client(transport=httpx.MockTransport(fake), base_url=API_URL)
    return GitHubClient("tok", http=http, sleep=lambda s: None, clock=lambda: 0.0)


def test_crawl_end_to_end(client, fake, tmp_path):
    summary = run_crawl(client, "prd", limit=10, out=tmp_path, now=lambda: "2026-09-02T00:00:00+00:00")

    assert isinstance(summary, CrawlSummary)
    assert (summary.repos, summary.candidates, summary.saved, summary.skipped) == (2, 3, 1, 3)
    assert summary.error is None
    assert [r.path for r in summary.top] == ["docs/prd/login.md"]

    md = tmp_path / "acme__widgets" / "docs__prd__login.md"
    meta = tmp_path / "acme__widgets" / "docs__prd__login.meta.json"
    assert md.read_text().startswith("# Widget Login PRD")
    sidecar = json.loads(meta.read_text())
    assert sidecar["grade_letter"] == "A" and sidecar["repo_license"] == "MIT"
    assert sidecar["inline_license"] == "Licensed under CC BY 4.0."
    assert sidecar["title"] == "Widget Login PRD"
    assert sidecar["html_url"] == "https://github.com/acme/widgets/blob/main/docs/prd/login.md"
    assert sidecar["url"] == "https://api.github.com/repos/acme/widgets/git/blobs/s2"
    assert sidecar["fetched_at"] == "2026-09-02T00:00:00+00:00"
    assert sidecar["stars"] == 120 and sidecar["topics"] == ["prd", "product"]
    assert sidecar["llm_score"] is None and sidecar["skipped"] is None

    rows = {(r.repo, r.path): r for r in read_index(tmp_path)}
    assert set(rows) == {
        ("acme/widgets", "docs/prd/login.md"),
        ("acme/widgets", "docs/requirements.md"),
        ("acme/widgets", "docs/big-prd.md"),
        ("beta/notes", ""),
    }
    assert rows[("acme/widgets", "docs/requirements.md")].skipped == "content sniff"
    assert rows[("acme/widgets", "docs/big-prd.md")].skipped == "over 1 MB"
    assert rows[("beta/notes", "")].skipped == "tree truncated"
    assert rows[("beta/notes", "")].repo_license is None
    assert not (tmp_path / "acme__widgets" / "docs__requirements.md").exists()
    assert fake.blob_requests() == [
        "/repos/acme/widgets/contents/docs/prd/login.md",
        "/repos/acme/widgets/contents/docs/requirements.md",
    ]


def test_recrawl_skips_indexed_shas(client, fake, tmp_path):
    run_crawl(client, "prd", limit=10, out=tmp_path)
    before = len(fake.blob_requests())
    summary = run_crawl(client, "prd", limit=10, out=tmp_path)
    assert len(fake.blob_requests()) == before
    assert (summary.candidates, summary.saved, summary.skipped) == (3, 0, 1)  # only the truncated repo is re-recorded
    assert len(read_index(tmp_path)) == 4


def test_recrawl_with_llm_refetches_only_ungraded_docs(client, fake, tmp_path):
    run_crawl(client, "prd", limit=10, out=tmp_path)
    fake.requests.clear()
    graded = []

    def grader(text: str) -> LlmGrade:
        graded.append(text[:20])
        return LlmGrade(81, "good", "fake/model")

    summary = run_crawl(client, "prd", limit=10, out=tmp_path, llm_grader=grader)
    assert fake.blob_requests() == ["/repos/acme/widgets/contents/docs/prd/login.md"]
    assert graded == ["# Widget Login PRD\n\n"]
    row = next(r for r in read_index(tmp_path) if r.path == "docs/prd/login.md")
    assert (row.llm_score, row.llm_critique, row.llm_model) == (81, "good", "fake/model")
    assert row.grade_score == 94  # rubric grade kept
    assert summary.saved == 1

    graded.clear()
    run_crawl(client, "prd", limit=10, out=tmp_path, llm_grader=grader)
    assert graded == []


def test_crawl_records_error_and_keeps_partial_index(client, fake, tmp_path):
    fake.fail_search_after = 1  # page 2 of search returns 500
    summary = run_crawl(client, "prd", limit=200, out=tmp_path)
    assert summary.error is not None and "500" in summary.error
    assert summary.saved == 1
    assert len(read_index(tmp_path)) == 4


def test_crawl_with_no_results(tmp_path):
    http = httpx.Client(transport=httpx.MockTransport(lambda r: httpx.Response(200, json={"items": []})), base_url=API_URL)
    summary = run_crawl(GitHubClient("t", http=http), "nothing", limit=5, out=tmp_path)
    assert summary == CrawlSummary()
    assert read_index(tmp_path) == []
