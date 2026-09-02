import json
from pathlib import Path

from prdy.cli import build_parser, main
from prdy.grade import grade
from prdy.store import Row, document_paths, read_index, upsert, write_document


def test_regrade_flags_parse():
    args = build_parser().parse_args(["regrade", "--out", "mycorpus"])
    assert args.command == "regrade"
    assert args.out == "mycorpus"

    args_default = build_parser().parse_args(["regrade"])
    assert args_default.out == "./corpus"


def test_regrade_missing_corpus_exits_1(tmp_path, capsys):
    corpus_dir = tmp_path / "nonexistent"
    assert main(["regrade", "--out", str(corpus_dir)]) == 1
    captured = capsys.readouterr()
    assert "no corpus index at" in captured.err


def test_regrade_missing_index_exits_1(tmp_path, capsys):
    assert main(["regrade", "--out", str(tmp_path)]) == 1
    captured = capsys.readouterr()
    assert "no corpus index at" in captured.err


def test_regrade_updates_scores_and_preserves_llm_fields(fixtures, tmp_path, capsys):
    good_text = (fixtures / "good_prd.md").read_text(encoding="utf-8")
    actual_grade = grade(good_text)

    # Seed doc 1: wrong rubric grade, but has LLM fields set
    row1 = Row(
        repo="acme/widgets",
        path="docs/prd.md",
        title="Widget Login PRD",
        stars=100,
        grade_score=10,
        grade_letter="F",
        grade_reasons=["stale"],
        llm_score=90,
        llm_critique="Great PRD",
        llm_model="anthropic/claude-sonnet-5",
    )
    write_document(tmp_path, row1, good_text)
    upsert(tmp_path, row1)

    # Seed doc 2: skipped row (no md file on disk)
    row2 = Row(
        repo="acme/gadgets",
        path="docs/skipped.md",
        skipped="content sniff",
        llm_score=None,
    )
    upsert(tmp_path, row2)

    assert main(["regrade", "--out", str(tmp_path)]) == 0
    out = capsys.readouterr().out
    assert "Regraded: 1 rows examined, 1 scores changed" in out

    # Check index.jsonl
    rows = read_index(tmp_path)
    assert len(rows) == 2

    r1 = next(r for r in rows if r.repo == "acme/widgets")
    assert r1.grade_score == actual_grade.score
    assert r1.grade_letter == actual_grade.letter
    assert r1.grade_reasons == actual_grade.reasons
    assert r1.llm_score == 90
    assert r1.llm_critique == "Great PRD"
    assert r1.llm_model == "anthropic/claude-sonnet-5"

    r2 = next(r for r in rows if r.repo == "acme/gadgets")
    assert r2.skipped == "content sniff"
    assert r2.grade_score is None

    # Check sidecar meta.json
    _, meta_path = document_paths(tmp_path, "acme/widgets", "docs/prd.md")
    sidecar = json.loads(meta_path.read_text(encoding="utf-8"))
    assert sidecar["grade_score"] == actual_grade.score
    assert sidecar["grade_letter"] == actual_grade.letter
    assert sidecar["grade_reasons"] == actual_grade.reasons
    assert sidecar["llm_score"] == 90
    assert sidecar["llm_critique"] == "Great PRD"
    assert sidecar["llm_model"] == "anthropic/claude-sonnet-5"


def test_regrade_unchanged_when_scores_match(fixtures, tmp_path, capsys):
    good_text = (fixtures / "good_prd.md").read_text(encoding="utf-8")
    actual_grade = grade(good_text)

    row = Row(
        repo="acme/widgets",
        path="docs/prd.md",
        grade_score=actual_grade.score,
        grade_letter=actual_grade.letter,
        grade_reasons=actual_grade.reasons,
    )
    write_document(tmp_path, row, good_text)
    upsert(tmp_path, row)

    assert main(["regrade", "--out", str(tmp_path)]) == 0
    out = capsys.readouterr().out
    assert "Regraded: 1 rows examined, 0 scores changed" in out
