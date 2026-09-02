"""One real GitHub search. Runs only with PRDY_LIVE=1 and a working token."""
import os

import pytest

from prdy.cli import main

pytestmark = pytest.mark.skipif(not os.environ.get("PRDY_LIVE"), reason="set PRDY_LIVE=1 to hit GitHub")


def test_live_crawl_one_repo(tmp_path, capsys):
    assert main(["crawl", "product requirements document", "--limit", "1", "--out", str(tmp_path)]) == 0
    out = capsys.readouterr().out
    assert out.startswith("Repos examined: 1")
