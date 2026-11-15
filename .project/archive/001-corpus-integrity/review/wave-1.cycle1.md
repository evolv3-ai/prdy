# Review — wave 1, cycle 1

Reviewed HEAD: ec4feec94fdf105e3dea5b3f08e584bd61369bef
Review scope: final

Wave verdict: pass
Cycle: 1
Depth: full
Tasks reviewed: 3

Inspection mode: Immutable patch. Identities proven with `git rev-parse` and `git ls-tree` in the combined checkout at Reviewed HEAD (worktree clean before and after the review, apart from this file):

- T001: `a4f503128882c8778a97a9eb31f2459b500250c3^` = `0c6986e81c5b1751f29d6893f6a8943945193372` (recorded base). Changed paths: the task file, `prdy/crawl.py`, `prdy/store.py`, `tests/test_crawl.py`, `tests/test_regrade.py`, `tests/test_store.py` — all declared. HEAD blobs equal the landing blobs for `prdy/store.py` (6dabc30), `tests/test_store.py` (a4c1c54), `tests/test_regrade.py` (20a781f); `prdy/crawl.py` and `tests/test_crawl.py` were changed later by T002, so T001 was judged from the landing commit's own patch, not from the checkout.
- T002: `c2de8abecb4e79b3b1dc07d992ceb4e362a80ba9^` = `7112c1831e5de033d3e7fb76bd8888394fa3a98d` (recorded base). Changed paths: the task file, `README.md`, `prdy/crawl.py`, `tests/test_cli.py`, `tests/test_crawl.py` — all declared. HEAD blobs equal the landing blobs for `prdy/crawl.py` (e3a859c), `tests/test_crawl.py` (cca15a8), `tests/test_cli.py` (ba09b3d); `README.md` was changed later by T003 and its T002 passages were read in the T002 patch and confirmed unchanged by the one-line T003 patch.
- T003: `bc7737d72750417fbe0dffb953c659a0a99d618e^` = `d5ddbe11c32705c214660c827af31840941efe00` (recorded base). Changed paths: the task file and `README.md` — both declared. HEAD blob of `README.md` (96745fc) equals the landing blob.
- Task-file changes in all three landing commits are limited to `status`, `agent`, `base` and appended Log entries; no contract body changed.

## T001 — Give every source path its own corpus document and repair old corpora on crawl: pass

- ✅ T001/AC1 — `tests/test_crawl.py::test_colliding_paths_each_get_own_document_and_sidecar` (landing patch) crawls `docs/prd.md`, `docs/prd.txt` and `docs__prd.md` with different content, asserts summary (3 candidates, 3 saved), each document's bytes equal that path's content, each sidecar `path` equals that path, and six distinct files. Recorded orchestrator Verify (sidecar gsd-path-verify/task-t001-verify, ledger commit a4f5031): exit 0, `51 passed`.
- ✅ T001/AC2 — `test_saved_row_without_document_is_fetched_again` seeds two saved rows with unchanged `blob_sha` and no document at `document_paths(...)[0]`, asserts both blobs are requested, documents and sidecars written there, and summary saved 2, unchanged 0. Code: `prdy/crawl.py` `lost_document` condition in the T001 patch. Same recorded Verify, exit 0.
- ✅ T001/AC3 — both tests above snapshot the corpus with `corpus_files` before the crawl and call `assert_nothing_lost` (file list is a subset afterwards; every pre-existing document whose sidecar names another path is byte-identical), plus explicit byte checks of the old-named document. Same recorded Verify, exit 0.
- ✅ T001/AC4 — E2 held-out: `tests/test_store.py::test_document_paths_case_only_difference_stays_distinct` exists in the landing patch with the ruling stated, asserts `docs/PRD.md` and `docs/prd.md` give different documents and sidecars. Included in the recorded Verify (`tests/test_store.py`), exit 0.
- ✅ T001/AC5 — E5 held-out: `tests/test_crawl.py::test_interrupted_crawl_rows_have_documents_and_next_crawl_completes` aborts on the second candidate, asserts the one recorded row has its document and sidecar, and that the next crawl saves the other two (saved 2, unchanged 1). Ruling stated in the test. Recorded Verify, exit 0.
- ✅ T001/AC6 — E10 held-out: `tests/test_crawl.py::test_old_named_document_of_other_path_is_left_unchanged` places an old-named document and sidecar of `prd.md.txt` at the location for `prd.md`, crawls, asserts old document and sidecar bytes unchanged, the new document stored at a different path with the right text and sidecar `path`, and no fetch on the next crawl. Ruling stated in the test. Recorded Verify, exit 0.
- ✅ T001/AC7 — `tests/test_regrade.py::test_regrade_examines_rows_whose_old_names_collided` asserts `3 rows examined` and per-path grades; the existing regrade tests are unchanged and pass in the same recorded Verify. Also observed live at Reviewed HEAD: `Regraded: 26 rows examined` on a corpus of 26 saved rows (see SC7).
- ✅ T001/IF1 — `prdy/store.py` `document_paths` (landing patch, blob 6dabc30 at HEAD): signature `(out, repo, path)` unchanged; both returned paths are `folder / ...` with `folder = repo_dir(out, repo)`; distinctness asserted over twelve formerly merging paths by `test_document_paths_distinct_for_paths_the_old_rule_merged` (distinct documents, distinct sidecars, parent equals the repo folder). Recorded Verify, exit 0.

