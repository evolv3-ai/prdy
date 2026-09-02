"""Thin, rate-limit-aware GitHub REST client."""
from __future__ import annotations

import os
import subprocess
import time
from collections.abc import Callable, Iterator, Mapping
from urllib.parse import quote

import httpx

API_URL = "https://api.github.com"
JSON_ACCEPT = "application/vnd.github+json"
RAW_ACCEPT = "application/vnd.github.raw+json"
API_VERSION = "2022-11-28"


class SkipRepo(Exception):
    """This repo or file cannot be read (404, non-rate-limit 403). Move on."""


class GitHubError(Exception):
    """Unrecoverable API failure. The crawl stops."""


class AuthError(Exception):
    """The token was rejected."""


def resolve_token(env: Mapping[str, str] | None = None, run=subprocess.run) -> str | None:
    """`gh auth token` when available, else GITHUB_TOKEN, else None."""
    env = os.environ if env is None else env
    try:
        proc = run(["gh", "auth", "token"], capture_output=True, text=True, timeout=10)
        if proc.returncode == 0 and proc.stdout.strip():
            return proc.stdout.strip()
    except (FileNotFoundError, subprocess.TimeoutExpired, OSError):
        pass
    return env.get("GITHUB_TOKEN") or None


class GitHubClient:
    def __init__(
        self,
        token: str,
        http: httpx.Client | None = None,
        sleep: Callable[[float], None] = time.sleep,
        clock: Callable[[], float] = time.time,
        retries: int = 3,
    ) -> None:
        self.token = token
        self.http = http or httpx.Client(base_url=API_URL, timeout=30.0, follow_redirects=True)
        self.sleep = sleep
        self.clock = clock
        self.retries = retries

    def request(self, path: str, params: dict | None = None, accept: str = JSON_ACCEPT) -> httpx.Response:
        headers = {
            "Authorization": f"Bearer {self.token}",
            "Accept": accept,
            "X-GitHub-Api-Version": API_VERSION,
            "User-Agent": "prdy",
        }
        failures = 0
        while True:
            try:
                resp = self.http.get(path, params=params, headers=headers)
            except httpx.TransportError as exc:
                failures += 1
                if failures > self.retries:
                    raise GitHubError(f"network error after {self.retries} retries: {exc}") from exc
                self.sleep(float(2 ** failures))
                continue

            if resp.status_code in (403, 429):
                if resp.headers.get("X-RateLimit-Remaining") == "0":
                    self._sleep_until_reset(resp)
                    continue
                if "secondary rate limit" in resp.text.lower() or "Retry-After" in resp.headers:
                    self.sleep(60.0)
                    continue
                raise SkipRepo(f"{resp.status_code} for {path}")
            if resp.status_code == 404:
                raise SkipRepo(f"404 for {path}")
            if resp.status_code == 401:
                raise AuthError("GitHub rejected the token (401)")
            if resp.status_code >= 400:
                raise GitHubError(f"{resp.status_code} for {path}: {resp.text[:200]}")

            if resp.headers.get("X-RateLimit-Remaining") == "0":
                self._sleep_until_reset(resp)
            return resp

    def _sleep_until_reset(self, resp: httpx.Response) -> None:
        reset = float(resp.headers.get("X-RateLimit-Reset", "0"))
        self.sleep(max(reset - self.clock(), 0.0) + 1.0)
