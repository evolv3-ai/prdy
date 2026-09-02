import json
from dataclasses import fields

from prdy.store import INDEX_NAME, Row, find_row, index_path, read_index, upsert

SPEC_FIELDS = [
    "repo", "path", "url", "html_url", "blob_sha", "default_branch", "fetched_at",
    "stars", "topics", "repo_license", "inline_license", "size", "title",
    "grade_score", "grade_letter", "grade_reasons", "llm_score", "llm_critique",
    "llm_model", "skipped",
]


def test_row_fields_match_spec_order():
    assert [f.name for f in fields(Row)] == SPEC_FIELDS


def test_row_round_trip_ignores_unknown_keys():
    row = Row(repo="a/b", path="docs/prd.md", stars=3, topics=["x"], grade_reasons=["no date"])
    data = row.to_dict()
    assert data["skipped"] is None and data["topics"] == ["x"]
    assert Row.from_dict({**data, "extra": 1}) == row


def test_read_index_missing_is_empty(tmp_path):
    assert read_index(tmp_path) == []
    assert index_path(tmp_path) == tmp_path / INDEX_NAME


def test_upsert_appends_then_replaces(tmp_path):
    upsert(tmp_path, Row(repo="a/b", path="p.md", blob_sha="1"))
    upsert(tmp_path, Row(repo="a/b", path="q.md", blob_sha="2"))
    upsert(tmp_path, Row(repo="a/b", path="p.md", blob_sha="3", grade_score=50))
    rows = read_index(tmp_path)
    assert [(r.path, r.blob_sha) for r in rows] == [("p.md", "3"), ("q.md", "2")]
    lines = index_path(tmp_path).read_text().splitlines()
    assert len(lines) == 2 and json.loads(lines[0])["grade_score"] == 50


def test_upsert_keys_on_repo_and_path(tmp_path):
    upsert(tmp_path, Row(repo="a/b", path="p.md"))
    upsert(tmp_path, Row(repo="c/d", path="p.md"))
    assert len(read_index(tmp_path)) == 2


def test_find_row():
    rows = [Row(repo="a/b", path="p.md"), Row(repo="a/b", path="")]
    assert find_row(rows, "a/b", "") is rows[1]
    assert find_row(rows, "z/z", "p.md") is None


from prdy.store import document_paths, repo_dir, write_document


def test_repo_dir_uses_double_underscore(tmp_path):
    assert repo_dir(tmp_path, "acme/widgets") == tmp_path / "acme__widgets"


def test_document_paths_replace_slashes_and_drop_extension(tmp_path):
    md, meta = document_paths(tmp_path, "acme/widgets", "docs/prd/login.txt")
    assert md == tmp_path / "acme__widgets" / "docs__prd__login.md"
    assert meta == tmp_path / "acme__widgets" / "docs__prd__login.meta.json"
    md2, _ = document_paths(tmp_path, "acme/widgets", "PRD.md")
    assert md2.name == "PRD.md"


def test_write_document_writes_text_and_sidecar(tmp_path):
    row = Row(repo="acme/widgets", path="docs/prd.md", blob_sha="s", grade_score=94, grade_letter="A")
    md = write_document(tmp_path, row, "# Hello\n")
    assert md.read_text() == "# Hello\n"
    sidecar = json.loads((md.parent / "docs__prd.meta.json").read_text())
    assert sidecar == row.to_dict()