Warnings (non-blocking):
- The Approach line "deterministic from `(repo, path)` alone" is met only on a corpus with no foreign sidecar: when a sidecar at the location names another path, `document_paths` returns the name plus a digest of the path. The coder logged this; it is what acceptance criterion 6 and the E10 ruling require, and no acceptance or interface criterion is contradicted. The Approach wording could be tightened.
- `tests/test_cli.py` is declared in `files` but was not changed; no criterion requires a change there.

Contract violations (blocking):
- none

## T002 — Retry fetch and write failures on every crawl and correct the README: pass

- ✅ T002/AC1 — `test_failed_fetch_is_retried_on_every_crawl_until_it_succeeds` and `test_failed_write_is_retried_on_every_crawl_until_it_succeeds` (landing patch): on each of two further crawls the blob is requested again and the summary is (3 candidates, 0 saved, 2 skipped, 2 unchanged) with the row still `fetch failed: ` or `write failed: `; after the failure is removed the row is saved, document and sidecar exist, summary saved 1. Code: `RETRIED_SKIPS` and `failed_before` in `prdy/crawl.py`. Recorded orchestrator Verify (sidecar gsd-path-verify/task-t002-verify, ledger commit c2de8ab): exit 0, `38 passed`.
- ✅ T002/AC2 — `test_over_1mb_and_content_sniff_rows_are_not_fetched_again` asserts no blob request on the later crawl, `unchanged == 3`, and both rows equal their earlier values. Recorded Verify, exit 0.
- ✅ T002/AC3 — `test_second_crawl_of_up_to_date_corpus_fetches_and_writes_nothing` asserts no blob request, `tree_files` (bytes and `st_mtime_ns` of every document and sidecar) identical, `unchanged == candidates == 3`, saved 0. Recorded Verify, exit 0.
- ✅ T002/AC4 — E8 held-out: `tests/test_crawl.py::test_only_fetch_and_write_failures_are_retried` builds all five skip reasons in one corpus and asserts over two later crawls that only the fetch-failed and write-failed blobs are requested, the truncated tree is examined again, summary (4, 0, 3, 2). E9 held-out: `tests/test_crawl.py::test_crawl_with_no_candidates_writes_nothing` covers no repositories and repositories without candidates, asserts empty corpus, the printed `Candidates: 0  Saved: 0  Skipped: 0  Unchanged: 0`, empty stderr and exit 0. Both rulings stated in the tests. Recorded Verify, exit 0.
- ✅ T002/AC5 — `tests/test_cli.py::test_crawl_twice_then_list_and_regrade_agree` runs `main(["crawl", ...])` twice, `list --json` and `regrade`; asserts both crawls return 0 and match the summary-line pattern, the second prints `Saved: 0`, and the `rows examined` number equals the listed row count. Recorded Verify, exit 0.
- ✅ T002/AC6 — `README.md:54-61` at Reviewed HEAD (unchanged from the T002 patch): "A `tree truncated` repository has no per-file rows and is examined again on each crawl", "`fetch failed: <reason>` or `write failed: <reason>` are retried on each crawl; rows skipped as `over 1 MB` or `content sniff` are not", "A corpus crawled by an earlier version is repaired by its next crawl ... old files are left in place", "The corpus assumes a case-sensitive filesystem". `README.md:46-47` show `docs__prd__login.md.md` and `docs__prd__login.md.meta.json`, the names `test_second_crawl_of_up_to_date_corpus_fetches_and_writes_nothing` asserts for `docs/prd/login.md`. `grep` for "re-examined" in `README.md` returns nothing; the recorded Verify's two `grep` clauses passed, exit 0.
- ✅ T002/IF1 — the README corpus-layout example (`README.md:46-47`) shows the names `store.document_paths` returns for `docs/prd/login.md`, per the assertion cited under AC6; T002 did not change `prdy/store.py` (blob 6dabc30 in both landing commits).

