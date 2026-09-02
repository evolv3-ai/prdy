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


from prdy.discover import looks_like_prd, find_inline_license, extract_title


def test_looks_like_prd_matches_requirement_or_prd_in_first_2kb():
    assert looks_like_prd(b"# Login PRD\n\nsome text")
    assert looks_like_prd(b"Functional Requirements:\n- a")
    assert not looks_like_prd(b"# Install notes\n\nRun pip install -e .")


def test_looks_like_prd_ignores_bytes_after_2kb():
    padding = b"x" * 2048
    assert not looks_like_prd(padding + b" requirement")
    assert looks_like_prd(b"requirement " + padding)


def test_looks_like_prd_tolerates_bad_utf8():
    assert looks_like_prd(b"\xff\xfe PRD \xff")


def test_find_inline_license_returns_first_matching_line_trimmed():
    text = "# Title\n\nbody\n\nCopyright 2024 Acme Inc. All rights reserved.\nLicense: MIT\n"
    assert find_inline_license(text) == "Copyright 2024 Acme Inc. All rights reserved."
    assert find_inline_license("SPDX-License-Identifier: Apache-2.0") == "SPDX-License-Identifier: Apache-2.0"
    assert find_inline_license("Shared under CC BY 4.0") == "Shared under CC BY 4.0"
    assert find_inline_license("This licence applies") == "This licence applies"
    assert find_inline_license("© 2025 Someone") == "© 2025 Someone"
    assert find_inline_license("nothing here") is None
    assert len(find_inline_license("license " + "y" * 500)) == 200


def test_extract_title_first_h1_or_fallback():
    assert extract_title("intro\n# Login PRD  \n## Sub", "x.md") == "Login PRD"
    assert extract_title("## Only H2\n", "x.md") == "x.md"
    assert extract_title("# Trailing hashes ##\n", "x.md") == "Trailing hashes"


def test_extract_title_ignores_fenced_code():
    assert extract_title("```\n# Not a title\n```\n# Real\n", "f.md") == "Real"
