# Evidence — codebase

Repo root: /home/wsladmin/dev/prdy
Scanned: 2026-11-15
Checks run: all in the supplied verify sidecar at audited HEAD `bf8dbcbd2d0c9447781f0178c51ccc00b81734c5` (branch `gsd-path-verify/inspect-codebase`, clean before and after apart from the gitignored `.venv/`).
- `env -u PRDY_LIVE uv run pytest -q` → 152 passed, 1 skipped in 0.48s (uv selected CPython 3.13.2; the skip is `tests/test_live.py`, gated on `PRDY_LIVE`)
- `uv run prdy --version` → `prdy 0.1.0`, exit 0
- `uv run prdy --help` → lists subcommands `crawl`, `grade`, `list`, `regrade`, exit 0
- `uv run prdy` (no subcommand) → argparse usage error on stderr, exit 1
- `uv run prdy grade tests/fixtures/good_prd.md` → `94 A` plus one reason line, exit 0
- `uv run prdy list --out /nonexistent-corpus` → `no PRDs in the index`, exit 0
- `uv run python -m prdy --version` → `No module named prdy.__main__`, exit 1
- `just --list` → 14 root recipes plus modules `adw` and `sbx`
- `uv run python -c "... store.document_paths / discover.is_prd_path ..."` → results quoted in the findings below
- `git log`, `git ls-files`, `git diff --stat 2e5fcdd bf8dbcb`, `git branch -a`, `git tag`, `git remote -v`
- Not run: `prdy crawl` and `--llm` paths (live network, GitHub and OpenRouter credentials), any `just` ADW or `sbx` recipe (paid model calls, VM creation), `just obs`.

## Map

- **Stack**: Python package `prdy` 0.1.0, `requires-python >=3.12`, one runtime dependency `httpx>=0.27` (locked 0.28.1), dev group `pytest>=8` (locked 9.1.1), build backend hatchling, lockfile `uv.lock` (`pyproject.toml:1-22`). Standard library only otherwise (argparse, dataclasses, json, re, subprocess). No linter, formatter, or type-checker configuration in `pyproject.toml`. No CI configuration (`.github/` absent). Alongside the product: a stamped agent "software factory" (`adws/`, Python scripts with PEP 723 inline dependencies pydantic, python-dotenv, pyyaml, rich, plus two TypeScript pi extensions), `just` recipes (`justfile`, `just/`), sandbox host/guest scripts (`sandbox_mount/`), and installed GSD Path runtime 1.7.1 (`.gsd-path/runtime.json`, `.claude/skills/`, `.opencode/skills/`).
- **Entry points**: console script `prdy = "prdy.cli:main"` (`pyproject.toml:8-9`); `prdy/cli.py:189` also supports direct execution. No `prdy/__main__.py`. Factory entry points are `adws/adw_*.py` scripts invoked through `just` recipes (`justfile:38-61`, `just/adws.just`).
- **Architecture**: Seven flat modules under `prdy/` (786 lines total). `cli.py` parses arguments and is the only module that prints; it dispatches to `cmd_crawl`, `cmd_grade`, `cmd_list`, `cmd_regrade` (`prdy/cli.py:58-65`). A crawl flows `discover.build_query` → `github.GitHubClient.search_repos` → `get_tree` → `discover.is_prd_path` filter → `get_blob` → `discover.looks_like_prd` sniff → `grade.grade` (deterministic 100-point rubric) → optional `llm.grade_with_model` (OpenRouter) → `store.write_document` and `store.upsert` (`prdy/crawl.py:55-141`). The corpus is a directory: `index.jsonl` plus, per repository, a `owner__repo/` folder of `<flattened path>.md` documents with `.meta.json` sidecars (`prdy/store.py:44-115`). `grade.py` and `discover.py` are pure functions; `github.py` owns HTTP retry and rate-limit handling.
- **Conventions**: `from __future__ import annotations` and a one-line module docstring in every module; full type hints; dataclasses for records (`Row`, `Grade`, `LlmGrade`, `CrawlSummary`); private module constants prefixed `_`. Errors are typed exceptions (`SkipRepo`, `GitHubError`, `AuthError`, `LlmError`) converted to exit codes only in `cli.py`: 0 success, 1 usage/auth/configuration, 2 crawl aborted mid-run (`prdy/cli.py:60-100`). Dependencies are injected for testing (`http`, `sleep`, `clock`, `run`, `now`, `llm_grader`). Tests are plain pytest functions, one file per module, using `httpx.MockTransport`, `monkeypatch`, `tmp_path`, `capsys`, and files in `tests/fixtures/`; no network in the default run. Commit subjects on the v1 work use `feat:` / `fix:` / `docs:` / `refactor:` prefixes; the five most recent commits use unprefixed sentence subjects.
- **Maturity**: The four CLI subcommands run and the suite passes (152 passed, 1 skipped). Test function counts per file: github 20, cli 18, grade 17, discover 12, store 11, crawl 10, llm 9, regrade 5, live 1. The live GitHub path and the OpenRouter path are exercised only through mocks in the default run. Package version is 0.1.0; no tags exist; nothing is published. The factory layer (`adws/`, `just/`, `sandbox_mount/`) is tracked, has no tests in this repository, and was not executed during this inspection.
- **Recent activity**: 27 commits. One on 2026-07-30 (`first commit`), 25 on 2026-09-02 (design spec, plan, the v1 build as 17 `feat`/`fix`/`refactor` commits, SSSF sandbox install, the factory-built `regrade` command and its merge), one on 2026-11-15 (`bf8dbcb`, GSD Path install). The last commit touching `prdy/` or `tests/` is `bf5edfc` (2026-09-02, `regrade`). `bf8dbcb` adds 1108 files / 794,682 lines, all of it pipeline tooling (`.claude/skills/`, `.opencode/skills/`, `.gsd-path/`, `AGENTS.md`, `WORKFLOW.md`, `.claude/CLAUDE.md`, `.claude/settings.json`); no product file changed.

