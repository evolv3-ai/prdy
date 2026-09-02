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