Warnings (non-blocking):
- The coder's Log states the retry tests were not run against the unfixed code. The tests assert blob requests that the pre-fix `unchanged` branch could not produce, so they can fail meaningfully.

Contract violations (blocking):
- none

## T003 — Show a real corpus file name in the README grade usage example: pass

- ✅ T003/AC1 — `README.md:26` at Reviewed HEAD reads `uv run prdy grade ./corpus/acme__widgets/docs__prd__login.md.md`; `grep` for `docs__` in `README.md` returns only lines 26, 46 and 47, none ending with `docs__prd__login.md`. Recorded orchestrator Verify (sidecar gsd-path-verify/task-t003-verify, ledger commit bc7737d): exit 0.
- ✅ T003/AC2 — `git show bc7737d72750417fbe0dffb953c659a0a99d618e -- README.md` shows one hunk with one removed and one added line (the `prdy grade` line); the only other path in the commit is the task file.
- ✅ T003/IF1 — Interface contract is `None`; nothing exchanged with another task.

Warnings (non-blocking):
- none

Contract violations (blocking):
- none

## Intent coverage

### SC1 — In one crawl of a repository that contains several candidate source paths which the current scheme stores in one file (the examples `docs/prd.md`, `docs/prd.txt` and `docs__prd.md` together), each path ends with its own corpus document and its own sidecar; each document's text is that path's fetched content and each sidecar's `path` field is that path.: pass
- ✅ T001/AC1 evidence: `test_colliding_paths_each_get_own_document_and_sidecar`, recorded T001 Verify exit 0 (`51 passed`). E1 (criterion SC1): the three adjacent paths are the test's inputs. E2 (held-out): `tests/test_store.py::test_document_paths_case_only_difference_stays_distinct` passed in the recorded T001 Verify. E3 (dismissed): the empty-path `tree truncated` row is never written. N1 (criterion SC1): each document's bytes are asserted equal to its own path's content and each sidecar `path` to its own path. Live at Reviewed HEAD: 26 saved rows produced 26 documents and 26 sidecars (SC7 run).

### SC2 — A crawl over a corpus whose index has a saved (not skipped) row with an unchanged `blob_sha` but no document at the location the fixed scheme gives that row fetches the file again and writes the document and sidecar there; that candidate is counted under `Saved`, not `Unchanged`.: pass
- ✅ T001/AC2 evidence: `test_saved_row_without_document_is_fetched_again` (blob requests for both rows, saved 2, unchanged 0), recorded T001 Verify exit 0. E4 (criterion SC5): the same test's follow-up crawl fetches nothing and counts unchanged 2. E5 (held-out): `tests/test_crawl.py::test_interrupted_crawl_rows_have_documents_and_next_crawl_completes` passed in the recorded T001 Verify. N2 (criterion SC6): `assert_nothing_lost` plus the byte check of the old-named document in that test.

