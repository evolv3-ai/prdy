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


def test_document_paths_replace_slashes_and_keep_extension(tmp_path):
    md, meta = document_paths(tmp_path, "acme/widgets", "docs/prd/login.txt")
    assert md == tmp_path / "acme__widgets" / "docs__prd__login.txt.md"
    assert meta == tmp_path / "acme__widgets" / "docs__prd__login.txt.meta.json"
    md2, meta2 = document_paths(tmp_path, "acme/widgets", "PRD.md")
    assert md2.name == "PRD.md.md" and meta2.name == "PRD.md.meta.json"
    md3, _ = document_paths(tmp_path, "acme/widgets", "docs/my_prd.md")
    assert md3.name == "docs__my_prd.md.md"


def test_document_paths_escapes_backslashes(tmp_path):
    md, _ = document_paths(tmp_path, "a/b", "..\\..\\evil.md")
    assert md.parent == tmp_path / "a__b"
    assert md.name == "..%5C..%5Cevil.md.md"


def test_document_paths_distinct_for_paths_the_old_rule_merged(tmp_path):
    paths = [
        "docs/prd.md", "docs/prd.txt", "docs__prd.md", "docs/prd", "docs_/_prd.md", "docs/_/prd.md",
        "docs%5F%5Fprd.md", "docs\\prd.md", "docs/prd.md.md", "_prd.md", "%5Fprd.md", "docs//prd.md",
    ]
    results = [document_paths(tmp_path, "a/b", p) for p in paths]
    assert len({md for md, _ in results}) == len(paths)
    assert len({meta for _, meta in results}) == len(paths)
    for md, meta in results:
        assert md.parent == meta.parent == tmp_path / "a__b"
        assert md.name.endswith(".md") and meta.name.endswith(".meta.json")
    assert results[0][0].name == "docs__prd.md.md"
    assert results[1][0].name == "docs__prd.txt.md"
    assert results[2][0].name == "docs%5F%5Fprd.md.md"


def test_document_paths_case_only_difference_stays_distinct(tmp_path):
    # E2 (held-out). Ruling: paths differing only by letter case are not handled; the corpus
    # assumes a case-sensitive filesystem, and on one each such path still gets its own document.
    upper_md, upper_meta = document_paths(tmp_path, "a/b", "docs/PRD.md")
    lower_md, lower_meta = document_paths(tmp_path, "a/b", "docs/prd.md")
    assert upper_md != lower_md and upper_meta != lower_meta
    assert upper_md.name == "docs__PRD.md.md" and lower_md.name == "docs__prd.md.md"


def test_document_paths_avoid_location_held_by_other_path(tmp_path):
    folder = tmp_path / "a__b"
    folder.mkdir()
    (folder / "prd.md.md").write_text("# other\n")
    (folder / "prd.md.meta.json").write_text(json.dumps({"repo": "a/b", "path": "prd.md.txt"}))

    md, meta = document_paths(tmp_path, "a/b", "prd.md")
    assert md.parent == meta.parent == folder
    assert md.name != "prd.md.md" and md.name.startswith("prd.md.") and md.name.endswith(".md")
    assert meta.name == md.name[: -len(".md")] + ".meta.json"
    assert (md, meta) == document_paths(tmp_path, "a/b", "prd.md")
    # the path the sidecar names keeps the location
    assert document_paths(tmp_path, "a/b", "prd.md.txt")[0].name == "prd.md.txt.md"

    write_document(tmp_path, Row(repo="a/b", path="prd.md"), "# mine\n")
    assert (folder / "prd.md.md").read_text() == "# other\n"
    assert md.read_text() == "# mine\n"
    assert document_paths(tmp_path, "a/b", "prd.md") == (md, meta)


def test_write_document_writes_text_and_sidecar(tmp_path):
    row = Row(repo="acme/widgets", path="docs/prd.md", blob_sha="s", grade_score=94, grade_letter="A")
    md = write_document(tmp_path, row, "# Hello\n")
    assert md.read_text() == "# Hello\n"
    sidecar = json.loads((md.parent / "docs__prd.md.meta.json").read_text())
    assert sidecar == row.to_dict()


from prdy.store import LETTER_RANK, filter_rows


def test_filter_rows_drops_skipped_applies_floor_and_sorts():
    rows = [
        Row(repo="a/b", path="prd.md", stars=10, grade_score=94, grade_letter="A"),
        Row(repo="c/d", path="prd.md", stars=500, grade_score=60, grade_letter="C"),
        Row(repo="e/f", path="x.md", skipped="content sniff"),
    ]
    by_score = filter_rows(rows, None, "score")
    assert [r.repo for r in by_score] == ["a/b", "c/d"]

    by_floor = filter_rows(rows, "B", "score")
    assert [r.repo for r in by_floor] == ["a/b"]

    by_stars = filter_rows(rows, None, "stars")
    assert by_stars[0].repo == "c/d"

    assert LETTER_RANK["A"] > LETTER_RANK["F"]
