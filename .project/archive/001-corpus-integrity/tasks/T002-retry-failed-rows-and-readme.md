---
id: T002
title: Retry fetch and write failures on every crawl and correct the README
wave: 1
deps: [T001]
status: done
agent: build_T002
base: 7112c1831e5de033d3e7fb76bd8888394fa3a98d
worktree: null
task_branch: null
files:
  - prdy/crawl.py
  - tests/test_crawl.py
  - tests/test_cli.py
  - README.md
---

# T002 — Retry fetch and write failures on every crawl and correct the README

## Context

`prdy/crawl.py:111-116` and `:130-135` record a candidate whose fetch or write failed as an index row with `skipped` set to `fetch failed: <reason>` or `write failed: <reason>` and its `blob_sha`. On a later crawl `prdy/crawl.py:93-95` counts any row with an unchanged `blob_sha` as unchanged, so the file is never fetched again until it changes upstream. The owner ruled that both reasons are retried on every crawl with no cap or backoff, while `over 1 MB` and `content sniff` rows are not retried. `README.md` (the paragraph after "Row fields") says skipped candidates including `tree truncated` "keep an index row so they are not re-examined"; a tree-truncated repository is examined again on every crawl (`prdy/crawl.py:74-76` records no per-file rows), which is DOCS-AUDIT queue row 28, ruled `fix-doc`. T001 has already changed the corpus file-naming rule and made a crawl re-fetch a saved row whose document is missing.

## Approach

- In `run_crawl`, an existing row whose `skipped` starts with `fetch failed` or `write failed` is not treated as unchanged: fetch it again even when `blob_sha` matches. Success makes it a saved row with document and sidecar; another failure keeps it a skipped row, recorded through the existing `record` path so it is counted in `Skipped`.
- Rows skipped as `over 1 MB` or `content sniff`, and saved rows whose document is present, keep today's unchanged behaviour. Do not add a retry counter, backoff, or index field.
- Leave T001's missing-document branch working; both conditions live beside each other in the same loop.
- README.md: correct the re-crawl paragraph and the corpus-layout example only. State what criterion 6 below lists and nothing more. N8 (judgment): the README must not promise letter-case safety, parallel-crawl safety, or recovery of documents already overwritten before the fix; each changed statement must match an INTENT success criterion or recorded ruling.
- N7 (judgment): the live check belongs to final review only. Tests in this task use `httpx.MockTransport` and `tmp_path`; nothing in this task calls the network, uses `--llm`, or reads a token.
- The CLI test for criterion 5 drives `prdy.cli.main([...])` with the patched GitHub transport already used in `tests/test_cli.py` (`patched_github`) and reads the printed output with `capsys`.
- `cli.py` stays the only module that prints and is not in this task's files: the summary format and exit codes do not change.
- Do not edit `docs/superpowers/`, `specs/`, any skill document, `justfile`, `just/`, `adws/`, `sandbox_mount/` or `.env.sample`.

## Interface contract

- `prdy.store.document_paths(out: Path, repo: str, path: str) -> tuple[Path, Path]` — returns `(document, sidecar)`, both directly inside `prdy.store.repo_dir(out, repo)`; the signature is unchanged; distinct `path` values for one `repo` return distinct documents and distinct sidecars. T001 defines the file-name rule; T002's README corpus-layout example shows names this function returns.

## Intent coverage

- SC3
- SC4
- SC5
- SC7
- SC8

## Acceptance criteria

