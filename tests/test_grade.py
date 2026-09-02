import pytest

from prdy.grade import SECTIONS, find_headings, find_bold_leads, find_sections


def test_sections_table_has_eight_keys():
    assert set(SECTIONS) == {
        "problem", "goals", "users", "requirements", "success-metrics",
        "non-goals", "timeline", "open-questions",
    }


def test_find_headings_atx_and_setext():
    text = "# One\n\nSub\n---\n\n## Two ##\n\nTitle\n===\n\n| a | b |\n|---|---|\n- item\n"
    assert find_headings(text) == [(1, "One"), (2, "Sub"), (2, "Two"), (1, "Title")]


def test_find_bold_leads():
    text = "**Problem:** we lose users\n__Goals__\nnot **bold** here\n"
    assert find_bold_leads(text) == ["Problem", "Goals"]


@pytest.mark.parametrize("heading, expected", [
    ("Problem statement", {"problem"}),
    ("Background", {"problem"}),
    ("Goals", {"goals"}),
    ("Objectives", {"goals"}),
    ("Non-Goals", {"non-goals"}),
    ("Non goals", {"non-goals"}),
    ("Out of scope", {"non-goals"}),
    ("Goals and Non-Goals", {"goals", "non-goals"}),
    ("Target users", {"users"}),
    ("Personas", {"users"}),
    ("User stories", {"requirements"}),
    ("Functional requirements", {"requirements"}),
    ("Features", {"requirements"}),
    ("Success metrics", {"success-metrics"}),
    ("KPIs", {"success-metrics"}),
    ("Timeline", {"timeline"}),
    ("Milestones", {"timeline"}),
    ("Open questions", {"open-questions"}),
    ("Risks", {"open-questions"}),
    ("Installation", set()),
])
def test_find_sections_single_heading(heading, expected):
    assert find_sections(f"## {heading}\n\nbody\n") == expected


def test_find_sections_uses_bold_leads_too():
    assert find_sections("**Success Metrics:** ship it\n") == {"success-metrics"}


def test_find_headings_ignores_fenced_code():
    text = "intro\n\n```bash\n# Not a heading\n## Also not\n```\n\nplain paragraph\n"
    assert find_headings(text) == []
    assert find_sections(text) == set()


def test_find_headings_skips_front_matter():
    assert find_headings("---\ntitle: x\n---\n\n# Real\n") == [(1, "Real")]


from prdy.grade import (
    Grade, RUBRIC_TEXT, count_lists, count_tables, grade, has_date,
    has_owner_line, letter_for, word_count,
)


def test_word_count():
    assert word_count("one two\nthree  four") == 4


def test_count_lists_counts_contiguous_runs():
    text = "- a\n- b\n\n- c\n\nparagraph\n\n1. x\n2) y\n* z\n"
    assert count_lists(text) == 2  # blank lines do not split a run; a paragraph does


def test_count_tables_requires_separator_row():
    assert count_tables("| a | b |\n|---|---|\n| 1 | 2 |\n") == 1
    assert count_tables("| a | b |\n| 1 | 2 |\n") == 0
    assert count_tables("Sub\n---\n") == 0


def test_has_date():
    assert has_date("Updated 2026-08-14")
    assert has_date("Written in March 2025")
    assert has_date("Sept. 2024 draft")
    assert not has_date("version 1.2.3 released last year")


def test_has_owner_line():
    assert has_owner_line("Owner: Jane")
    assert has_owner_line("**Author**: Jane")
    assert has_owner_line("| Status | Draft |")
    assert has_owner_line("- DRI: Jane")
    assert not has_owner_line("The owner of the widget can edit it.")


@pytest.mark.parametrize("score, letter", [
    (100, "A"), (85, "A"), (84, "B"), (70, "B"), (69, "C"), (55, "C"), (54, "D"), (40, "D"), (39, "F"), (0, "F"),
])
def test_letter_for(score, letter):
    assert letter_for(score) == letter


def test_grade_good_prd(fixtures):
    result = grade((fixtures / "good_prd.md").read_text())
    assert isinstance(result, Grade)
    assert result.score == 94
    assert result.letter == "A"
    assert result.reasons == ["between 200 and 600 words"]


def test_grade_weak_prd(fixtures):
    result = grade((fixtures / "weak_prd.md").read_text())
    assert result.score == 8
    assert result.letter == "F"
    assert "no problem section" in result.reasons
    assert "no requirements section" not in result.reasons
    assert "under 200 words" in result.reasons
    assert "fewer than three headings across two levels" in result.reasons
    assert "needs a list and a table, or two lists" in result.reasons
    assert "no date" in result.reasons
    assert "no author, owner, or status line" in result.reasons


def test_grade_length_bands():
    assert "under 200 words" in grade("w " * 199).reasons
    assert "between 200 and 600 words" in grade("w " * 200).reasons
    long = grade("w " * 600)
    assert "between 200 and 600 words" not in long.reasons and "over 4000 words" not in long.reasons
    assert "over 4000 words" in grade("w " * 4001).reasons


def test_rubric_text_mentions_every_check():
    for word in ("Sections", "Length", "Heading", "Lists", "Ownership", "100"):
        assert word in RUBRIC_TEXT
