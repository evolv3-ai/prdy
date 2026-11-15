#!/usr/bin/env python3
"""Run an existing Core hook except in explicitly migrated project roots."""

import argparse
import json
from pathlib import Path
import subprocess
import sys


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", required=True, action="append", type=Path)
    parser.add_argument("--command", required=True)
    # Windows wrappers record bash: the host ran the original through Git Bash,
    # and shell=True would run it through cmd.exe instead.
    parser.add_argument("--shell", choices=("bash",))
    args = parser.parse_args()
    payload = sys.stdin.buffer.read()
    try:
        event = json.loads(payload)
        cwd = event.get("cwd") if isinstance(event, dict) else None
        if isinstance(cwd, str) and Path(cwd).is_absolute():
            directory = Path(cwd).resolve(strict=True)
            for project in args.repo:
                root = project.resolve(strict=True)
                if directory.is_dir() and (directory == root or root in directory.parents):
                    return 0
    except (OSError, ValueError, RuntimeError):
        # An uncertain event keeps the original hook's protection and errors.
        pass
    if args.shell == "bash":
        sys.path.insert(0, str(Path(__file__).resolve().parent))
        import _common

        result = subprocess.run(_common.bash_argv(args.command), input=payload)
    else:
        result = subprocess.run(args.command, shell=True, input=payload)
    return result.returncode if result.returncode >= 0 else 128 - result.returncode


if __name__ == "__main__":
    raise SystemExit(main())
