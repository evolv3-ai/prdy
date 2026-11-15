import json
from pathlib import Path

import httpx
import pytest

from prdy.crawl import CrawlSummary, run_crawl
from prdy.github import API_URL, GitHubClient
from prdy.llm import LlmGrade
from prdy.store import Row, document_paths, read_index, upsert


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


class OverrideGitHub(FakeGitHub):
    """FakeGitHub, but specific paths answer with a fixed response instead."""

    def __init__(self, fixtures: Path, overrides: dict[str, httpx.Response]):
        super().__init__(fixtures)
        self.overrides = overrides

    def __call__(self, request: httpx.Request) -> httpx.Response:
        path = request.url.path
        if path in self.overrides:
            self.requests.append(path)
            return self.overrides[path]
        return super().__call__(request)


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

    md = tmp_path / "acme__widgets" / "docs__prd__login.md.md"
    meta = tmp_path / "acme__widgets" / "docs__prd__login.md.meta.json"
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
    assert not (tmp_path / "acme__widgets" / "docs__requirements.md.md").exists()
    assert fake.blob_requests() == [
        "/repos/acme/widgets/contents/docs/prd/login.md",
        "/repos/acme/widgets/contents/docs/requirements.md",
    ]


def test_recrawl_skips_indexed_shas(client, fake, tmp_path):
    run_crawl(client, "prd", limit=10, out=tmp_path)
    before = len(fake.blob_requests())
    summary = run_crawl(client, "prd", limit=10, out=tmp_path)
    assert len(fake.blob_requests()) == before
    # only the truncated repo is re-recorded; the three candidates are unchanged
    assert (summary.candidates, summary.saved, summary.skipped, summary.unchanged) == (3, 0, 1, 3)
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


def test_write_failure_is_recorded_and_skipped(client, fake, tmp_path, monkeypatch):
    def boom(out, row, text):
        raise OSError("disk full")

    monkeypatch.setattr("prdy.store.write_document", boom)
    summary = run_crawl(client, "prd", limit=10, out=tmp_path)

    rows = {(r.repo, r.path): r for r in read_index(tmp_path)}
    login = rows[("acme/widgets", "docs/prd/login.md")]
    assert login.skipped is not None and login.skipped.startswith("write failed: ")
    assert not (tmp_path / "acme__widgets" / "docs__prd__login.md.md").exists()
    assert (summary.repos, summary.candidates, summary.saved, summary.skipped) == (2, 3, 0, 4)


def test_crawl_fetch_failure_is_recorded_and_skipped(fixtures, tmp_path):
    fake = OverrideGitHub(fixtures, {
        "/repos/acme/widgets/contents/docs/prd/login.md": httpx.Response(404, json={"message": "Not Found"}),
    })
    http = httpx.Client(transport=httpx.MockTransport(fake), base_url=API_URL)
    client = GitHubClient("tok", http=http, sleep=lambda s: None, clock=lambda: 0.0)

    summary = run_crawl(client, "prd", limit=10, out=tmp_path)

    rows = {(r.repo, r.path): r for r in read_index(tmp_path)}
    login = rows[("acme/widgets", "docs/prd/login.md")]
    assert login.skipped is not None and login.skipped.startswith("fetch failed: ")
    assert not (tmp_path / "acme__widgets" / "docs__prd__login.md.md").exists()
    assert (summary.repos, summary.candidates, summary.saved, summary.skipped) == (2, 3, 0, 4)


def test_crawl_skips_repo_with_empty_git_repository(fixtures, tmp_path):
    fake = OverrideGitHub(fixtures, {
        "/repos/acme/widgets/git/trees/main": httpx.Response(409, json={"message": "Git Repository is empty"}),
    })
    http = httpx.Client(transport=httpx.MockTransport(fake), base_url=API_URL)
    client = GitHubClient("tok", http=http, sleep=lambda s: None, clock=lambda: 0.0)

    summary = run_crawl(client, "prd", limit=10, out=tmp_path)

    assert summary.repos == 2
    assert summary.candidates == 0
    rows = read_index(tmp_path)
    assert not any(r.repo == "acme/widgets" for r in rows)
    assert any(r.repo == "beta/notes" and r.skipped == "tree truncated" for r in rows)


COLLIDING = {
    "docs/prd.md": b"# Markdown PRD\n\nRequirements for the markdown file.\n",
    "docs/prd.txt": b"Text PRD\n\nRequirements for the text file.\n",
    "docs__prd.md": b"# Top-level PRD\n\nRequirements for the top-level file.\n",
}


