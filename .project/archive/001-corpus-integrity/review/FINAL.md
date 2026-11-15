# Final Review — reused full wave

Reviewed HEAD: f54cedae0b1deef2e5400082d8a35e3c3887ce3c
Overall verdict: pass
Source review: .project/review/wave-1.cycle1.md
Source commit: ec4feec94fdf105e3dea5b3f08e584bd61369bef

## Success criteria

### SC1 — In one crawl of a repository that contains several candidate source paths which the current scheme stores in one file (the examples `docs/prd.md`, `docs/prd.txt` and `docs__prd.md` together), each path ends with its own corpus document and its own sidecar; each document's text is that path's fetched content and each sidecar's `path` field is that path.

- **Verdict**: met
- **Check**: none
- **Observed**: T001/AC1 evidence: `test_colliding_paths_each_get_own_document_and_sidecar`, recorded T001 Verify exit 0 (`51 passed`). E1 (criterion SC1): the three adjacent paths are the test's inputs. E2 (held-out): `tests/test_store.py::test_document_paths_case_only_difference_stays_distinct` passed in the recorded T001 Verify. E3 (dismissed): the empty-path `tree truncated` row is never written. N1 (criterion SC1): each document's bytes are asserted equal to its own path's content and each sidecar `path` to its own path. Live at Reviewed HEAD: 26 saved rows produced 26 documents and 26 sidecars (SC7 run).
- **Reference**: .project/review/wave-1.cycle1.md — SC1
- **Finding**: none
- **Fix direction**: none

### SC2 — A crawl over a corpus whose index has a saved (not skipped) row with an unchanged `blob_sha` but no document at the location the fixed scheme gives that row fetches the file again and writes the document and sidecar there; that candidate is counted under `Saved`, not `Unchanged`.

- **Verdict**: met
- **Check**: none
- **Observed**: T001/AC2 evidence: `test_saved_row_without_document_is_fetched_again` (blob requests for both rows, saved 2, unchanged 0), recorded T001 Verify exit 0. E4 (criterion SC5): the same test's follow-up crawl fetches nothing and counts unchanged 2. E5 (held-out): `tests/test_crawl.py::test_interrupted_crawl_rows_have_documents_and_next_crawl_completes` passed in the recorded T001 Verify. N2 (criterion SC6): `assert_nothing_lost` plus the byte check of the old-named document in that test.
- **Reference**: .project/review/wave-1.cycle1.md — SC2
- **Finding**: none
- **Fix direction**: none

### SC3 — A row skipped with a reason starting `fetch failed` or `write failed` and an unchanged `blob_sha` is fetched again on every later crawl, with no attempt cap and no backoff. When the retry succeeds the row becomes a saved row with its document; when it fails again the row stays skipped and is counted in the summary's `Skipped` total.

- **Verdict**: met
- **Check**: none
- **Observed**: T002/AC1 evidence: the fetch and write retry tests, recorded T002 Verify exit 0 (`38 passed`). E6 and E7 (criterion SC3): the blob is requested on each of two consecutive later crawls with identical results; `prdy/crawl.py` holds no counter, delay or new index field (`failed_before` is a prefix test only). N3 (criterion SC3): each failing retry is asserted in `summary.skipped` (2, including the truncated repository).
- **Reference**: .project/review/wave-1.cycle1.md — SC3
- **Finding**: none
- **Fix direction**: none

### SC4 — A row skipped as `over 1 MB` or `content sniff` with an unchanged `blob_sha` is not fetched again and is counted under `Unchanged`.

- **Verdict**: met
- **Check**: none
- **Observed**: T002/AC2 evidence: `test_over_1mb_and_content_sniff_rows_are_not_fetched_again`, recorded T002 Verify exit 0. E8 (held-out): `tests/test_crawl.py::test_only_fetch_and_write_failures_are_retried` passed in the recorded T002 Verify. N4 (criterion SC4): no blob request asserted. Live at Reviewed HEAD: 28 `content sniff` rows from the first run were all counted in `Unchanged: 54` on the second run (SC7).
- **Reference**: .project/review/wave-1.cycle1.md — SC4
- **Finding**: none
- **Fix direction**: none

### SC5 — A second crawl over an up-to-date corpus with nothing changed upstream and no `fetch failed` or `write failed` rows fetches no blob, writes no document or sidecar, and counts every candidate under `Unchanged`.

- **Verdict**: met
- **Check**: none
- **Observed**: T002/AC3 evidence: `test_second_crawl_of_up_to_date_corpus_fetches_and_writes_nothing`, recorded T002 Verify exit 0. E9 (held-out): `tests/test_crawl.py::test_crawl_with_no_candidates_writes_nothing` passed in the recorded T002 Verify. N5 (criterion SC5): bytes and modification times of every document and sidecar asserted identical. Live at Reviewed HEAD: second run printed `Saved: 0  Skipped: 0  Unchanged: 54` with 53 files before and after (SC7).
- **Reference**: .project/review/wave-1.cycle1.md — SC5
- **Finding**: none
- **Fix direction**: none

### SC6 — No crawl deletes a file from the corpus folder, and no crawl changes the bytes of a document whose sidecar names a different source path than the one being written. Search space: every file under the corpus folder that existed before the crawl, in the tests that cover criteria 1 and 2. Check: compare the file list and the bytes of those documents before and after the crawl. Absent result: no file missing and no such document changed.