## Finding: Product code is under 6% of tracked files

- **Claim**: Of 1364 tracked files, 712 are under `.claude/` and 550 under `.opencode/`; the product is 8 files in `prdy/` (786 lines) and 17 in `tests/` (about 1,480 lines including fixtures).
- **Source**: `git ls-files | awk -F/ '{print $1}' | sort | uniq -c`; `wc -l` over `prdy/` and `tests/`
- **Confidence**: high
- **Why it matters here**: Repository-wide searches, line counts, and "recent activity" are dominated by installed tooling. Scope and file lists for a milestone need explicit paths, or they will match generated skill copies.

## Finding: Root AGENTS.md, WORKFLOW.md and .claude/CLAUDE.md describe the pipeline, not prdy

- **Claim**: The three root-level agent instruction files were added by `bf8dbcb` and contain GSD Path operating rules only; none states a prdy convention, command, or constraint. The only product-specific prose is `README.md`, `docs/superpowers/` and `specs/61c66de7_regrade-command.md`.
- **Source**: `git diff --stat 2e5fcdd bf8dbcb -- . ':!.claude/skills' ':!.opencode'`; `.claude/CLAUDE.md:1-2`
- **Confidence**: high
- **Why it matters here**: Product conventions binding on a planner exist only in the code and tests summarised in the Map, not in any agent-facing rules file.

## Finding: Two separate agent build systems are installed in one repository

