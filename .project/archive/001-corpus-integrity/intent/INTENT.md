# Intent — prdy

Lane: quick   <!-- remaining work after corrections C4 and C5 is one small README task in the same wave; T001 and T002 are landed and unchanged; no RESEARCH or NEEDS-USER items, no cross-wave risk -->

Review panel: off

Finding skeptics: off

Surfaces: CLI

## Summary

prdy's local corpus can silently lose data in two ways: different source
paths in one repository are stored in the same corpus file, and a document
whose fetch or write failed once is never tried again. This milestone fixes
both in `prdy crawl` for the person who builds and re-crawls a corpus, makes
an existing corpus repair itself on its next crawl, and corrects the README
where it misdescribes re-crawl behaviour. GSD Path owns this work; the
installed SSSF factory, sandbox, herdr and `just` material stays untouched.

## Problem

Verified in inspect (`.project/research/evidence-codebase.md`):

- `store.document_paths` flattens `/` to `__` and replaces the extension with
  `.md`, so `docs/prd.md`, `docs/prd.txt` and a file named `docs__prd.md` in
  one repository all resolve to one corpus file. Index rows stay distinct, but
  the document and sidecar hold whichever was written last, so `regrade` and
  `grade` can read a different file's text than the row describes.
- A candidate skipped as `fetch failed` or `write failed` keeps its `blob_sha`
  in the index; a later crawl treats the unchanged `blob_sha` as `unchanged`
  and never fetches it again, so a transient failure is permanent until the
  upstream file changes.
- README.md says skipped candidates including `tree truncated` "keep an index
  row so they are not re-examined"; a tree-truncated repository is in fact
  re-examined on every crawl (DOCS-AUDIT queue row 28).

## Users

The repository owner, a technical single user who runs `prdy crawl` from a
terminal against their own `gh` login and re-crawls the same corpus folder
over time.

## Success criteria

1. In one crawl of a repository that contains several candidate source paths
   which the current scheme stores in one file (the examples `docs/prd.md`,
   `docs/prd.txt` and `docs__prd.md` together), each path ends with its own
   corpus document and its own sidecar; each document's text is that path's
   fetched content and each sidecar's `path` field is that path.
2. A crawl over a corpus whose index has a saved (not skipped) row with an
   unchanged `blob_sha` but no document at the location the fixed scheme
   gives that row fetches the file again and writes the document and sidecar
   there; that candidate is counted under `Saved`, not `Unchanged`.
3. A row skipped with a reason starting `fetch failed` or `write failed` and
   an unchanged `blob_sha` is fetched again on every later crawl, with no
   attempt cap and no backoff. When the retry succeeds the row becomes a
   saved row with its document; when it fails again the row stays skipped
   and is counted in the summary's `Skipped` total.
4. A row skipped as `over 1 MB` or `content sniff` with an unchanged
   `blob_sha` is not fetched again and is counted under `Unchanged`.
5. A second crawl over an up-to-date corpus with nothing changed upstream and
   no `fetch failed` or `write failed` rows fetches no blob, writes no
   document or sidecar, and counts every candidate under `Unchanged`.
6. No crawl deletes a file from the corpus folder, and no crawl changes the
   bytes of a document whose sidecar names a different source path than the
   one being written. Search space: every file under the corpus folder that
   existed before the crawl, in the tests that cover criteria 1 and 2. Check:
   compare the file list and the bytes of those documents before and after
   the crawl. Absent result: no file missing and no such document changed.
