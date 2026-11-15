---
id: T001
title: Give every source path its own corpus document and repair old corpora on crawl
wave: 1
deps: []
status: done
agent: build_T001
base: 0c6986e81c5b1751f29d6893f6a8943945193372
worktree: null
task_branch: null
files:
  - prdy/store.py
  - prdy/crawl.py
  - tests/test_store.py
  - tests/test_crawl.py
  - tests/test_regrade.py
  - tests/test_cli.py
---

# T001 — Give every source path its own corpus document and repair old corpora on crawl

## Context

`prdy/store.py:89-94` (`document_paths`) flattens `/` to `__` and replaces the extension with `.md`, so three source files in one upstream repository — a Markdown file and a text file with the same stem in the same folder, plus a top-level file whose own name is that folder and stem joined by a double underscore — all resolve to one corpus file (the exact example paths are in acceptance criterion 1). Index rows stay distinct because they key on `(repo, path)`, but the document and its `.meta.json` sidecar hold whichever path was written last. `prdy/crawl.py:86-95` treats a row with an unchanged `blob_sha` as unchanged, so once the naming rule changes, a corpus crawled earlier would keep rows whose document is not where the new rule looks. `prdy/cli.py` (`cmd_regrade`) and `store.write_meta` / `store.write_document` all locate files through `document_paths`. The owner ruled that an old corpus is repaired by its next crawl, that old-named files are left in place and never deleted, and that there is no migration command.

## Approach

- Change the naming rule inside `store.document_paths` so that distinct source paths in one repository always return distinct document and sidecar paths. Keep its signature and keep both files directly inside `store.repo_dir(out, repo)`; the existing "refusing to write outside the repo folder" guards in `write_meta` and `write_document` must still hold.
- The rule is the coder's choice, within these limits: deterministic from `(repo, path)` alone; no new index field; standard library only; file names stay readable enough that a person can tell which source path a document came from.
- In `run_crawl`, a saved (not skipped) row with an unchanged `blob_sha` whose document is not a file at `document_paths(...)[0]` must be fetched and written again, and counted under `Saved`.
- Never delete a file from the corpus. Never change the bytes of an existing document whose sidecar's `path` names a different source path than the one being written; when such a document occupies the location, the new document must still end up stored separately (E10).
- Paths differing only by letter case are out of scope beyond E2: do not add case folding or case-collision handling.
- Do not change `index.jsonl` row fields, exit codes, the rubric, `--llm` behaviour, or the output of `list`, `grade` and `regrade`. `regrade` must keep reading documents through `document_paths`.
- Existing tests that assert the old file names (`tests/test_store.py`, `tests/test_crawl.py`, `tests/test_regrade.py`, `tests/test_cli.py`) are updated to the new rule; none is deleted.
- `cli.py` stays the only module that prints. Tests are plain pytest functions using `httpx.MockTransport` and `tmp_path`, with no network; `tests/test_crawl.py` already has `FakeGitHub` and `OverrideGitHub` to extend.
- Do not touch `README.md`; T002 owns it.

## Interface contract

- `prdy.store.document_paths(out: Path, repo: str, path: str) -> tuple[Path, Path]` — returns `(document, sidecar)`, both directly inside `prdy.store.repo_dir(out, repo)`; the signature is unchanged; distinct `path` values for one `repo` return distinct documents and distinct sidecars. T001 defines the file-name rule; T002's README corpus-layout example shows names this function returns.

## Intent coverage

- SC1
- SC2
- SC6

## Acceptance criteria

