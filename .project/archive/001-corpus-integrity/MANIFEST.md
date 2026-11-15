# Archive — 001-corpus-integrity

Milestone: corpus-integrity
Shipped: 2026-11-15
Final verdict: all criteria met; project verify passed
Waves: 1  Tasks: 3 done / 3 total  Review cycles used: 1
Carried forward: none

## Success criteria at ship

| Criterion | Verdict | Evidence |
|-----------|---------|----------|
| In one crawl of a repository that contains several candidate source paths which the current scheme stores in one file (the examples `docs/prd.md`, `docs/prd.txt` and `docs__prd.md` together), each path ends with its own corpus document and its own sidecar; each document's text is that path's fetched content and each sidecar's `path` field is that path. | met | .project/review/wave-1.cycle1.md — SC1 |
| A crawl over a corpus whose index has a saved (not skipped) row with an unchanged `blob_sha` but no document at the location the fixed scheme gives that row fetches the file again and writes the document and sidecar there; that candidate is counted under `Saved`, not `Unchanged`. | met | .project/review/wave-1.cycle1.md — SC2 |
| A row skipped with a reason starting `fetch failed` or `write failed` and an unchanged `blob_sha` is fetched again on every later crawl, with no attempt cap and no backoff. When the retry succeeds the row becomes a saved row with its document; when it fails again the row stays skipped and is counted in the summary's `Skipped` total. | met | .project/review/wave-1.cycle1.md — SC3 |
| A row skipped as `over 1 MB` or `content sniff` with an unchanged `blob_sha` is not fetched again and is counted under `Unchanged`. | met | .project/review/wave-1.cycle1.md — SC4 |
| A second crawl over an up-to-date corpus with nothing changed upstream and no `fetch failed` or `write failed` rows fetches no blob, writes no document or sidecar, and counts every candidate under `Unchanged`. | met | .project/review/wave-1.cycle1.md — SC5 |
| No crawl deletes a file from the corpus folder, and no crawl changes the bytes of a document whose sidecar names a different source path than the one being written. Search space: every file under the corpus folder that existed before the crawl, in the tests that cover criteria 1 and 2. Check: compare the file list and the bytes of those documents before and after the crawl. Absent result: no file missing and no such document changed. | met | .project/review/wave-1.cycle1.md — SC6 |
| At the CLI, with the owner's `gh` login, the reviewer runs `uv run prdy crawl "prd" --topic prd --limit 10 --out <temp folder>`. When that run's summary shows `Saved: 0`, the reviewer widens the keywords, qualifiers or `--limit` and runs again into a fresh temporary folder, for at most five attempts, until a first run saves at least one document; if none does, this criterion is `unverifiable`, not met. That first run and an identical second run into the same folder both exit 0 and print the `Repos examined … Saved … Skipped … Unchanged …` summary line; the second run's summary shows `Saved: 0` unless the first run recorded a `fetch failed` or `write failed` row; then `uv run prdy regrade --out <temp folder>` exits 0 and its `rows examined` number equals the number of rows `uv run prdy list --out <temp folder> --json` prints. | met | .project/review/wave-1.cycle1.md — SC7; evidence: Walkthrough performed by this reviewer at Reviewed HEAD; attempt 1 of at most 5 saved 26 documents, so no widening was needed. E11 (criterion SC7): the empty case did not occur and the widening rule was not invoked. N7 (judgment): every command wrote only under `/tmp/tmp.vloGZvznwD` (created by `mktemp -d`, outside any repository) or redirected stdout to the session scratch folder; no command carried `--llm`; `GITHUB_TOKEN` and `GH_TOKEN` were not set, and each command ran under `env -u OPENROUTER_API_KEY -u GITHUB_TOKEN -u GH_TOKEN`, so the only credential was the existing `gh` login and no model was called. |
| README.md states that a `tree truncated` repository is examined again on each crawl, that `fetch failed` and `write failed` rows are retried on each crawl while `over 1 MB` and `content sniff` rows are not, that a corpus crawled by an earlier version is repaired by its next crawl with old files left in place, and that the corpus assumes a case-sensitive filesystem; its corpus-layout example and its `prdy grade` usage example show file names the fixed scheme produces. | met | .project/review/wave-1.cycle1.md — SC8 |

## Contents

- build/evidence.json
- build/verify-ledger.jsonl
- intent/INTENT.md
- plan/PLAN.md
- plan/build-recovery-f9f19a83cbaf229ebf0bf062e875ac360b8ce20a/review/wave-1.cycle1.md
- research/DOCS-AUDIT.md
- research/SYNTHESIS.md
- research/evidence-codebase.md
- review/FINAL.md
- review/final-gap-1.md
- review/wave-1.cycle1.md
- tasks/T001-distinct-corpus-documents.md
- tasks/T002-retry-failed-rows-and-readme.md
- tasks/T003-readme-grade-usage-example.md

## Notes

- none
