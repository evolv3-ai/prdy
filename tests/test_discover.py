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


from prdy.discover import is_prd_path, MAX_BLOB_SIZE


@pytest.mark.parametrize("path", [
    "prd.md",
    "PRD-login.md",
    "feature_prd.md",
    "docs/prd/login.md",
    "docs/prds/2025/checkout.mdx",
    "specs/product-requirements.md",
    "specs/product_requirements.rst",
    "docs/requirements.md",
    "docs/Requirements-Overview.txt",
    "PRD.markdown",
])
def test_is_prd_path_positive(path):
    assert is_prd_path(path)


@pytest.mark.parametrize("path", [
    "requirements.txt",
    "src/requirements.txt",
    "prdy/cli.py",
    "docs/prd/diagram.png",
    "README.md",
    "docs/upgrade.md",
    "prd",
    "sprdx.md",
    "docs/aprd.md",
])
def test_is_prd_path_negative(path):
    assert not is_prd_path(path)


def test_max_blob_size_is_one_megabyte():
    assert MAX_BLOB_SIZE == 1_000_000