### SC3 — A row skipped with a reason starting `fetch failed` or `write failed` and an unchanged `blob_sha` is fetched again on every later crawl, with no attempt cap and no backoff. When the retry succeeds the row becomes a saved row with its document; when it fails again the row stays skipped and is counted in the summary's `Skipped` total.: pass
- ✅ T002/AC1 evidence: the fetch and write retry tests, recorded T002 Verify exit 0 (`38 passed`). E6 and E7 (criterion SC3): the blob is requested on each of two consecutive later crawls with identical results; `prdy/crawl.py` holds no counter, delay or new index field (`failed_before` is a prefix test only). N3 (criterion SC3): each failing retry is asserted in `summary.skipped` (2, including the truncated repository).

### SC4 — A row skipped as `over 1 MB` or `content sniff` with an unchanged `blob_sha` is not fetched again and is counted under `Unchanged`.: pass
- ✅ T002/AC2 evidence: `test_over_1mb_and_content_sniff_rows_are_not_fetched_again`, recorded T002 Verify exit 0. E8 (held-out): `tests/test_crawl.py::test_only_fetch_and_write_failures_are_retried` passed in the recorded T002 Verify. N4 (criterion SC4): no blob request asserted. Live at Reviewed HEAD: 28 `content sniff` rows from the first run were all counted in `Unchanged: 54` on the second run (SC7).

### SC5 — A second crawl over an up-to-date corpus with nothing changed upstream and no `fetch failed` or `write failed` rows fetches no blob, writes no document or sidecar, and counts every candidate under `Unchanged`.: pass
- ✅ T002/AC3 evidence: `test_second_crawl_of_up_to_date_corpus_fetches_and_writes_nothing`, recorded T002 Verify exit 0. E9 (held-out): `tests/test_crawl.py::test_crawl_with_no_candidates_writes_nothing` passed in the recorded T002 Verify. N5 (criterion SC5): bytes and modification times of every document and sidecar asserted identical. Live at Reviewed HEAD: second run printed `Saved: 0  Skipped: 0  Unchanged: 54` with 53 files before and after (SC7).

### SC6 — No crawl deletes a file from the corpus folder, and no crawl changes the bytes of a document whose sidecar names a different source path than the one being written. Search space: every file under the corpus folder that existed before the crawl, in the tests that cover criteria 1 and 2. Check: compare the file list and the bytes of those documents before and after the crawl. Absent result: no file missing and no such document changed.: pass
- ✅ T001/AC3 evidence over the stated search space: the SC1 test and the SC2 test each take `corpus_files(tmp_path)` before the crawl (including an old-named shared document, its sidecar, and in the SC1 test an unrelated `notes.txt`) and call `assert_nothing_lost` afterwards — no file missing, no such document changed; recorded T001 Verify exit 0. E10 (held-out): `tests/test_crawl.py::test_old_named_document_of_other_path_is_left_unchanged` passed in the recorded T001 Verify. N6 (criterion SC6): the file-list subset assertion. No delete or unlink call exists in the `prdy/crawl.py` or `prdy/store.py` patches.