class OneRepoGitHub:
    """One repository, acme/widgets, whose tree is exactly the given {path: content} mapping."""

    def __init__(self, files: dict[str, bytes]):
        self.files = files
        self.requests: list[str] = []
        self.fail_on: str | None = None

    def __call__(self, request: httpx.Request) -> httpx.Response:
        path = request.url.path
        self.requests.append(path)
        if path == "/search/repositories":
            if request.url.params["page"] == "1":
                return httpx.Response(200, json={"items": [{"full_name": "acme/widgets", "default_branch": "main"}]})
            return httpx.Response(200, json={"items": []})
        if path == "/repos/acme/widgets/git/trees/main":
            tree = [
                {"path": p, "type": "blob", "sha": f"sha-{p}", "size": len(body)}
                for p, body in self.files.items()
            ]
            return httpx.Response(200, json={"tree": tree, "truncated": False})
        prefix = "/repos/acme/widgets/contents/"
        if path.startswith(prefix) and path[len(prefix):] in self.files:
            if path[len(prefix):] == self.fail_on:
                raise RuntimeError("interrupted")
            return httpx.Response(200, content=self.files[path[len(prefix):]])
        return httpx.Response(404, json={"message": "Not Found"})

    def blob_requests(self) -> list[str]:
        return [p for p in self.requests if "/contents/" in p]


def one_repo_client(fake: OneRepoGitHub) -> GitHubClient:
    http = httpx.Client(transport=httpx.MockTransport(fake), base_url=API_URL)
    return GitHubClient("tok", http=http, sleep=lambda s: None, clock=lambda: 0.0)


def corpus_files(out: Path) -> dict[Path, bytes]:
    return {p: p.read_bytes() for p in sorted(out.rglob("*")) if p.is_file()}


def assert_nothing_lost(out: Path, before: dict[Path, bytes], writing: set[str]) -> None:
    """SC6: no pre-existing file is gone, and no document of another source path changed."""
    after = corpus_files(out)
    assert set(before) <= set(after)
    for file, data in before.items():
        if not file.name.endswith(".md"):
            continue
        sidecar = file.with_name(file.name[: -len(".md")] + ".meta.json")
        if sidecar in before and json.loads(before[sidecar])["path"] not in writing:
            assert after[file] == data, file


def old_rule_names(path: str) -> tuple[str, str]:
    """File names the naming rule before this fix gave a source path."""
    flat = path.replace("/", "__")
    stem = flat.rsplit(".", 1)[0] if "." in flat.rsplit("__", 1)[-1] else flat
    return f"{stem}.md", f"{stem}.meta.json"


def test_colliding_paths_each_get_own_document_and_sidecar(tmp_path):
    # a corpus left by the old rule: one file shared by all three paths, last written by docs/prd.txt
    folder = tmp_path / "acme__widgets"
    folder.mkdir()
    old_md, old_meta = old_rule_names("docs/prd.txt")
    assert (old_md, old_meta) == old_rule_names("docs/prd.md") == old_rule_names("docs__prd.md")
    (folder / old_md).write_bytes(b"old shared text\n")
    (folder / old_meta).write_text(json.dumps(Row(repo="acme/widgets", path="docs/prd.txt").to_dict()))
    (tmp_path / "notes.txt").write_text("the owner's own file\n")
    before = corpus_files(tmp_path)

    fake = OneRepoGitHub(COLLIDING)
    summary = run_crawl(one_repo_client(fake), "prd", limit=10, out=tmp_path)

    assert (summary.candidates, summary.saved, summary.skipped, summary.unchanged) == (3, 3, 0, 0)
    documents = set()
    for path, body in COLLIDING.items():
        md, meta = document_paths(tmp_path, "acme/widgets", path)
        assert md.read_bytes() == body
        assert json.loads(meta.read_text())["path"] == path
        documents.add(md)
        documents.add(meta)
    assert len(documents) == 6
    assert_nothing_lost(tmp_path, before, writing=set())
    assert (folder / old_md).read_bytes() == b"old shared text\n"

    # nothing changed upstream: the next crawl fetches and writes nothing
    fake.requests.clear()
    settled = corpus_files(tmp_path)
    again = run_crawl(one_repo_client(fake), "prd", limit=10, out=tmp_path)
    assert (again.saved, again.skipped, again.unchanged) == (0, 0, 3)
    assert fake.blob_requests() == []
    assert corpus_files(tmp_path) == settled