1. (SC3, E6, E7, N3) A row skipped with a reason starting `fetch failed` or `write failed` and an unchanged `blob_sha` has its blob requested again on each of two further crawls while it keeps failing, and each of those crawls counts it in `Skipped`; when the fetch or write then succeeds, the row becomes a saved row with its document and sidecar and is counted in `Saved`.
2. (SC4, N4) A row skipped as `over 1 MB` or `content sniff` with an unchanged `blob_sha` causes no blob request on a later crawl and is counted under `Unchanged`.
3. (SC5, E4, N5) A second crawl over an up-to-date corpus with nothing changed upstream and no `fetch failed` or `write failed` rows makes no blob request, leaves every document and sidecar's bytes and modification unchanged, and counts every candidate under `Unchanged`.
4. (E8, held-out) `tests/test_crawl.py::test_only_fetch_and_write_failures_are_retried` covers all five skip reasons in one corpus; ruling: only reasons starting `fetch failed` or `write failed` are retried, and `over 1 MB`, `content sniff` and `tree truncated` rows keep today's behaviour. (E9, held-out) `tests/test_crawl.py::test_crawl_with_no_candidates_writes_nothing` shows a crawl with no repositories, and one whose repositories have no candidates, writes no document, reports `Saved: 0`, `Skipped: 0`, `Unchanged: 0`, and has no error; ruling: exit 0 as today.
5. (SC7) A test in `tests/test_cli.py` runs `main(["crawl", ...])` twice into one temporary corpus against the mocked GitHub, then `main(["list", "--out", ..., "--json"])` and `main(["regrade", "--out", ...])`: both crawls return 0 and print the `Repos examined … Saved … Skipped … Unchanged …` line, the second prints `Saved: 0`, and regrade's `rows examined` number equals the number of rows `list --json` printed.
6. (SC8) README.md states that a `tree truncated` repository is examined again on each crawl; that `fetch failed` and `write failed` rows are retried on each crawl while `over 1 MB` and `content sniff` rows are not; that a corpus crawled by an earlier version is repaired by its next crawl with old files left in place; and that the corpus assumes a case-sensitive filesystem. Its corpus-layout example shows file names that `store.document_paths` returns for `docs/prd/login.md`. The sentence "so they are not re-examined" no longer appears.

## Verify

```bash
uv run pytest -q tests/test_crawl.py tests/test_cli.py && grep -q "case-sensitive" README.md && ! grep -q "so they are not re-examined" README.md
```

Heavy: no

## Log

- 2026-11-15 — created by the plan orchestrator (quick lane)
- 2026-11-15 — coder build_T002: `prdy/crawl.py` — `run_crawl` no longer counts a row as unchanged when its `skipped` starts with `fetch failed` or `write failed` (`RETRIED_SKIPS`), beside T001's missing-document condition; no counter, backoff, or index field. `tests/test_crawl.py` — added `test_failed_fetch_is_retried_on_every_crawl_until_it_succeeds`, `test_failed_write_is_retried_on_every_crawl_until_it_succeeds`, `test_over_1mb_and_content_sniff_rows_are_not_fetched_again`, `test_second_crawl_of_up_to_date_corpus_fetches_and_writes_nothing`, held-out `test_only_fetch_and_write_failures_are_retried` (E8) and `test_crawl_with_no_candidates_writes_nothing` (E9). `tests/test_cli.py` — added `test_crawl_twice_then_list_and_regrade_agree` (SC7, mocked GitHub). `README.md` — re-crawl paragraph rewritten and corpus-layout example changed to `docs__prd__login.md.md` / `docs__prd__login.md.meta.json`, the names `store.document_paths` returned for `docs/prd/login.md` when called. Verify `uv run pytest -q tests/test_crawl.py tests/test_cli.py && grep -q "case-sensitive" README.md && ! grep -q "so they are not re-examined" README.md`: pass, exit 0, 38 passed. Full `uv run pytest -q`: 168 passed, 1 skipped. No network, `--llm`, or token used. Not changed, outside this task's allowed README passages: the Usage example `uv run prdy grade ./corpus/acme__widgets/docs__prd__login.md` (README line 26) still shows the pre-T001 file name. The retry tests were not run against the unfixed code.
- 2026-11-15 — orchestrator Verify (sidecar gsd-path-verify/task-t002-verify): pass, exit 0; output tail:
  ```
  ......................................                                   [100%]
  38 passed in 0.40s
  Using CPython 3.13.2
  Creating virtual environment at: .venv
     Building prdy @ file:///home/wsladmin/.gsd-path/projects/faceeaa45fdf777af605b55b81575cdc6b492468a1464cf78e4910df2c1739b6/c28fd1b867f62c0f33ed2d82e0df0ac6fba0cd81dbdf93ad0232a6bd66bcaf23/verify/task-t002-verify
        Built prdy @ file:///home/wsladmin/.gsd-path/projects/faceeaa45fdf777af605b55b81575cdc6b492468a1464cf78e4910df2c1739b6/c28fd1b867f62c0f33ed2d82e0df0ac6fba0cd81dbdf93ad0232a6bd66bcaf23/verify/task-t002-verify
  Installed 12 packages in 5ms
  ```
