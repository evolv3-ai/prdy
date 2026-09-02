# prdy

prdy crawls GitHub for product requirements documents (PRDs), saves each one
locally with a metadata sidecar, grades it against a deterministic rubric
(optionally a model grade too), records licenses, and keeps a JSONL index.

## Setup

- Python 3.12+ and [uv](https://docs.astral.sh/uv/).
- A GitHub token: `gh auth login`, or export `GITHUB_TOKEN`. Unauthenticated
  use is refused because search is limited to 10 requests a minute without one.
- Optional, for `--llm`: `OPENROUTER_API_KEY`. Put it in `.env` and run with
  `uv run --env-file .env prdy ...`.

```sh
uv sync
uv run pytest
```

## Usage

```sh
uv run prdy crawl "product requirements document" --stars ">50" --limit 30 --out ./corpus
uv run prdy crawl "prd" --topic prd --topic product-management --language Markdown
uv run --env-file .env prdy crawl "prd template" --llm --model anthropic/claude-sonnet-5
uv run prdy grade ./corpus/acme__widgets/docs__prd__login.md
uv run prdy regrade --out ./corpus
uv run prdy list --out ./corpus --min-grade B --sort stars
uv run prdy list --out ./corpus --json
```

`regrade` re-runs the rubric on every saved document and rewrites `grade_*` in the index and sidecars, leaving the `llm_*` fields alone; it exits 1 when the corpus or its index is missing.

`--limit` caps the number of repositories examined, not the number of PRDs found.

Exit codes: `0` success (even when nothing was found); `1` usage or auth error;
`2` the crawl aborted on an unrecoverable API error after partial progress. The
index keeps whatever landed.

## Corpus layout

```
corpus/
  index.jsonl                     one row per candidate, including skipped ones
  acme__widgets/
    docs__prd__login.md           the document as fetched
    docs__prd__login.meta.json    same fields as its index row
```

Row fields: `repo, path, url, html_url, blob_sha, default_branch, fetched_at,
stars, topics, repo_license, inline_license, size, title, grade_score,
grade_letter, grade_reasons, llm_score, llm_critique, llm_model, skipped`.

Re-crawling skips any candidate whose `blob_sha` is already indexed. Skipped
candidates (`tree truncated`, `over 1 MB`, `content sniff`, `fetch failed: <reason>`,
`write failed: <reason>`) keep an index row so they are not re-examined.

## Rubric

| Check | Points |
|---|---|
| Sections present (problem, goals, users, requirements, success metrics, non-goals, timeline, open questions), 8 each | 64 |
| Length band: under 200 words 0; 200–600 6; 600–4000 12; over 4000 8 | 12 |
| At least three headings across two levels | 8 |
| A list and a table, or two lists | 8 |
| A date (4) and an author/owner/status line (4) | 8 |

A ≥ 85, B ≥ 70, C ≥ 55, D ≥ 40, F below. `prdy grade <file>` prints the score
and every reason a check fell short, so the rubric can be tuned offline.

Design: `docs/superpowers/specs/2026-09-02-prdy-v1-design.md`.