7. At the CLI, with the owner's `gh` login, the reviewer runs `uv run prdy
   crawl "prd" --topic prd --limit 10 --out <temp folder>`. When that run's
   summary shows `Saved: 0`, the reviewer widens the keywords, qualifiers or
   `--limit` and runs again into a fresh temporary folder, for at most five
   attempts, until a first run saves at least one document; if none does,
   this criterion is `unverifiable`, not met. That first run and an identical
   second run into the same folder both exit 0 and print the `Repos examined
   … Saved … Skipped … Unchanged …` summary line; the second run's summary
   shows `Saved: 0` unless the first run recorded a `fetch failed` or `write
   failed` row; then `uv run prdy regrade --out <temp folder>` exits 0 and
   its `rows examined` number equals the number of rows `uv run prdy list
   --out <temp folder> --json` prints.
8. README.md states that a `tree truncated` repository is examined again on
   each crawl, that `fetch failed` and `write failed` rows are retried on
   each crawl while `over 1 MB` and `content sniff` rows are not, that a
   corpus crawled by an earlier version is repaired by its next crawl with
   old files left in place, and that the corpus assumes a case-sensitive
   filesystem; its corpus-layout example and its `prdy grade` usage example
   show file names the fixed scheme produces.

## Edge coverage

| Edge | Criterion | Category | Disposition | Detail |
|------|-----------|----------|-------------|--------|
| E1 | SC1 | adjacency | criterion SC1 | |
| E2 | SC1 | encoding | held-out | Source paths that differ only by letter case (`docs/PRD.md` vs `docs/prd.md`) are not handled: the corpus assumes a case-sensitive filesystem, and on one each such path still gets its own document. User ruling: "Accept all five". |
| E3 | SC1 | empty | dismissed | The only row with an empty `path` is the `tree truncated` row, which is always skipped and never has a document written (`prdy/crawl.py:74-76`). |
| E4 | SC2 | idempotency | criterion SC5 | |
| E5 | SC2 | concurrency | held-out | A crawl interrupted between two candidates leaves every index row already recorded with its document on disk, and the next crawl completes the rest. Two crawls running at once on one corpus are unsupported, with no guarantee. User ruling: "Accept all five". |
| E6 | SC3 | boundary | criterion SC3 | |
| E7 | SC3 | idempotency | criterion SC3 | |
| E8 | SC4 | adjacency | held-out | Only skip reasons starting `fetch failed` or `write failed` are retried; `over 1 MB`, `content sniff` and `tree truncated` rows keep today's behaviour. User ruling: "fetch failed and write failed". |
| E9 | SC5 | empty | held-out | A crawl whose search returns no repositories, or whose repositories have no candidates, writes nothing, reports `Saved: 0  Skipped: 0  Unchanged: 0` for candidates, and exits 0 as today. |
| E10 | SC6 | adjacency | held-out | When the fixed location for one source path is already occupied by an old-named document whose sidecar names a different source path, that old document's bytes are left unchanged and the new document is still stored separately. User ruling: "Heal on next crawl" with old-named files left in place, never deleted. |
| E11 | SC7 | empty | criterion SC7 | |
| E12 | SC8 | none | dismissed | The criterion is a set of fixed statements in one document; it handles no data shape. |

## Prohibitions

| Prohibition | Criterion | Must not | Disposition | Detail |
|-------------|-----------|----------|-------------|--------|
| N1 | SC1 | show one source file's text under another source path's row | criterion SC1 | |
| N2 | SC2 | delete or overwrite a corpus document that belongs to a different source path while repairing an old corpus | criterion SC6 | |
| N3 | SC3 | hide a retry that failed again from the crawl summary | criterion SC3 | |
| N4 | SC4 | spend the owner's GitHub rate limit re-fetching files whose result cannot change | criterion SC4 | |
| N5 | SC5 | rewrite documents or sidecars the owner already has when nothing changed | criterion SC5 | |
| N6 | SC6 | lose a file the owner already has in their corpus | criterion SC6 | |
| N7 | SC7 | write into the owner's real corpus folder, call a paid model, or use any credential other than the existing `gh` login during the live check | judgment | The reviewer confirms the recorded commands target a temporary folder, carry no `--llm` flag, and set no token variable. |
| N8 | SC8 | promise protection the code does not give (letter-case safety, parallel-crawl safety, or recovery of documents already overwritten before the fix) | judgment | The reviewer reads the changed README passages and confirms each statement matches a success criterion or a recorded ruling and none claims more. |

## Scope: in

- A corpus file-naming rule in `prdy/store.py` under which distinct source
  paths in one repository get distinct documents and sidecars.
- Crawl re-fetches a saved row whose document is missing at its fixed
  location (repair of corpora crawled before the fix).
- Crawl retries `fetch failed` and `write failed` rows whose `blob_sha` is
  unchanged.
- Tests for the above, including the held-out edges.
- README.md corrections named in criterion 8 (DOCS-AUDIT queue row 28).

## Scope: out (vetoes)

- Removing or modifying the SSSF factory, its skills, the sandbox material,
  herdr, `just/`, the `justfile`, `.env.sample`, the `.gitignore` SSSF
  entries, or `specs/61c66de7_regrade-command.md` — user: "keep herdr, keep
  the just/ folder and file.  Just could be utilized in the project/repo.
  Also keep the sandbox info in case the system uses it.  we may use it as
  well." and "if it's not critical to remove them, just keep the skills."
- Building product changes through the SSSF factory — user: "GSD Path owns
  the next milestone."
- Deleting any file from a corpus, including old-named documents left by an
  earlier version — user chose "Heal on next crawl": "Old-named files are
  left in place, never deleted."
- A separate migration command or an in-place rename of existing corpora.
- Handling source paths that differ only by letter case.
- Any guarantee for two crawls running at once on one corpus.
- A retry cap, backoff, or new index field for retry state.
- Changing the `index.jsonl` row fields, the exit codes (0 / 1 / 2), the
  rubric, the `--llm` path, or the `list`, `grade` and `regrade` behaviour
  beyond reading documents from their fixed location.
- Editing `docs/superpowers/plans/2026-09-02-prdy-v1.md`,
  `docs/superpowers/specs/2026-09-02-prdy-v1-design.md`, or any skill
  document (accepted drift, below).

## Constraints

- Python `>=3.12`, standard library plus `httpx`; no new runtime dependency.
- Follow the conventions in the codebase map: `cli.py` is the only module
  that prints; typed exceptions become exit codes only in `cli.py`;
  dependencies are injected for tests; tests are plain pytest functions with
  no network in the default run.
- The project check is `uv run pytest -q`; no lint or type-check step exists.
- `python -m prdy` does not work; use `uv run prdy`.
- Final review may run one small live crawl (criterion 7) with the owner's
  existing `gh` login into a temporary folder. No other network use, no
  `--llm` call, no SSSF or sandbox recipe.
- Integration mode: `direct`.

## Current state (brownfield only)

- **What exists**: `prdy` 0.1.0, a Python CLI of seven flat modules (786
  lines) with `crawl`, `grade`, `list` and `regrade`; one runtime dependency
  (`httpx`); the suite is 152 passed, 1 skipped at `bf8dbcb`. The corpus is a
  folder with `index.jsonl` plus per-repository folders of `.md` documents
  and `.meta.json` sidecars.
- **Must not break**: the `index.jsonl` row schema; exit codes 0 / 1 / 2;
  `list`, `grade` and `regrade` output; the rubric; everything listed under
  Scope: out.
- **Doc-vs-code rulings**: queue row 28 (README "not re-examined") →
  `fix-doc`, user: "defer to you". Queue rows 29–36 (v1 plan, v1 design spec,
  regrade spec) → `accept-drift`, user: "defer to you". Queue rows 1–27
  (SSSF, sandbox and herdr skill documents) → `accept-drift`, proposed by
  define after the user ruled to keep those skills ("if it's not critical to
  remove them, just keep the skills"); confirmed or changed at intent
  approval.
- **Ground truth**: `.project/research/evidence-codebase.md`, `.project/research/DOCS-AUDIT.md`

## Risks

- A naming rule that separates `docs/prd.md` from a file literally named
  `docs__prd.md` changes the stored name of some or all documents, so the
  first crawl after the fix may re-fetch much of an existing corpus.
- A permanently missing upstream file is re-fetched on every crawl; accepted
  by ruling (no cap).
- Criterion 7 depends on live GitHub search results and rate limits; a search that finds no candidates is handled by widening the query, bounded at five attempts (C4).

## Open questions

None.

## Corrections

- C1 2026-11-15: "GSD Path owns the next milestone. remove the sssf and its skills."
- C2 2026-11-15: "keep herdr, keep the just/ folder and file.  Just could be utilized in the project/repo.  Also keep the sandbox info in case the system uses it.  we may use it as well."
- C3 2026-11-15: "if it's not critical to remove them, just keep the skills. I thought it might help, but if it doesn't matter, leave it.  If it DOES matter, remove your recommendations."
- C4 2026-11-15: Wave 1 cycle 1 review blocked SC7 because the live search found no candidates and `regrade` had no index. Asked how to correct the criterion, the user chose: "Require a crawl that saves something (Recommended)" — "The reviewer starts from `prdy crawl \"prd\" --topic prd --limit 10` and may widen the query or limit until the first run saves at least one document; the twice-run, list and regrade checks then apply as before." The five-attempt bound and the `unverifiable` outcome were proposed by define and approved with this correction.
- C5 2026-11-15: Asked whether to fix the README `prdy grade` usage example that still shows a pre-fix corpus file name, the user chose: "Fix it now (Recommended)". SC8 now covers that example.