def test_saved_row_without_document_is_fetched_again(tmp_path):
    files = {"docs/prd.md": COLLIDING["docs/prd.md"], "docs/prd.txt": COLLIDING["docs/prd.txt"]}
    folder = tmp_path / "acme__widgets"
    folder.mkdir()
    # an earlier version saved both rows, with unchanged blob shas, into one old-named file
    old_md, old_meta = old_rule_names("docs/prd.md")
    for path in files:
        upsert(tmp_path, Row(repo="acme/widgets", path=path, blob_sha=f"sha-{path}", grade_score=10, grade_letter="F"))
    (folder / old_md).write_bytes(files["docs/prd.txt"])
    (folder / old_meta).write_text(json.dumps(Row(repo="acme/widgets", path="docs/prd.txt").to_dict()))
    before = corpus_files(tmp_path)

    fake = OneRepoGitHub(files)
    summary = run_crawl(one_repo_client(fake), "prd", limit=10, out=tmp_path)

    assert (summary.candidates, summary.saved, summary.skipped, summary.unchanged) == (2, 2, 0, 0)
    assert fake.blob_requests() == [
        "/repos/acme/widgets/contents/docs/prd.md",
        "/repos/acme/widgets/contents/docs/prd.txt",
    ]
    for path, body in files.items():
        md, meta = document_paths(tmp_path, "acme/widgets", path)
        assert md.read_bytes() == body
        assert json.loads(meta.read_text())["path"] == path
    assert_nothing_lost(tmp_path, before, writing=set())
    assert (folder / old_md).read_bytes() == files["docs/prd.txt"]
    assert len(read_index(tmp_path)) == 2

    fake.requests.clear()
    again = run_crawl(one_repo_client(fake), "prd", limit=10, out=tmp_path)
    assert (again.saved, again.unchanged) == (0, 2)
    assert fake.blob_requests() == []


def test_skipped_row_without_document_stays_unchanged(tmp_path):
    files = {"docs/prd.md": b"nothing relevant here\n"}
    fake = OneRepoGitHub(files)
    first = run_crawl(one_repo_client(fake), "prd", limit=10, out=tmp_path)
    assert read_index(tmp_path)[0].skipped == "content sniff" and first.skipped == 1

    fake.requests.clear()
    again = run_crawl(one_repo_client(fake), "prd", limit=10, out=tmp_path)
    assert (again.saved, again.skipped, again.unchanged) == (0, 0, 1)
    assert fake.blob_requests() == []


def test_interrupted_crawl_rows_have_documents_and_next_crawl_completes(tmp_path):
    # E5 (held-out). Ruling: a crawl interrupted between two candidates leaves every index row
    # already recorded with its document on disk, and the next crawl completes the rest; two
    # crawls running at once on one corpus are unsupported, with no guarantee.
    fake = OneRepoGitHub(COLLIDING)
    fake.fail_on = "docs/prd.txt"  # the second candidate
    with pytest.raises(RuntimeError, match="interrupted"):
        run_crawl(one_repo_client(fake), "prd", limit=10, out=tmp_path)

    rows = read_index(tmp_path)
    assert [(r.path, r.skipped) for r in rows] == [("docs/prd.md", None)]
    for row in rows:
        md, meta = document_paths(tmp_path, row.repo, row.path)
        assert md.read_bytes() == COLLIDING[row.path]
        assert json.loads(meta.read_text())["path"] == row.path

    fake.fail_on = None
    fake.requests.clear()
    summary = run_crawl(one_repo_client(fake), "prd", limit=10, out=tmp_path)
    assert (summary.candidates, summary.saved, summary.skipped, summary.unchanged) == (3, 2, 0, 1)
    assert fake.blob_requests() == [
        "/repos/acme/widgets/contents/docs/prd.txt",
        "/repos/acme/widgets/contents/docs__prd.md",
    ]
    assert {r.path for r in read_index(tmp_path)} == set(COLLIDING)
    for path, body in COLLIDING.items():
        assert document_paths(tmp_path, "acme/widgets", path)[0].read_bytes() == body


