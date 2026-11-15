---
id: T003
title: Show a real corpus file name in the README grade usage example
wave: 1
deps: [T002]
status: done
agent: build_T003
base: d5ddbe11c32705c214660c827af31840941efe00
worktree: null
task_branch: null
files:
  - README.md
---

# T003 — Show a real corpus file name in the README grade usage example

## Context

T001 changed the corpus file-naming rule in `prdy/store.py` (`document_paths`): the source extension is kept and a Markdown extension is appended, so a stored document's name now ends with a doubled Markdown extension when the upstream file was Markdown. T002 updated the re-crawl paragraph and corpus-layout example of `README.md` to match. The Usage block of `README.md` still has a `prdy grade` line whose corpus file name carries only the single extension, a name the fixed rule no longer produces. The wave 1 cycle 1 review recorded this as a warning, and the owner ruled "Fix it now" (INTENT.md correction C5); success criterion SC8 now requires the `prdy grade` usage example to show a file name the fixed scheme produces.

## Approach

- Change only the `prdy grade` line in the Usage block of `README.md`; the exact required line is in acceptance criterion 1. It is the document name the README corpus-layout example already shows for the same upstream file.
- Do not change any other README line, and do not touch any other file.
- N8 (judgment): the README must not promise letter-case safety, parallel-crawl safety, or recovery of documents already overwritten before the fix; this task adds no new statement.

## Interface contract

- None

## Intent coverage

- SC8

## Acceptance criteria

1. (SC8) The `prdy grade` usage example in `README.md` reads `uv run prdy grade ./corpus/acme__widgets/docs__prd__login.md.md`, and no line of `README.md` ends with `docs__prd__login.md`.
2. `git diff` for this task changes exactly one line of `README.md`.

## Verify

```bash
grep -q 'uv run prdy grade ./corpus/acme__widgets/docs__prd__login.md.md$' README.md && ! grep -q 'docs__prd__login\.md$' README.md
```

Heavy: no

## Log

- 2026-11-15 — created by the plan orchestrator (quick lane, build repair after INTENT.md corrections C4 and C5)
- 2026-11-15 — coder build_t003: preflight clean at base d5ddbe1 (`README.md` and `prdy/store.py` `document_paths` exist; SC8 present in INTENT.md; Interface contract None). Changed the one `prdy grade` line in the README Usage block to `uv run prdy grade ./corpus/acme__widgets/docs__prd__login.md.md`; no other README line or file changed (`git diff --numstat -- README.md`: 1 added, 1 removed). Verify run in the worktree: exit 0.
- 2026-11-15 — orchestrator Verify (sidecar gsd-path-verify/task-t003-verify): pass, exit 0
