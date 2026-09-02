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


@pytest.mark.parametrize("status, exc", [(404, SkipRepo), (403, SkipRepo), (401, AuthError), (422, GitHubError), (500, GitHubError)])
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