def test_old_named_document_of_other_path_is_left_unchanged(tmp_path):
    # E10 (held-out). Ruling: "Heal on next crawl" - old-named files are left in place, never
    # deleted; an old document occupying a path's location keeps its bytes and the new document
    # is still stored separately.
    new_path, old_path = "prd.md", "prd.md.txt"
    wanted_md, wanted_meta = document_paths(tmp_path, "acme/widgets", new_path)
    # under the old rule, the other path's document and sidecar sit exactly there
    assert (wanted_md.name, wanted_meta.name) == old_rule_names(old_path)
    wanted_md.parent.mkdir()
    old_text = b"# Older PRD\n\nRequirements kept from an earlier crawl.\n"
    old_sidecar = json.dumps(Row(repo="acme/widgets", path=old_path, blob_sha="old").to_dict()).encode()
    wanted_md.write_bytes(old_text)
    wanted_meta.write_bytes(old_sidecar)
    before = corpus_files(tmp_path)

    new_text = b"# Newer PRD\n\nRequirements for the other source path.\n"
    fake = OneRepoGitHub({new_path: new_text})
    summary = run_crawl(one_repo_client(fake), "prd", limit=10, out=tmp_path)

    assert (summary.candidates, summary.saved, summary.skipped, summary.unchanged) == (1, 1, 0, 0)
    assert wanted_md.read_bytes() == old_text
    assert wanted_meta.read_bytes() == old_sidecar
    assert_nothing_lost(tmp_path, before, writing={new_path})
    assert set(before) < set(corpus_files(tmp_path))

    md, meta = document_paths(tmp_path, "acme/widgets", new_path)
    assert md != wanted_md and meta != wanted_meta
    assert md.read_bytes() == new_text
    assert json.loads(meta.read_text())["path"] == new_path

    # the separately stored document is found again: nothing is fetched on the next crawl
    fake.requests.clear()
    again = run_crawl(one_repo_client(fake), "prd", limit=10, out=tmp_path)
    assert (again.saved, again.unchanged) == (0, 1)
    assert fake.blob_requests() == []
    assert wanted_md.read_bytes() == old_text


LOGIN = "docs/prd/login.md"
LOGIN_BLOB = f"/repos/acme/widgets/contents/{LOGIN}"


def tree_files(out: Path) -> dict[Path, tuple[bytes, int]]:
    """Bytes and modification time of every document and sidecar (everything but the index)."""
    return {
        p: (p.read_bytes(), p.stat().st_mtime_ns)
        for p in sorted(out.rglob("*"))
        if p.is_file() and p.parent != out
    }


def test_failed_fetch_is_retried_on_every_crawl_until_it_succeeds(fixtures, tmp_path):
    # SC3 / E6 / E7 / N3: no cap, no backoff, and a retry that fails again is still counted
    fake = OverrideGitHub(fixtures, {LOGIN_BLOB: httpx.Response(404, json={"message": "Not Found"})})
    http = httpx.Client(transport=httpx.MockTransport(fake), base_url=API_URL)
    client = GitHubClient("tok", http=http, sleep=lambda s: None, clock=lambda: 0.0)
    md, meta = document_paths(tmp_path, "acme/widgets", LOGIN)

    run_crawl(client, "prd", limit=10, out=tmp_path)
    for _ in range(2):
        fake.requests.clear()
        summary = run_crawl(client, "prd", limit=10, out=tmp_path)
        assert fake.blob_requests() == [LOGIN_BLOB]
        # skipped: the failed retry plus the truncated repo; the other two candidates are unchanged
        assert (summary.candidates, summary.saved, summary.skipped, summary.unchanged) == (3, 0, 2, 2)
        row = next(r for r in read_index(tmp_path) if r.path == LOGIN)
        assert row.skipped is not None and row.skipped.startswith("fetch failed: ")
        assert row.blob_sha == "s2"
        assert not md.exists() and not meta.exists()

    del fake.overrides[LOGIN_BLOB]
    fake.requests.clear()
    summary = run_crawl(client, "prd", limit=10, out=tmp_path)
    assert fake.blob_requests() == [LOGIN_BLOB]
    assert (summary.candidates, summary.saved, summary.skipped, summary.unchanged) == (3, 1, 1, 2)
    row = next(r for r in read_index(tmp_path) if r.path == LOGIN)
    assert row.skipped is None and row.grade_letter == "A"
    assert md.read_text().startswith("# Widget Login PRD")
    assert json.loads(meta.read_text())["path"] == LOGIN
    assert len(read_index(tmp_path)) == 4

    # once saved it is an ordinary unchanged row
    fake.requests.clear()
    summary = run_crawl(client, "prd", limit=10, out=tmp_path)
    assert fake.blob_requests() == []
    assert (summary.saved, summary.skipped, summary.unchanged) == (0, 1, 3)


