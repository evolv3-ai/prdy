import subprocess

import httpx
import pytest

from prdy.github import API_URL, JSON_ACCEPT, AuthError, GitHubClient, GitHubError, SkipRepo, resolve_token


class FakeRun:
    def __init__(self, returncode=0, stdout="", raise_=None):
        self.returncode, self.stdout, self.raise_ = returncode, stdout, raise_

    def __call__(self, *args, **kwargs):
        if self.raise_:
            raise self.raise_
        return subprocess.CompletedProcess(args, self.returncode, self.stdout, "")


def test_resolve_token_prefers_gh():
    assert resolve_token(env={"GITHUB_TOKEN": "envtok"}, run=FakeRun(0, "ghtok\n")) == "ghtok"


def test_resolve_token_falls_back_to_env_when_gh_missing_or_failing():
    assert resolve_token(env={"GITHUB_TOKEN": "envtok"}, run=FakeRun(raise_=FileNotFoundError())) == "envtok"
    assert resolve_token(env={"GITHUB_TOKEN": "envtok"}, run=FakeRun(1, "")) == "envtok"
    assert resolve_token(env={}, run=FakeRun(1, "")) is None


def make_client(handler, clock=lambda: 1000.0, retries=3):
    """GitHubClient over a MockTransport; returns (client, list of sleep durations)."""
    sleeps: list[float] = []
    http = httpx.Client(transport=httpx.MockTransport(handler), base_url=API_URL)
    return GitHubClient("tok", http=http, sleep=sleeps.append, clock=clock, retries=retries), sleeps


def test_request_sends_auth_and_accept_headers():
    seen = {}

    def handler(request):
        seen.update(request.headers)
        return httpx.Response(200, json={"ok": True})

    client, _ = make_client(handler)
    assert client.request("/x").json() == {"ok": True}
    assert seen["authorization"] == "Bearer tok"
    assert seen["accept"] == JSON_ACCEPT
    assert seen["x-github-api-version"] == "2022-11-28"


def test_request_sleeps_until_reset_on_primary_rate_limit():
    calls = []

    def handler(request):
        calls.append(1)
        if len(calls) == 1:
            return httpx.Response(403, headers={"X-RateLimit-Remaining": "0", "X-RateLimit-Reset": "1030"},
                                  json={"message": "API rate limit exceeded"})
        return httpx.Response(200, json={})

    client, sleeps = make_client(handler)
    client.request("/x")
    assert len(calls) == 2
    assert sleeps == [31.0]


def test_request_sleeps_after_success_when_remaining_is_zero():
    def handler(request):
        return httpx.Response(200, headers={"X-RateLimit-Remaining": "0", "X-RateLimit-Reset": "1005"}, json={})

    client, sleeps = make_client(handler)
    client.request("/x")
    assert sleeps == [6.0]


def test_request_secondary_rate_limit_sleeps_60():
    calls = []

    def handler(request):
        calls.append(1)
        if len(calls) == 1:
            return httpx.Response(403, headers={"X-RateLimit-Remaining": "40"},
                                  json={"message": "You have exceeded a secondary rate limit."})
        return httpx.Response(200, json={})

    client, sleeps = make_client(handler)
    client.request("/x")
    assert sleeps == [60.0] and len(calls) == 2


def test_request_honours_retry_after_header_on_secondary_rate_limit():
    calls = []

    def handler(request):
        calls.append(1)
        if len(calls) == 1:
            return httpx.Response(403, headers={"X-RateLimit-Remaining": "40", "Retry-After": "7"}, json={})
        return httpx.Response(200, json={})

    client, sleeps = make_client(handler)
    client.request("/x")
    assert sleeps == [7.0] and len(calls) == 2


def test_request_bare_429_treated_as_secondary_limit():
    calls = []

    def handler(request):
        calls.append(1)
        if len(calls) == 1:
            return httpx.Response(429)
        return httpx.Response(200, json={})

    client, sleeps = make_client(handler)
    client.request("/x")
    assert sleeps == [60.0] and len(calls) == 2


def test_request_negative_retry_after_clamped_to_zero():
    calls = []

    def handler(request):
        calls.append(1)
        if len(calls) == 1:
            return httpx.Response(429, headers={"Retry-After": "-5"})
        return httpx.Response(200, json={})

    client, sleeps = make_client(handler)
    client.request("/x")
    assert sleeps == [0.0] and len(calls) == 2


