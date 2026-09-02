import pytest

from prdy.discover import build_query


def test_build_query_keywords_only():
    assert build_query("product requirements") == "product requirements"


def test_build_query_all_qualifiers_in_order():
    q = build_query("prd", topics=["prd", "docs"], stars=">50", language="Python",
                    pushed=">2025-01-01", org="acme")
    assert q == "prd topic:prd topic:docs stars:>50 language:Python pushed:>2025-01-01 org:acme"


def test_build_query_strips_and_skips_empty():
    assert build_query("  prd  ", topics=[], stars=None, language="") == "prd"
