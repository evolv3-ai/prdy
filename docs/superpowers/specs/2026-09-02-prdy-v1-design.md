# prdy v1 — design

Date: 2026-09-02. Status: approved in conversation, awaiting written review.

## Purpose

prdy crawls GitHub for product requirements documents (PRDs), saves each one
locally with its metadata, grades it, records its license, and keeps an index
of everything found. v1 is deliberately small: one CLI, sequential requests, a
folder of markdown files plus one JSONL index. Additional features come later
on top of this base.

## Decisions already made

| Question | Decision |
|---|---|
| Discovery | GitHub *repository* search driven by keywords and the usual search qualifiers, then one recursive tree listing per repo, then path heuristics. Code search is out of scope for v1. |
| Output | Local corpus: one markdown file per PRD plus a `.meta.json` sidecar, and one `index.jsonl` at the corpus root. No database. |
| Grading | A deterministic rubric always; an optional model grade behind `--llm`. |
| License | Two fields: the repository's SPDX id from the API, and any inline license or copyright line in the PRD itself. |
| Stack | Python 3.12+, `uv` for running and dependencies, `pytest` for tests. |
| Auth | `gh auth token` when available, else `GITHUB_TOKEN`. Unauthenticated use is refused with a message, because search without a token is limited to 10 requests a minute. |

## CLI

```
uv run prdy crawl "<keywords>" [--topic T ...] [--stars ">50"] [--language L]
                  [--pushed ">2025-01-01"] [--org O] [--limit 30] [--out ./corpus]
                  [--llm] [--model M]
uv run prdy grade <file.md> [--llm] [--model M]
uv run prdy list [--out ./corpus] [--min-grade B] [--sort score|stars|fetched] [--json]
```

- `crawl` builds one repository-search query: the keywords verbatim, then each
  filter as its qualifier (`topic:`, `stars:`, `language:`, `pushed:`,
  `org:`). `--limit` caps the number of repositories examined, not PRDs found.
  Repeatable `--topic` adds one qualifier per value (GitHub ANDs them).
- `grade` prints the rubric result for a local file, so the rubric can be
  tuned without crawling. With `--llm` it prints the model grade too.
- `list` reads `index.jsonl` and prints a table (or JSON with `--json`).

Exit codes: 0 on success even when nothing was found; 1 on a usage or auth
error; 2 when the crawl aborted on an unrecoverable API error after partial
progress (the index keeps what landed).

## Modules

```
prdy/
  cli.py        argparse entry point; wires the others, no logic of its own
  github.py     thin REST client: search_repos, get_tree, get_blob; rate-limit aware
  discover.py   query builder from CLI flags; is_prd_path; content sniff
  grade.py      rubric -> Grade(score, letter, reasons)
  llm.py        optional model grade via OpenRouter -> LlmGrade(score, critique, model)
  store.py      corpus layout, sidecar writing, index upsert and read
tests/
  fixtures/     recorded JSON responses (search page, tree, blob) and sample PRDs
```

Each module exposes plain functions and small dataclasses; nothing holds
global state. `cli.py` is the only module that prints.

### github.py

- Base URL `https://api.github.com`, `Accept: application/vnd.github+json`,
  token from `gh auth token` (subprocess, ignored if `gh` is missing) or
  `GITHUB_TOKEN`.
- `search_repos(query, limit)` pages through `/search/repositories`
  (`per_page=100`, sorted by stars) and yields repo dicts until `limit`.
- `get_tree(owner, repo, ref)` calls `/repos/{o}/{r}/git/trees/{ref}?recursive=1`
  and returns the entries plus the `truncated` flag.
- `get_blob(owner, repo, path, ref)` fetches raw content through
  `/repos/{o}/{r}/contents/{path}?ref=` with the raw media type; returns bytes.
- Every response checks `X-RateLimit-Remaining`; at 0 the client sleeps until
  `X-RateLimit-Reset` and retries. HTTP 403 with a secondary-rate-limit body
  sleeps 60 s. Network errors retry three times with backoff. 404 and other
  403s raise `SkipRepo`.

### discover.py

- `build_query(keywords, topics, stars, language, pushed, org) -> str`.
- `is_prd_path(path) -> bool`, case-insensitive:
  - extension in `.md .mdx .markdown .rst .txt`, and
  - the exact filename `requirements.txt` is never a match, and
  - any of: filename contains `prd` as a whole word (`prd.md`, `PRD-login.md`,
    `feature_prd.md`); a directory segment is `prd` or `prds`; filename
    contains `product-requirements`, `product_requirements`, or `requirements`.
