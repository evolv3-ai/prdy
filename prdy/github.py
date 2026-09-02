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
        self._owns_http = http is None
        self.http = http or httpx.Client(base_url=API_URL, timeout=30.0, follow_redirects=True)
        self.sleep = sleep
        self.clock = clock
        self.retries = retries

    def close(self) -> None:
        """Close the underlying HTTP client, but only when this client created it."""
        if self._owns_http:
            self.http.close()

    def __enter__(self) -> "GitHubClient":
        return self

    def __exit__(self, *exc_info: object) -> None:
        self.close()

    def request(self, path: str, params: dict | None = None, accept: str = JSON_ACCEPT) -> httpx.Response:
        headers = {
            "Authorization": f"Bearer {self.token}",
            "Accept": accept,
            "X-GitHub-Api-Version": API_VERSION,
            "User-Agent": "prdy",
        }
        failures = 0
        secondary_failures = 0  # consecutive secondary-rate-limit / Retry-After responses; capped by self.retries
        while True:
            try:
                resp = self.http.get(path, params=params, headers=headers)
            except httpx.TransportError as exc:
                failures += 1
                if failures > self.retries:
                    raise GitHubError(f"network error after {self.retries} retries: {exc}") from exc
                self.sleep(float(2 ** failures))
                continue

            not_exhausted = resp.headers.get("X-RateLimit-Remaining") != "0"
            is_secondary_limit = not_exhausted and (
                resp.status_code == 429
                or (
                    resp.status_code == 403
                    and ("secondary rate limit" in resp.text.lower() or "Retry-After" in resp.headers)
                )
            )
            if is_secondary_limit:
                secondary_failures += 1
                if secondary_failures > self.retries:
                    raise GitHubError(
                        f"secondary rate limit for {path} persisted after {self.retries} retries"
                    )
                retry_after = resp.headers.get("Retry-After")
                try:
                    delay = float(retry_after) if retry_after is not None else 60.0
                except ValueError:
                    delay = 60.0
                delay = max(delay, 0.0)
                self.sleep(delay)
                continue
            secondary_failures = 0

            if resp.status_code in (403, 429):
                if resp.headers.get("X-RateLimit-Remaining") == "0":
                    self._sleep_until_reset(resp)
                    continue
                raise SkipRepo(f"{resp.status_code} for {path}")
            if resp.status_code == 404:
                raise SkipRepo(f"404 for {path}")
            if resp.status_code == 409:
                raise SkipRepo(f"409 for {path}")
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

    def search_repos(self, query: str, limit: int) -> Iterator[dict]:
        """Yield repository dicts from /search/repositories, most stars first, up to `limit`."""
        if limit <= 0:
            return
        per_page = min(100, limit)
        yielded, page = 0, 1
        while yielded < limit and page <= 10:  # GitHub search stops at 1000 results
            params = {"q": query, "sort": "stars", "order": "desc", "per_page": per_page, "page": page}
            try:
                resp = self.request("/search/repositories", params)
            except SkipRepo as exc:
                raise GitHubError(f"repository search failed: {exc}") from exc
            items = resp.json().get("items", [])
            if not items:
                return
            for item in items:
                yield item
                yielded += 1
                if yielded >= limit:
                    return
            page += 1

    def get_tree(self, owner: str, repo: str, ref: str) -> tuple[list[dict], bool]:
        resp = self.request(f"/repos/{owner}/{repo}/git/trees/{quote(ref, safe='')}", {"recursive": "1"})
        data = resp.json()
        return data.get("tree", []), bool(data.get("truncated", False))

    def get_blob(self, owner: str, repo: str, path: str, ref: str) -> bytes:
        resp = self.request(f"/repos/{owner}/{repo}/contents/{quote(path, safe='/')}", {"ref": ref}, accept=RAW_ACCEPT)
        return resp.content