- **Claim**: The repository carries the SSSF factory (`adws/`, `just/`, `sandbox_mount/`, skills `sssf`, `sssf-admin`, `sssf-sandbox`, `sssf-sandbox-orchestrator`, `sandbox-exe-dev`, `herdr`) and GSD Path (15 `gsd-path*` skills plus `path`, mirrored under `.opencode/skills/`). The last product change (`regrade`, `bf5edfc`, author `exe.dev user`) was produced by the factory and merged in `2e5fcdd`; GSD Path was installed afterwards and has built nothing yet.
- **Source**: `git ls-files .claude/skills | awk -F/ '{print $3}' | sort | uniq -c`; `git log --format='%h %ad %an %s'`
- **Confidence**: high
- **Why it matters here**: Both systems can commit to this repository and each has its own planning artifacts (`specs/` for the factory planner, `.project/` for GSD Path). Which one owns upcoming work is not recorded in the code.

## Finding: A PreToolUse hook runs the GSD Path guard on every tool call

- **Claim**: `.claude/settings.json` registers `python3 "$CLAUDE_PROJECT_DIR/.gsd-path/guard_hook.py"` with matcher `.*` for every Claude Code tool call in this project.
- **Source**: `.claude/settings.json:1-15`
- **Confidence**: high
- **Why it matters here**: Tool calls by any agent working in this checkout, including factory or ad-hoc sessions, pass through the guard; a blocked write may come from the hook rather than from the product.

## Finding: The factory's only quality gate is the pytest suite

- **Claim**: `adws/adw_modules/quality.py` wires a single block, `uv run pytest -q`; its comment records that prdy has no lint, typecheck, or build step. `pyproject.toml` configures none either.
- **Source**: `adws/adw_modules/quality.py:144`, `adws/adw_modules/quality.py:193-195`; `pyproject.toml:11-22`
- **Confidence**: high
- **Why it matters here**: `uv run pytest -q` is the one mechanical project check that exists. A plan that names a lint or type-check Verify command would be naming something not installed.

## Finding: `python -m prdy` does not work

- **Claim**: There is no `prdy/__main__.py`; `uv run python -m prdy --version` exits 1 with `No module named prdy.__main__`. The installed `prdy` script and `python prdy/cli.py` are the working invocations.
- **Source**: `uv run python -m prdy --version` (exit 1); `git ls-files prdy`
- **Confidence**: high
- **Why it matters here**: A Verify command or doc written with `python -m prdy` fails regardless of feature correctness.

## Finding: Usage errors exit 1, not argparse's default 2; exit 2 means a crawl aborted

- **Claim**: `main()` catches argparse's `SystemExit` and returns 1 for any non-zero code; `cmd_crawl` returns 2 only when `CrawlSummary.error` is set, after printing the partial summary.
- **Source**: `prdy/cli.py:60-63`, `prdy/cli.py:96-100`; `uv run prdy` → exit 1
- **Confidence**: high
- **Why it matters here**: The exit-code contract is deliberate and tested; a new subcommand that lets argparse exit 2 would collide with the "aborted crawl" meaning.

## Finding: Different source paths can map to the same corpus file

- **Claim**: `store.document_paths` flattens `/` to `__` and replaces the extension with `.md`, so `docs/prd.md`, `docs/prd.txt` and `docs__prd.md` in one repository all resolve to `a__b/docs__prd.md`. Index rows stay distinct because they key on `(repo, path)`, while the document and sidecar are overwritten by whichever was written last.
- **Source**: `prdy/store.py:89-94`; `uv run python -c "... document_paths ..."` printed `c/a__b/docs__prd.md` three times
- **Confidence**: high (mapping verified; no real-corpus occurrence observed)
- **Why it matters here**: `regrade` and any future feature that reads documents back by index row can read a different file's text than the row describes.

## Finding: `regrade` rewrites the whole index once per row and never touches model grades

- **Claim**: `cmd_regrade` calls `store.upsert` for each examined row, and `upsert` re-reads and rewrites `index.jsonl` in full each time. It updates `grade_score`, `grade_letter`, `grade_reasons` only; `llm_*` fields are carried through unchanged. Rows with `skipped` set or with a missing `.md` are passed over without a message.
- **Source**: `prdy/cli.py:162-186`; `prdy/store.py:67-82`
- **Confidence**: high
- **Why it matters here**: Index writes are quadratic in corpus size for `regrade` and for `crawl` (`prdy/crawl.py:46-47`); corpus-scale features inherit that cost.