def test_request_caps_secondary_rate_limit_retries():
    # retries=3 (make_client default) means up to 3 sleeps are tolerated; the 4th
    # secondary-limit response in a row raises GitHubError instead of sleeping again.
    def handler(request):
        return httpx.Response(403, headers={"X-RateLimit-Remaining": "40"},
                              json={"message": "You have exceeded a secondary rate limit."})

    calls = []

    def counting_handler(request):
        calls.append(1)
        return handler(request)

    client, sleeps = make_client(counting_handler)
    with pytest.raises(GitHubError):
        client.request("/x")
    assert len(calls) == 4
    assert sleeps == [60.0, 60.0, 60.0]


@pytest.mark.parametrize("status, exc", [(404, SkipRepo), (403, SkipRepo), (409, SkipRepo), (401, AuthError), (422, GitHubError), (500, GitHubError)])
def test_request_error_mapping(status, exc):
    client, _ = make_client(lambda request: httpx.Response(status, headers={"X-RateLimit-Remaining": "40"}, json={"message": "no"}))
    with pytest.raises(exc):
        client.request("/x")


def test_request_retries_network_errors_with_backoff():
    calls = []

    def handler(request):
        calls.append(1)
        if len(calls) <= 2:
            raise httpx.ConnectError("boom", request=request)
        return httpx.Response(200, json={})

    client, sleeps = make_client(handler)
    client.request("/x")
    assert len(calls) == 3 and sleeps == [2.0, 4.0]


def test_request_gives_up_after_three_network_retries():
    def handler(request):
        raise httpx.ConnectError("boom", request=request)

    client, sleeps = make_client(handler)
    with pytest.raises(GitHubError):
        client.request("/x")
    assert sleeps == [2.0, 4.0, 8.0]


import json

from prdy.github import RAW_ACCEPT


def test_search_repos_pages_and_stops_on_empty_page(fixtures):
    seen = []

    def handler(request):
        seen.append(dict(request.url.params))
        if request.url.params["page"] == "1":
            return httpx.Response(200, json=json.loads((fixtures / "search_page.json").read_text()))
        return httpx.Response(200, json={"total_count": 2, "items": []})

    client, _ = make_client(handler)
    repos = list(client.search_repos("prd stars:>50", limit=5))
    assert [r["full_name"] for r in repos] == ["acme/widgets", "beta/notes"]
    assert seen[0]["q"] == "prd stars:>50"
    assert seen[0]["sort"] == "stars" and seen[0]["per_page"] == "5"
    assert [s["page"] for s in seen] == ["1", "2"]


def test_search_repos_honours_limit_within_a_page(fixtures):
    client, _ = make_client(lambda r: httpx.Response(200, json=json.loads((fixtures / "search_page.json").read_text())))
    assert [r["full_name"] for r in client.search_repos("prd", limit=1)] == ["acme/widgets"]


def test_search_repos_wraps_skip_as_unrecoverable():
    client, _ = make_client(lambda r: httpx.Response(403, headers={"X-RateLimit-Remaining": "40"}, json={}))
    with pytest.raises(GitHubError):
        list(client.search_repos("prd", limit=1))


def test_get_tree_returns_entries_and_truncated_flag(fixtures):
    seen = {}

    def handler(request):
        seen["url"] = str(request.url)
        return httpx.Response(200, json=json.loads((fixtures / "tree_notes.json").read_text()))

    client, _ = make_client(handler)
    entries, truncated = client.get_tree("beta", "notes", "main")
    assert entries == [] and truncated is True
    assert seen["url"] == f"{API_URL}/repos/beta/notes/git/trees/main?recursive=1"


def test_client_closes_only_owned_http():
    injected = httpx.Client(transport=httpx.MockTransport(lambda r: httpx.Response(200, json={})), base_url=API_URL)
    with GitHubClient("t", http=injected) as client:
        assert client.http is injected
    assert injected.is_closed is False
    injected.close()

    with GitHubClient("t") as client:
        pass
    assert client.http.is_closed is True


def test_get_blob_uses_raw_accept_and_quotes_path():
    seen = {}

    def handler(request):
        seen["url"] = str(request.url)
        seen["accept"] = request.headers["accept"]
        return httpx.Response(200, content=b"# PRD\n")

    client, _ = make_client(handler)
    assert client.get_blob("acme", "widgets", "docs/my prd.md", "main") == b"# PRD\n"
    assert seen["url"] == f"{API_URL}/repos/acme/widgets/contents/docs/my%20prd.md?ref=main"
    assert seen["accept"] == RAW_ACCEPT