### SC7 — At the CLI, with the owner's `gh` login, the reviewer runs `uv run prdy crawl "prd" --topic prd --limit 10 --out <temp folder>`. When that run's summary shows `Saved: 0`, the reviewer widens the keywords, qualifiers or `--limit` and runs again into a fresh temporary folder, for at most five attempts, until a first run saves at least one document; if none does, this criterion is `unverifiable`, not met. That first run and an identical second run into the same folder both exit 0 and print the `Repos examined … Saved … Skipped … Unchanged …` summary line; the second run's summary shows `Saved: 0` unless the first run recorded a `fetch failed` or `write failed` row; then `uv run prdy regrade --out <temp folder>` exits 0 and its `rows examined` number equals the number of rows `uv run prdy list --out <temp folder> --json` prints.: pass
- ✅ Walkthrough performed by this reviewer at Reviewed HEAD; attempt 1 of at most 5 saved 26 documents, so no widening was needed. E11 (criterion SC7): the empty case did not occur and the widening rule was not invoked. N7 (judgment): every command wrote only under `/tmp/tmp.vloGZvznwD` (created by `mktemp -d`, outside any repository) or redirected stdout to the session scratch folder; no command carried `--llm`; `GITHUB_TOKEN` and `GH_TOKEN` were not set, and each command ran under `env -u OPENROUTER_API_KEY -u GITHUB_TOKEN -u GH_TOKEN`, so the only credential was the existing `gh` login and no model was called.
- **Surface**: CLI
- **Check**: `gh auth status`; `uv run prdy crawl "prd" --topic prd --limit 10 --out /tmp/tmp.vloGZvznwD` run twice; `uv run prdy list --out /tmp/tmp.vloGZvznwD --json`; `uv run prdy regrade --out /tmp/tmp.vloGZvznwD`
- **Observed**: Step 1: `gh auth status` reported a login to github.com; the folder was new and empty. Step 2, attempt 1: `Repos examined: 10  Candidates: 54  Saved: 26  Skipped: 28  Unchanged: 0`, followed by a `Top by score:` block, exit 0 (success state). The index then held 26 saved rows and 28 `content sniff` rows, no `fetch failed` or `write failed` row. Step 3, identical command into the same folder: `Repos examined: 10  Candidates: 54  Saved: 0  Skipped: 0  Unchanged: 54`, exit 0; 53 files before and after. Step 4: `list --json` exit 0, 26 rows. Step 5: `Regraded: 26 rows examined, 0 scores changed`, exit 0; 26 equals 26. Step 6: confirmed as recorded under N7. Empty, loading and error states did not occur in the live run; the empty state is covered by the E9 held-out test.

### SC8 — README.md states that a `tree truncated` repository is examined again on each crawl, that `fetch failed` and `write failed` rows are retried on each crawl while `over 1 MB` and `content sniff` rows are not, that a corpus crawled by an earlier version is repaired by its next crawl with old files left in place, and that the corpus assumes a case-sensitive filesystem; its corpus-layout example and its `prdy grade` usage example show file names the fixed scheme produces.: pass
- ✅ T002/AC6 and T003/AC1 evidence: `README.md:54-61` carries all four statements; `README.md:46-47` (corpus layout) and `README.md:26` (`prdy grade` usage) show `docs__prd__login.md.md` and `docs__prd__login.md.meta.json`, the names the fixed rule gives `docs/prd/login.md` (asserted in the recorded T002 Verify; the live run at Reviewed HEAD produced names of the same form, for example `examples__url-shortener__before__PRD.md.md`). Recorded T002 and T003 Verify both exit 0. E12 (dismissed): fixed statements, no data shape. N8 (judgment): this reviewer read every changed README passage (lines 26, 46-47, 54-61); each statement maps to SC2, SC3, SC4, SC8 or the E2 and E10 rulings, and none promises letter-case safety, parallel-crawl safety, or recovery of documents overwritten before the fix — the only case statement is that the corpus assumes a case-sensitive filesystem.

## Summary for orchestrator

- blocked findings: none
- repeat offenders: none
- warnings worth a human eye: T001's `document_paths` consults an existing sidecar to pick between the plain name and a digest-suffixed name, so the Approach phrase "deterministic from `(repo, path)` alone" holds only without a foreign sidecar (required by E10; coder logged it). `OPENROUTER_API_KEY` is present in the ambient shell environment; it was unset for every walkthrough command and no `--llm` flag was used.