## Finding: Skipped rows are recorded in the index and some are never retried

- **Claim**: Candidates rejected for size, content sniff, fetch failure, or write failure are stored as index rows with a `skipped` reason and their `blob_sha`. On a later crawl an unchanged `blob_sha` counts as `unchanged` and is not re-fetched, including `fetch failed` rows. A truncated repository tree is stored as a row with `path=""`. `list` hides all skipped rows.
- **Source**: `prdy/crawl.py:74-76`, `prdy/crawl.py:86-95`, `prdy/crawl.py:106-120`; `prdy/store.py:122-123`
- **Confidence**: high
- **Why it matters here**: `index.jsonl` line count is not the number of saved PRDs, and a transient fetch failure is permanent until the upstream blob changes.

## Finding: A failed model grade is retried on every later `--llm` crawl

- **Claim**: When the model call fails twice, `grade_with_model` returns `score=None` with the error text as critique rather than raising. `run_crawl` treats an existing row with `llm_score is None` as wanting a model grade, so it re-fetches the blob and calls the model again on each `--llm` crawl.
- **Source**: `prdy/llm.py:64-78`; `prdy/crawl.py:86-95`
- **Confidence**: high
- **Why it matters here**: Model failures are data in the corpus, not errors, and crawl cost with `--llm` depends on prior failures.

## Finding: The default OpenRouter model id is unconfirmed in the code itself

- **Claim**: `DEFAULT_MODEL = "anthropic/claude-sonnet-5"` carries the comment "Verify this id exists at https://openrouter.ai/models before the first live run". No test or recorded run in the repository shows a live OpenRouter call.
- **Source**: `prdy/llm.py:13-14`; `tests/test_llm.py:14` (MockTransport only)
- **Confidence**: high for the code; validity of the id is unverifiable (no live call made)
- **Why it matters here**: The `--llm` path may never have been exercised against the real service.

## Finding: The PRD path heuristic accepts dependency-style filenames

- **Claim**: `is_prd_path` excludes exactly `requirements.txt` but returns True for `requirements-dev.txt` and `docs/requirements.md`, because any stem containing `requirements` matches. Such files become candidates and are then subject to the 2 KB content sniff for `requirement` or `prd`.
- **Source**: `prdy/discover.py:35-48`, `prdy/discover.py:56-59`; `uv run python -c "... is_prd_path ..."` printed `True True True True`
- **Confidence**: high
- **Why it matters here**: Candidate counts and stored `content sniff` skip rows include non-PRD files; changes to discovery need this baseline.

## Finding: Token resolution shells out to `gh` before reading the environment

- **Claim**: `resolve_token` runs `gh auth token` first (10 s timeout) and falls back to `GITHUB_TOKEN` only when that fails or prints nothing.
- **Source**: `prdy/github.py:30-39`
- **Confidence**: high
- **Why it matters here**: On a machine with `gh` logged in, setting `GITHUB_TOKEN` does not change which identity a crawl uses.

## Finding: `uv` runs the project on CPython 3.13, the system interpreter is 3.12

- **Claim**: With no `.python-version` file, `uv run` created the sidecar venv with CPython 3.13.2 while `/usr/bin/python3` is 3.12.3; `requires-python` is `>=3.12`.
- **Source**: `uv run pytest -q` output (`Using CPython 3.13.2`); `python3 --version`; `pyproject.toml:5`
- **Confidence**: high
- **Why it matters here**: The passing result above is evidence for 3.13 only; 3.12 was not exercised.

## Finding: The factory roster routes every agent through OpenRouter while `.env.sample` names three providers