def test_failed_write_is_retried_on_every_crawl_until_it_succeeds(client, fake, tmp_path, monkeypatch):
    # SC3 / E6 / E7 / N3 for the write side
    def boom(out, row, text):
        raise OSError("disk full")

    md, meta = document_paths(tmp_path, "acme/widgets", LOGIN)
    with monkeypatch.context() as patch:
        patch.setattr("prdy.store.write_document", boom)
        run_crawl(client, "prd", limit=10, out=tmp_path)
        for _ in range(2):
            fake.requests.clear()
            summary = run_crawl(client, "prd", limit=10, out=tmp_path)
            assert fake.blob_requests() == [LOGIN_BLOB]
            assert (summary.candidates, summary.saved, summary.skipped, summary.unchanged) == (3, 0, 2, 2)
            row = next(r for r in read_index(tmp_path) if r.path == LOGIN)
            assert row.skipped is not None and row.skipped.startswith("write failed: ")
            assert not md.exists() and not meta.exists()

    fake.requests.clear()
    summary = run_crawl(client, "prd", limit=10, out=tmp_path)
    assert fake.blob_requests() == [LOGIN_BLOB]
    assert (summary.candidates, summary.saved, summary.skipped, summary.unchanged) == (3, 1, 1, 2)
    row = next(r for r in read_index(tmp_path) if r.path == LOGIN)
    assert row.skipped is None
    assert md.read_text().startswith("# Widget Login PRD")
    assert json.loads(meta.read_text())["path"] == LOGIN


def test_over_1mb_and_content_sniff_rows_are_not_fetched_again(client, fake, tmp_path):
    # SC4 / N4
    run_crawl(client, "prd", limit=10, out=tmp_path)
    before = {r.path: r for r in read_index(tmp_path)}
    assert before["docs/requirements.md"].skipped == "content sniff"
    assert before["docs/big-prd.md"].skipped == "over 1 MB"

    fake.requests.clear()
    summary = run_crawl(client, "prd", limit=10, out=tmp_path, now=lambda: "2030-01-01T00:00:00+00:00")
    assert fake.blob_requests() == []
    assert summary.unchanged == 3
    after = {r.path: r for r in read_index(tmp_path)}
    # the rows were not re-recorded either
    assert after["docs/requirements.md"] == before["docs/requirements.md"]
    assert after["docs/big-prd.md"] == before["docs/big-prd.md"]


def test_second_crawl_of_up_to_date_corpus_fetches_and_writes_nothing(client, fake, tmp_path):
    # SC5 / E4 / N5
    first = run_crawl(client, "prd", limit=10, out=tmp_path)
    assert first.saved == 1
    assert not any((r.skipped or "").startswith(("fetch failed", "write failed")) for r in read_index(tmp_path))
    before = tree_files(tmp_path)
    assert {p.name for p in before} == {"docs__prd__login.md.md", "docs__prd__login.md.meta.json"}

    fake.requests.clear()
    summary = run_crawl(client, "prd", limit=10, out=tmp_path)
    assert fake.blob_requests() == []
    assert tree_files(tmp_path) == before
    assert summary.candidates == 3 and summary.unchanged == summary.candidates
    assert summary.saved == 0


class FiveReasonsGitHub:
    """acme/widgets holds one candidate per per-file skip reason; beta/notes has a truncated tree."""

    FILES = {
        "docs/prd-fetch.md": None,  # the blob answers 404
        "docs/prd-write.md": b"# Write PRD\n\nRequirements that cannot be written to disk.\n",
        "docs/prd-big.md": b"",  # listed as over 1 MB, never fetched
        "docs/prd-sniff.md": b"installation notes, nothing else\n",
    }

    def __init__(self):
        self.requests: list[str] = []

    def __call__(self, request: httpx.Request) -> httpx.Response:
        path = request.url.path
        self.requests.append(path)
        if path == "/search/repositories":
            if request.url.params["page"] == "1":
                return httpx.Response(200, json={"items": [
                    {"full_name": "acme/widgets", "default_branch": "main"},
                    {"full_name": "beta/notes", "default_branch": "main"},
                ]})
            return httpx.Response(200, json={"items": []})
        if path == "/repos/acme/widgets/git/trees/main":
            tree = [
                {"path": p, "type": "blob", "sha": f"sha-{p}", "size": 2_000_000 if p == "docs/prd-big.md" else 60}
                for p in self.FILES
            ]
            return httpx.Response(200, json={"tree": tree, "truncated": False})
        if path == "/repos/beta/notes/git/trees/main":
            return httpx.Response(200, json={"tree": [], "truncated": True})
        prefix = "/repos/acme/widgets/contents/"
        if path.startswith(prefix) and self.FILES.get(path[len(prefix):]):
            return httpx.Response(200, content=self.FILES[path[len(prefix):]])
        return httpx.Response(404, json={"message": "Not Found"})

    def blob_requests(self) -> list[str]:
        return [p for p in self.requests if "/contents/" in p]


