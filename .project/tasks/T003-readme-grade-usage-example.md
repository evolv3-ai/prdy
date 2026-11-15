---
id: T003
title: Show a real corpus file name in the README grade usage example
wave: 1
deps: [T002]
status: pending
agent: null
base: null
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