- **Claim**: `sssf.config.yaml` sets every model as `openrouter/...` (default `google/gemini-3.6-flash`, planner `moonshotai/kimi-k3`, reviewer `openai/gpt-5.6-terra`, documenter `openai/gpt-5.6-luna`). `.env.sample` describes a starter roster needing `OPENROUTER_API_KEY`, `FIREWORKS_API_KEY` and `OPENAI_API_KEY`. `just/adws.just:15` says the root justfile uses interactive zsh, and the root `justfile` contains no `set shell`.
- **Source**: `adws/adw_sssf_config/sssf.config.yaml:1-5`, `:41`, `:107`, `:125`; `.env.sample:8-11`; `grep -n "set shell" -r justfile just`
- **Confidence**: high
- **Why it matters here**: Comments in the stamped factory files do not all describe this repository's configuration; treat them as template text.

## Finding: Factory agents are barred from editing the factory, and the planner writes to `specs/`

- **Claim**: `defaults.protected_files` lists `adws/adw_modules/`, `adws/adw_sssf_config/` and `adws/adw_*.py`; the planner's only repo write target is `specs/`, the documenter's are `app_docs/`, `docs/` and Markdown files, and the builder is unrestricted apart from protected files.
- **Source**: `adws/adw_sssf_config/sssf.config.yaml:20-32`, `:50-51`, `:70-72`, `:131-135`
- **Confidence**: high (configuration read; enforcement in `adws/adw_modules/permissions.py` not executed)
- **Why it matters here**: `specs/61c66de7_regrade-command.md` is a factory plan artifact, and `app_docs/` does not exist in the tree.

## Apparent intent

- Inference: prdy is a personal or small-team tool for assembling a graded local corpus of public PRDs, with the deterministic rubric as the primary score and a model grade as an optional second opinion — based on `pyproject.toml:4`, the `prdy/llm.py:1` docstring "Never replaces the rubric grade", and the `Row` fields for licence and provenance (`prdy/store.py:14-34`).
- Inference: the repository doubles as a proving ground for agent-driven delivery — based on v1 being built in one day from a written plan, `regrade` being built by the SSSF factory in a sandbox VM, and GSD Path being installed next with no product change since 2026-09-02.
- Inference: the next product work is expected to be additional CLI subcommands or corpus features layered on `store` and `grade`, following the `regrade` pattern — based on `regrade` reusing `read_index`, `document_paths`, `write_meta` and `upsert` without touching the crawl path.

## Open questions for define

- Which build system owns the next milestone's product changes: GSD Path, the SSSF factory, or both with a stated boundary?
- Is the SSSF layer (`adws/`, `just/`, `sandbox_mount/`, `.env.sample`, the `sssf*` skills) in scope to change, or a fixed tool that must not be touched?
- Are the corpus layout and `index.jsonl` row schema a compatibility contract for existing corpora, or free to change?
- Is the exit-code contract (0 / 1 / 2) fixed for new subcommands?
- Has `--llm` ever run against OpenRouter, and is `anthropic/claude-sonnet-5` the intended default model?
- Are the corpus filename collisions and the never-retried `fetch failed` rows known and accepted, or defects to fix?
- Which Python version is the support target: 3.12 as declared, or 3.13 as `uv` currently selects?
- Should a lint or type-check step exist, or is `uv run pytest -q` the complete project check?
- Is a live crawl (`PRDY_LIVE=1`, real GitHub token) permitted as verification evidence during the pipeline?

## Blocked areas

- Live `prdy crawl` and both `--llm` paths — require network access and GitHub / OpenRouter credentials; not run.
- SSSF factory workflows (`adws/adw_*.py`, `just adw ...`) — invoke paid model calls and can commit; read statically only, and `adws/adw_modules/` was sampled (`gates.py`, `quality.py`), not read in full.
- Sandbox lifecycle (`just sbx ...`, `sandbox_mount/`) — creates billable exe.dev VMs and API keys; recipe names and file list inspected only.
- `.claude/skills/` and `.opencode/skills/` contents — excluded by the brief except for directory names and file counts.
- Python 3.12 behaviour — the sidecar run used CPython 3.13.2; 3.12 not exercised.