def test_only_fetch_and_write_failures_are_retried(tmp_path, monkeypatch):
    # E8 (held-out). Ruling: only skip reasons starting `fetch failed` or `write failed` are
    # retried; `over 1 MB`, `content sniff` and `tree truncated` rows keep today's behaviour.
    # User ruling: "fetch failed and write failed".
    from prdy import store

    real_write = store.write_document

    def write_unless_blocked(out, row, text):
        if row.path == "docs/prd-write.md":
            raise OSError("disk full")
        return real_write(out, row, text)

    monkeypatch.setattr("prdy.store.write_document", write_unless_blocked)
    fake = FiveReasonsGitHub()
    client = one_repo_client(fake)

    def reasons() -> dict[tuple[str, str], str]:
        return {(r.repo, r.path): (r.skipped or "").split(":")[0] for r in read_index(tmp_path)}

    all_five = {
        ("acme/widgets", "docs/prd-fetch.md"): "fetch failed",
        ("acme/widgets", "docs/prd-write.md"): "write failed",
        ("acme/widgets", "docs/prd-big.md"): "over 1 MB",
        ("acme/widgets", "docs/prd-sniff.md"): "content sniff",
        ("beta/notes", ""): "tree truncated",
    }
    first = run_crawl(client, "prd", limit=10, out=tmp_path)
    assert reasons() == all_five
    assert (first.candidates, first.saved, first.skipped, first.unchanged) == (4, 0, 5, 0)

    retried = [
        "/repos/acme/widgets/contents/docs/prd-fetch.md",
        "/repos/acme/widgets/contents/docs/prd-write.md",
    ]
    for _ in range(2):
        fake.requests.clear()
        summary = run_crawl(client, "prd", limit=10, out=tmp_path)
        # only the two failures are requested again; over 1 MB and content sniff are unchanged
        assert fake.blob_requests() == retried
        # the truncated repo is examined again and re-recorded as today, with no blob request
        assert "/repos/beta/notes/git/trees/main" in fake.requests
        assert (summary.candidates, summary.saved, summary.skipped, summary.unchanged) == (4, 0, 3, 2)
        assert reasons() == all_five
    assert corpus_files(tmp_path).keys() == {tmp_path / "index.jsonl"}


def test_crawl_with_no_candidates_writes_nothing(tmp_path, monkeypatch, capsys):
    # E9 (held-out). Ruling: a crawl whose search returns no repositories, or whose repositories
    # have no candidates, writes nothing, reports `Saved: 0  Skipped: 0  Unchanged: 0` for
    # candidates, and exits 0 as today.
    from prdy.cli import main

    def no_repositories(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"items": []})

    no_candidates = OneRepoGitHub({"README.md": b"# Widgets\n", "src/main.py": b"print('hi')\n"})

    for name, handler, repos in (("none", no_repositories, 0), ("empty", no_candidates, 1)):
        out = tmp_path / name
        out.mkdir()
        http = httpx.Client(transport=httpx.MockTransport(handler), base_url=API_URL)
        summary = run_crawl(GitHubClient("tok", http=http, sleep=lambda s: None), "prd", limit=5, out=out)
        assert summary == CrawlSummary(repos=repos)
        assert summary.error is None
        assert corpus_files(out) == {}

        # the same crawl at the command line: the printed totals and the exit code
        monkeypatch.setattr("prdy.cli.resolve_token", lambda: "tok")
        monkeypatch.setattr(
            "prdy.cli.GitHubClient",
            lambda token, handler=handler: GitHubClient(
                token, http=httpx.Client(transport=httpx.MockTransport(handler), base_url=API_URL), sleep=lambda s: None
            ),
        )
        assert main(["crawl", "prd", "--limit", "5", "--out", str(out)]) == 0
        captured = capsys.readouterr()
        assert f"Repos examined: {repos}  Candidates: 0  Saved: 0  Skipped: 0  Unchanged: 0" in captured.out
        assert captured.err == ""
        assert corpus_files(out) == {}
    assert no_candidates.blob_requests() == []
