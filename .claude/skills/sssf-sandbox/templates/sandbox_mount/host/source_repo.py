#!/usr/bin/env python3
"""Resolve the public HTTPS URL a sandbox VM clones.

    sandbox_mount/host/source_repo.py            -> prints the URL, exit 0
    sandbox_mount/host/source_repo.py --probe    -> also proves it clones anonymously

SBX_SOURCE_REPO (from .env, loaded by the just module) wins. Otherwise `origin`,
with GitHub's git@ and ssh:// forms rewritten to https. Anything that is not
https:// is refused: the VM has no credential, so only an anonymous clone can work.
"""
from __future__ import annotations

import os
import shutil
import subprocess
import sys
import tempfile
from urllib.parse import urlsplit, urlunsplit

SCP_PREFIX = "git@github.com:"
SSH_PREFIX = "ssh://git@github.com/"


def resolve() -> str:
    url = os.environ.get("SBX_SOURCE_REPO", "").strip()
    if not url:
        proc = subprocess.run(["git", "remote", "get-url", "origin"], capture_output=True, text=True)
        if proc.returncode != 0:
            raise SystemExit("source_repo: no SBX_SOURCE_REPO and no git remote 'origin' — set SBX_SOURCE_REPO in .env")
        url = proc.stdout.strip()
    if url.startswith(SCP_PREFIX):
        url = "https://github.com/" + url[len(SCP_PREFIX):]
    elif url.startswith(SSH_PREFIX):
        url = "https://github.com/" + url[len(SSH_PREFIX):]
    if not url.startswith("https://"):
        raise SystemExit(f"source_repo: '{url}' is not an https:// URL the VM can clone anonymously — set SBX_SOURCE_REPO in .env")
    parts = urlsplit(url)
    if parts.username or parts.password:
        netloc = parts.hostname + (f":{parts.port}" if parts.port else "")
        safe = urlunsplit((parts.scheme, netloc, parts.path, parts.query, parts.fragment))
        raise SystemExit(f"source_repo: '{safe}' carries a credential in the URL — the VM must clone anonymously; use a plain https:// URL")
    return url


def probe(url: str) -> None:
    timeout = float(os.environ.get("SBX_PROBE_TIMEOUT", "60"))
    # Isolate git from the host's config and credential store: a global/system
    # gitconfig (url.insteadOf rewrites, credential helpers) or ~/.netrc could
    # make an otherwise-private repo appear to clone anonymously, hiding a
    # broken assumption from a probe that is supposed to catch exactly that.
    fake_home = tempfile.mkdtemp(prefix="source-repo-probe-")
    env = dict(
        os.environ,
        GIT_TERMINAL_PROMPT="0",
        GIT_ASKPASS="/bin/false",
        GIT_CONFIG_GLOBAL="/dev/null",
        GIT_CONFIG_SYSTEM="/dev/null",
        GIT_CONFIG_NOSYSTEM="1",
        HOME=fake_home,
    )
    try:
        proc = subprocess.run(["git", "-c", "credential.helper=", "ls-remote", "--heads", url], capture_output=True, text=True, env=env, timeout=timeout)
    except subprocess.TimeoutExpired:
        raise SystemExit(f"source_repo: anonymous clone of {url} timed out after {timeout:g}s (is the host reachable?)")
    finally:
        shutil.rmtree(fake_home, ignore_errors=True)
    if proc.returncode != 0:
        raise SystemExit(f"source_repo: anonymous clone of {url} would fail (is the repo public?):\n{proc.stderr.strip()}")


def main(argv: list[str]) -> int:
    url = resolve()
    if "--probe" in argv:
        probe(url)
    print(url)
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main(sys.argv[1:]))
    except SystemExit as exc:
        if isinstance(exc.code, str):
            print(exc.code, file=sys.stderr)
            sys.exit(1)
        raise