- **Verdict**: met
- **Check**: none
- **Observed**: T001/AC3 evidence over the stated search space: the SC1 test and the SC2 test each take `corpus_files(tmp_path)` before the crawl (including an old-named shared document, its sidecar, and in the SC1 test an unrelated `notes.txt`) and call `assert_nothing_lost` afterwards — no file missing, no such document changed; recorded T001 Verify exit 0. E10 (held-out): `tests/test_crawl.py::test_old_named_document_of_other_path_is_left_unchanged` passed in the recorded T001 Verify. N6 (criterion SC6): the file-list subset assertion. No delete or unlink call exists in the `prdy/crawl.py` or `prdy/store.py` patches.
- **Reference**: .project/review/wave-1.cycle1.md — SC6
- **Finding**: none
- **Fix direction**: none

### SC7 — At the CLI, with the owner's `gh` login, the reviewer runs `uv run prdy crawl "prd" --topic prd --limit 10 --out <temp folder>`. When that run's summary shows `Saved: 0`, the reviewer widens the keywords, qualifiers or `--limit` and runs again into a fresh temporary folder, for at most five attempts, until a first run saves at least one document; if none does, this criterion is `unverifiable`, not met. That first run and an identical second run into the same folder both exit 0 and print the `Repos examined … Saved … Skipped … Unchanged …` summary line; the second run's summary shows `Saved: 0` unless the first run recorded a `fetch failed` or `write failed` row; then `uv run prdy regrade --out <temp folder>` exits 0 and its `rows examined` number equals the number of rows `uv run prdy list --out <temp folder> --json` prints.

- **Verdict**: met
- **Check**: `gh auth status`; `uv run prdy crawl "prd" --topic prd --limit 10 --out /tmp/tmp.vloGZvznwD` run twice; `uv run prdy list --out /tmp/tmp.vloGZvznwD --json`; `uv run prdy regrade --out /tmp/tmp.vloGZvznwD`
- **Observed**: Step 1: `gh auth status` reported a login to github.com; the folder was new and empty. Step 2, attempt 1: `Repos examined: 10  Candidates: 54  Saved: 26  Skipped: 28  Unchanged: 0`, followed by a `Top by score:` block, exit 0 (success state). The index then held 26 saved rows and 28 `content sniff` rows, no `fetch failed` or `write failed` row. Step 3, identical command into the same folder: `Repos examined: 10  Candidates: 54  Saved: 0  Skipped: 0  Unchanged: 54`, exit 0; 53 files before and after. Step 4: `list --json` exit 0, 26 rows. Step 5: `Regraded: 26 rows examined, 0 scores changed`, exit 0; 26 equals 26. Step 6: confirmed as recorded under N7. Empty, loading and error states did not occur in the live run; the empty state is covered by the E9 held-out test.
- **Reference**: .project/review/wave-1.cycle1.md — SC7; evidence: Walkthrough performed by this reviewer at Reviewed HEAD; attempt 1 of at most 5 saved 26 documents, so no widening was needed. E11 (criterion SC7): the empty case did not occur and the widening rule was not invoked. N7 (judgment): every command wrote only under `/tmp/tmp.vloGZvznwD` (created by `mktemp -d`, outside any repository) or redirected stdout to the session scratch folder; no command carried `--llm`; `GITHUB_TOKEN` and `GH_TOKEN` were not set, and each command ran under `env -u OPENROUTER_API_KEY -u GITHUB_TOKEN -u GH_TOKEN`, so the only credential was the existing `gh` login and no model was called.
- **Finding**: none
- **Fix direction**: none
- **Surface**: CLI

### SC8 — README.md states that a `tree truncated` repository is examined again on each crawl, that `fetch failed` and `write failed` rows are retried on each crawl while `over 1 MB` and `content sniff` rows are not, that a corpus crawled by an earlier version is repaired by its next crawl with old files left in place, and that the corpus assumes a case-sensitive filesystem; its corpus-layout example and its `prdy grade` usage example show file names the fixed scheme produces.

- **Verdict**: met
- **Check**: none
- **Observed**: T002/AC6 and T003/AC1 evidence: `README.md:54-61` carries all four statements; `README.md:46-47` (corpus layout) and `README.md:26` (`prdy grade` usage) show `docs__prd__login.md.md` and `docs__prd__login.md.meta.json`, the names the fixed rule gives `docs/prd/login.md` (asserted in the recorded T002 Verify; the live run at Reviewed HEAD produced names of the same form, for example `examples__url-shortener__before__PRD.md.md`). Recorded T002 and T003 Verify both exit 0. E12 (dismissed): fixed statements, no data shape. N8 (judgment): this reviewer read every changed README passage (lines 26, 46-47, 54-61); each statement maps to SC2, SC3, SC4, SC8 or the E2 and E10 rulings, and none promises letter-case safety, parallel-crawl safety, or recovery of documents overwritten before the fix — the only case statement is that the corpus assumes a case-sensitive filesystem.
- **Reference**: .project/review/wave-1.cycle1.md — SC8
- **Finding**: none
- **Fix direction**: none
