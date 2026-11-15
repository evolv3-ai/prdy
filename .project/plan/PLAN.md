# Plan — prdy

Project verify: `uv run pytest -q`

## Config

- max_review_cycles: 3
- wave_budget: none
- review_panel: off
- finding_skeptics: off

## Wave 1 — corpus integrity

Goal: every source path keeps its own corpus document, an old corpus repairs itself on its next crawl, transient failures are retried, and the README matches the code. If the naming rule cannot keep old-named documents intact (SC6), the milestone returns to define.
Review depth: full

## Surface contract

### CLI — T002

Criteria: SC7
Entry: `uv run prdy crawl "product requirements document" --limit 3 --out <temp folder>`
States: empty — the summary line shows `Saved: 0  Skipped: 0  Unchanged: 0` and the command exits 0; loading — no output until the crawl finishes; error — `crawl aborted: <reason>` on stderr after the partial summary, exit 2, or an auth message and exit 1 when no `gh` login exists; success — the `Repos examined … Candidates … Saved … Skipped … Unchanged …` line, an optional `Top by score:` block, exit 0.
Walkthrough:
1. Create an empty temporary folder outside the repository and confirm `gh auth status` reports a login.
2. Run `uv run prdy crawl "product requirements document" --limit 3 --out <temp folder>`; record the summary line and exit code 0.
3. Run the same command again; record the summary line and exit code 0, and confirm `Saved: 0` unless the first run's index has a row whose `skipped` starts `fetch failed` or `write failed`.
4. Run `uv run prdy list --out <temp folder> --json` and count the rows printed.
5. Run `uv run prdy regrade --out <temp folder>`; confirm exit code 0 and that its `rows examined` number equals the count from step 4.
6. Confirm the recorded commands carry no `--llm` flag, set no token variable, and wrote only under the temporary folder (N7).

## Intent coverage

| Criterion | Task | Acceptance |
|-----------|------|------------|
| SC1 | T001 | AC1 |
| SC2 | T001 | AC2 |
| SC3 | T002 | AC1 |
| SC4 | T002 | AC2 |
| SC5 | T002 | AC3 |
| SC6 | T001 | AC3 |
| SC7 | T002 | AC5 |
| SC8 | T002 | AC6 |

## Held-out checks

| Edge | Task | Test |
|------|------|------|
| E2 | T001 | tests/test_store.py::test_document_paths_case_only_difference_stays_distinct |
| E5 | T001 | tests/test_crawl.py::test_interrupted_crawl_rows_have_documents_and_next_crawl_completes |
| E8 | T002 | tests/test_crawl.py::test_only_fetch_and_write_failures_are_retried |
| E9 | T002 | tests/test_crawl.py::test_crawl_with_no_candidates_writes_nothing |
| E10 | T001 | tests/test_crawl.py::test_old_named_document_of_other_path_is_left_unchanged |

## Dependency notes

- T002 depends on T001 through shared files: both change `prdy/crawl.py`, `tests/test_crawl.py` and `tests/test_cli.py`. T002 also consumes `store.document_paths` as fixed by T001: the README corpus-layout example must show the names that function returns, and the retry branch sits beside T001's missing-document branch in `run_crawl`. A reviewer sees it in T002's diff base, which already contains T001's landing commit.