- `looks_like_prd(head: bytes) -> bool`: the first 2 KB, decoded leniently,
  contains `requirement` or `prd` case-insensitively. The file is fetched
  once in full (it is at most 1 MB); a file that fails the sniff is recorded as
  skipped and is neither graded nor written, so a repo full of
  `requirements.md` install notes costs one request each and no corpus space.
- Files over 1 MB (by tree `size`) are skipped before any fetch.

### grade.py

`grade(text) -> Grade(score: int, letter: str, reasons: list[str])`.

Points, summing to 100:

| Check | Points | How |
|---|---|---|
| Sections present, 8 × 8 | 64 | A heading (any level) or bold lead-in whose text matches one of: problem/background/context; goals/objectives; users/personas/audience; requirements/user stories/features; success metrics/KPIs; non-goals/out of scope; timeline/milestones/roadmap; open questions/risks. Synonyms live in one table in the module. |
| Length band | 12 | Under 200 words 0; 200–600 6; 600–4000 12; over 4000 8. |
| Heading structure | 8 | At least three headings with at least two levels. |
| Lists or tables | 8 | At least one bullet list and one table, or two lists. |
| Ownership signals | 8 | A date (ISO or month-year) and an author/owner/status line. |

Letter: A ≥ 85, B ≥ 70, C ≥ 55, D ≥ 40, F below. `reasons` lists every
check that scored below its maximum, in words a reader can act on
("no success-metrics section", "under 200 words").

### llm.py

`grade_with_model(text, model) -> LlmGrade(score, critique, model)`. Sends
the rubric table and the document to an OpenRouter chat completion (key from
`OPENROUTER_API_KEY`, default model set in one constant, override with
`--model`). Asks for JSON `{score, critique}`; a malformed reply is retried
once, then recorded as `null` with the error in `critique`. The rubric grade
is never replaced by the model grade; both are stored.

### store.py

Corpus layout:

```
<out>/
  index.jsonl
  <owner>__<repo>/
    <path with / replaced by __>.md
    <same name>.meta.json
```

Sidecar and index row carry the same fields:

```
repo, path, url, html_url, blob_sha, default_branch, fetched_at,
stars, topics, repo_license (SPDX id or null), inline_license (line or null),
size, title (first H1 or filename), grade_score, grade_letter, grade_reasons,
llm_score, llm_critique, llm_model, skipped (null or reason)
```

`upsert(row)` rewrites `index.jsonl` with the row replacing any existing row
with the same `(repo, path)`. On crawl, a candidate whose `blob_sha` already
matches the index is not fetched or re-graded unless `--llm` is set and
`llm_score` is null. Skipped files still get an index row with `skipped`
set, so a re-crawl does not re-examine them.

### Inline license detection

Scan the whole text for a line matching, case-insensitively, `license`,
`licence`, `copyright`, `©`, `SPDX-License-Identifier`, or `CC BY`. Record
the first matching line, trimmed to 200 characters. Absent, `null`.

## Data flow of `crawl`

1. Resolve token; refuse without one.
2. Build the query; page through repository search up to `--limit` repos.
3. Per repo: tree listing on the default branch. Truncated tree → index row
   with `skipped: "tree truncated"` for the repo (path `""`), continue.
4. Filter entries with `is_prd_path`, then size. For each survivor whose
   `blob_sha` is not already indexed: fetch, sniff head, and either skip
   (`skipped: "content sniff"`) or grade, license-scan, write the file and
   sidecar, upsert the index.
5. Print a summary: repos examined, candidates, saved, skipped, and the top
   five by score. Exit 0.

## Testing

- Unit: `build_query`, `is_prd_path` (positive and negative table),
  `looks_like_prd`, every rubric check against small fixtures, inline
  license detection, `upsert` semantics and re-crawl skipping.
- Client: `github.py` against a fake transport replaying recorded fixtures,
  including one rate-limit response to prove the sleep path.
- Integration: `crawl` end to end against the fake transport, asserting the
  corpus layout and the index rows.
- Live smoke, skipped unless `PRDY_LIVE=1`: one real search with `--limit 1`.

## Out of scope for v1

Code search, concurrency, a database, a web UI, deduplicating the same PRD
across forks, re-grading old rows when the rubric changes (a `regrade`
command is the obvious next feature), and any write to GitHub.
