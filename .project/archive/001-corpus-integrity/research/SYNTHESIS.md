# Synthesis

Quick lane: research and decide were skipped (INTENT.md `Lane: quick`); every choice below is closed by INTENT.md or the codebase map.

## Settled

- Stack — Python `>=3.12`, standard library plus `httpx`, no new runtime dependency (INTENT.md Constraints; evidence-codebase.md § Map, Stack)
- Module boundaries — naming lives in `prdy/store.py`, the crawl loop in `prdy/crawl.py`, and only `prdy/cli.py` prints (INTENT.md Constraints; evidence-codebase.md § Map, Architecture and Conventions)
- Index schema — `index.jsonl` row fields are unchanged; no new field for retry state (INTENT.md Scope: out)
- Old corpora — repaired by the next crawl; old-named files are left in place and never deleted; no migration command (INTENT.md SC2, SC6, Scope: out)
- Retry scope — only skip reasons starting `fetch failed` or `write failed` are retried, on every crawl, with no cap or backoff (INTENT.md SC3, SC4, E8)
- Letter case — paths differing only by case are not handled; the corpus assumes a case-sensitive filesystem (INTENT.md E2, Scope: out)
- Parallel crawls — unsupported, no guarantee (INTENT.md E5, Scope: out)
- Exit codes — 0 / 1 / 2 unchanged (INTENT.md Scope: out; evidence-codebase.md § Finding: Usage errors exit 1)
- Project check — `uv run pytest -q` is the only mechanical check; no lint or type-check step exists (evidence-codebase.md § Finding: The factory's only quality gate is the pytest suite)
- Invocation — `uv run prdy`; `python -m prdy` does not work (evidence-codebase.md § Finding: `python -m prdy` does not work)
- Tests — plain pytest functions, `httpx.MockTransport`, `tmp_path`, no network in the default run (evidence-codebase.md § Map, Conventions)
- Live evidence — one small live crawl at final review only, into a temporary folder, with the owner's `gh` login and no `--llm` (INTENT.md Constraints, SC7, N7)
- Tooling ownership — GSD Path builds this milestone; the SSSF factory, sandbox, herdr and `just` material is not touched (INTENT.md Scope: out, C1–C3)
- Docs — README.md row 28 is fixed; the v1 plan, v1 design spec, regrade spec and skill documents are accepted drift (INTENT.md Current state; DOCS-AUDIT.md § User rulings)

## For the planner

- **Wave-1 blockers**: the file-naming rule must separate `docs/prd.md`, `docs/prd.txt` and `docs__prd.md` without overwriting an old-named document that belongs to another source path (INTENT.md SC1, SC6, E10).
- **Walking skeleton**: a mocked crawl of one repository with colliding paths that ends with one document and sidecar per path, then a second crawl that reports everything unchanged.
- **Pitfalls → tasks**: `regrade` and `grade` read documents through `store.document_paths`, so the naming task must keep them reading the fixed location (evidence-codebase.md § Finding: Different source paths can map to the same corpus file); existing tests assert the old names and must be updated with the rule, not deleted.

## User rulings

- Removal of SSSF → dropped; keep all of it untouched (INTENT.md C1–C3)
- Old corpora → "Heal on next crawl"
- Retry scope → "fetch failed and write failed"
- Live check → "Allow a small live crawl"
- Remaining edge rulings → "Accept all five"; intent approved 2026-11-15 ("approve intent")

## Still unknown

- None.