1. (SC1, E1) A mocked crawl of one repository whose tree contains `docs/prd.md`, `docs/prd.txt` and `docs__prd.md`, each with different PRD content, ends with three documents and three sidecars; each document's text is that path's fetched content and each sidecar's `path` field is that path.
2. (SC2) A crawl over a corpus whose index has a saved row with an unchanged `blob_sha` and no document at `document_paths(...)[0]` requests that blob again, writes the document and sidecar there, and counts the candidate under `Saved`, not `Unchanged`.
3. (SC6, N2, N6) In the tests for criteria 1 and 2, every file that existed under the corpus folder before the crawl still exists afterwards, and every pre-existing document whose sidecar names a different source path is byte-identical afterwards.
4. (E2, held-out) `tests/test_store.py::test_document_paths_case_only_difference_stays_distinct` shows that `docs/PRD.md` and `docs/prd.md` return different documents; ruling: paths differing only by letter case are not handled, the corpus assumes a case-sensitive filesystem, and on one each such path still gets its own document.
5. (E5, held-out) `tests/test_crawl.py::test_interrupted_crawl_rows_have_documents_and_next_crawl_completes` aborts a crawl between two candidates and shows that every saved row already in the index has its document on disk and that the next crawl saves the rest; ruling: two crawls at once on one corpus are unsupported, with no guarantee.
6. (E10, held-out) `tests/test_crawl.py::test_old_named_document_of_other_path_is_left_unchanged` places an old-named document and sidecar belonging to another source path at the location the new rule gives a path, crawls, and shows the old document's bytes unchanged and the new path's document stored separately; ruling: old-named files are left in place, never deleted.
7. `uv run prdy regrade` on a corpus written by the new rule examines every saved row (the existing `tests/test_regrade.py` behaviour holds under the new names).

## Verify

```bash
uv run pytest -q tests/test_store.py tests/test_crawl.py tests/test_regrade.py tests/test_cli.py
```

Heavy: no

## Log

- 2026-11-15 — created by the plan orchestrator (quick lane)
- 2026-11-15 — coder build_T001: implemented. Naming rule (`prdy/store.py` `document_paths`): `/` becomes `__`, the source extension is kept and `.md` / `.meta.json` is appended (`docs/prd.md` -> `docs__prd.md.md` + `docs__prd.md.meta.json`, `docs/prd.txt` -> `docs__prd.txt.md`); `%`, `\` and any `_` touching another `_` or a segment edge are percent-escaped so a literal underscore never reads as a separator (top-level `docs__prd.md` -> `docs%5F%5Fprd.md.md`). `prdy/crawl.py`: a saved row with an unchanged `blob_sha` whose document is not a file at `document_paths(...)[0]` is fetched and written again. Tests: old-name assertions updated in `tests/test_store.py` and `tests/test_crawl.py`; new tests added there and in `tests/test_regrade.py`, including the three held-out tests; `tests/test_cli.py` needed no change (it asserts no file names).
- 2026-11-15 — coder build_T001: decision for the reviewer to check. The Approach asks for a rule "deterministic from (repo, path) alone" and also that, when the location is occupied by a document whose sidecar names a different source path, the new document "must still end up stored separately" while `regrade` keeps reading through `document_paths`. To meet all three, `document_paths` reads the sidecar at the location: only when it exists and names a different path does it return the same name plus a digest of the path (`<name>.<sha256[:12]>.md`). Every candidate name is a function of `(repo, path)` alone and no index field is added, but the choice between them depends on that pre-existing sidecar. On a corpus with no such foreign sidecar the result depends on `(repo, path)` only.
- 2026-11-15 — coder build_T001: Verify `uv run pytest -q tests/test_store.py tests/test_crawl.py tests/test_regrade.py tests/test_cli.py` -> 51 passed, 0 failed. Full suite `uv run pytest -q` result recorded in the coder's report.
- 2026-11-15 — orchestrator Verify (sidecar gsd-path-verify/task-t001-verify): pass, exit 0; output tail:
  ```
  ...................................................                      [100%]
  51 passed in 0.37s
  Using CPython 3.13.2
  Creating virtual environment at: .venv
     Building prdy @ file:///home/wsladmin/.gsd-path/projects/faceeaa45fdf777af605b55b81575cdc6b492468a1464cf78e4910df2c1739b6/c28fd1b867f62c0f33ed2d82e0df0ac6fba0cd81dbdf93ad0232a6bd66bcaf23/verify/task-t001-verify
        Built prdy @ file:///home/wsladmin/.gsd-path/projects/faceeaa45fdf777af605b55b81575cdc6b492468a1464cf78e4910df2c1739b6/c28fd1b867f62c0f33ed2d82e0df0ac6fba0cd81dbdf93ad0232a6bd66bcaf23/verify/task-t001-verify
  Installed 12 packages in 5ms
  ```
