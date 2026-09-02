# Plan: `prdy regrade` — re-run the rubric over the whole corpus

## Context

The task prompt has two blank slots where the command name was lost during
templating ("Add a ___ command to prdy", "CLI: ___, exit 0"). The required
test file is `tests/test_regrade.py`, so the command is **`regrade`**:
`prdy regrade --out <corpus>`.

`regrade` re-runs the deterministic rubric (`prdy/grade.py::grade`) on every
document already in the corpus and rewrites the grade fields, without touching
the LLM fields. It exists so a corpus graded with an older rubric can be
re-scored offline after the rubric is tuned.

Existing architecture (must be preserved):

- `prdy/cli.py` — argparse + the only module that prints. Commands wired via
  the `handlers` dict in `main()`.
- `prdy/store.py` — all corpus I/O: `read_index`, `upsert`,
  `document_paths(out, repo, path)` -> `(md_path, meta_path)`, `write_document`.
  A `Row` carries `grade_score/grade_letter/grade_reasons` AND
  `llm_score/llm_critique/llm_model` AND `skipped`.
- `prdy/grade.py` — `grade(text) -> Grade(score, letter, reasons)`; pure.
- `prdy/crawl.py` — shows the pattern: `row.grade_score, row.grade_letter,
  row.grade_reasons = result.score, result.letter, result.reasons`, then
  `store.write_document(out, row, text)` + `store.upsert(out, row)`.

## Behaviour spec

CLI: `prdy regrade [--out <dir>]` (default `./corpus`, matching `crawl`/`list`).

1. If `<out>` does not exist as a directory **or** `<out>/index.jsonl` does
   not exist, print an error to stderr and exit **1**.
2. Read the index via `store.read_index(Path(args.out))`.
3. For each row with `skipped is None`:
   - Locate the saved markdown with `store.document_paths(out, row.repo,
     row.path)` (first element of the tuple). If the `.md` file is missing on
     disk, leave the row untouched and do not count it (edge case not in the
     prompt; silent skip is the least surprising choice).
   - `text = md.read_text(encoding="utf-8", errors="replace")` (same call the
     `grade` command uses in cli.py).
   - `result = grade(text)`; compare `result.score` to `row.grade_score`
     (or letter/reasons — score comparison suffices) to count changes.
   - Set `row.grade_score`, `row.grade_letter`, `row.grade_reasons` from the
     result. **Do not touch** `row.llm_score`, `row.llm_critique`,
     `row.llm_model`.
   - Persist to BOTH stores: rewrite the `.meta.json` sidecar and
     `store.upsert(out, row)`.
4. Rows with `skipped` set are ignored entirely.
5. Print exactly one summary line to stdout, e.g.
   `Regraded: 12 rows examined, 3 scores changed`, and exit **0** (even if
   nothing changed and even if the index was empty).

## Files to change

### 1. `prdy/store.py` — add `write_meta`

`write_document` currently writes the `.md` and the `.meta.json` sidecar in
one call; regrade must update the sidecar without rewriting the document.

- Extract the sidecar-writing line from `write_document` into a new helper:

  ```python
  def write_meta(out: Path, row: Row) -> Path:
      """Rewrite only the .meta.json sidecar for a row."""
      _, meta = document_paths(out, row.repo, row.path)
      meta.parent.mkdir(parents=True, exist_ok=True)
      meta.write_text(json.dumps(row.to_dict(), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
      return meta
  ```

- Make `write_document` call `write_meta` for its sidecar write (keeps the
  existing guard that refuses paths outside the repo folder, and keeps one
  sidecar format).

### 2. `prdy/cli.py` — wire the command

- In `build_parser()`, add (after the `list` subparser):

  ```python
  regrade = sub.add_parser("regrade", help="re-run the rubric grade on every document in the corpus")
  regrade.add_argument("--out", default="./corpus", help="corpus directory")
  ```

- Add `"regrade": cmd_regrade` to the `handlers` dict in `main()`.
- Add `cmd_regrade` (import `store` pieces it needs — `read_index`,
  `document_paths`, `write_meta`, `upsert` are already importable; `grade` is
  already imported):

  ```python
  def cmd_regrade(args: argparse.Namespace) -> int:
      out = Path(args.out)
      if not out.is_dir() or not index_path(out).exists():
          print(f"no corpus index at {index_path(out)}", file=sys.stderr)
          return 1
      examined = changed = 0
      for row in read_index(out):
          if row.skipped is not None:
              continue
          md, _ = document_paths(out, row.repo, row.path)
          if not md.is_file():
              continue
          examined += 1
          result = grade(md.read_text(encoding="utf-8", errors="replace"))
          if result.score != row.grade_score:
              changed += 1
          row.grade_score, row.grade_letter, row.grade_reasons = (
              result.score, result.letter, result.reasons,
          )
          write_meta(out, row)
          upsert(out, row)
      print(f"Regraded: {examined} rows examined, {changed} scores changed")
      return 0
  ```

  (`index_path` needs adding to the `from prdy.store import ...` list.)

  Note: `upsert` rewrites the whole index per row, same as crawl does per
  candidate — acceptable for this offline maintenance command.

### 3. `tests/test_regrade.py` — new file

Use `tmp_path`, `capsys`, the `fixtures` fixture from `tests/conftest.py`
(FIXTURES dir with `good_prd.md` / `weak_prd.md`), and
`store.write_document` + `store.upsert` to build corpora — the same
construction style as `tests/test_store.py` and the `seed()` helper in
`tests/test_cli.py`. Call the CLI via `from prdy.cli import main`.

Helper shape:

```python
def seed_doc(out, repo, path, md_text, **row_kwargs):
    text = (FIXTURES_DIR / md_text).read_text(...)  # or reuse `fixtures` fixture
    row = Row(repo=repo, path=path, ...)
    write_document(out, row, text)
    upsert(out, row)
    return row
```

Tests:

1. **`test_regrade_updates_scores_when_rubric_differs`** — seed a doc from
   `good_prd.md` with deliberately wrong grade fields
   (`grade_score=1, grade_letter="F", grade_reasons=["stale"]`), plus one
   `skipped="content sniff"` row (no document). Run
   `main(["regrade", "--out", str(tmp_path)])` → `0`. Assert via
   `read_index(tmp_path)`: the row's `grade_score/grade_letter/grade_reasons`
   now equal `grade(fixtures/"good_prd.md" text)`; the skipped row is
   unchanged. Assert the summary line mentions examined/changed counts.
2. **`test_regrade_updates_meta_sidecar`** — same seed; after regrade,
   `json.loads((tmp_path/"acme__widgets"/"docs__prd.meta.json").read_text())`
   has the new `grade_score`, i.e. sidecar matches the index row
   (`sidecar == row.to_dict()`).
3. **`test_regrade_preserves_llm_fields`** — seed with
   `llm_score=88, llm_critique="solid", llm_model="m/x"` and wrong rubric
   fields; after regrade the three llm fields are byte-identical in both the
   index row and the sidecar, while grade fields changed.
4. **`test_regrade_unchanged_when_scores_match`** (cheap, locks the counter)
   — seed with grade fields set from an actual `grade(text)` call; summary
   says `0 scores changed`, exit 0.
5. **`test_regrade_missing_corpus_exits_1`** — `main(["regrade", "--out",
   str(tmp_path / "nope")])` → `1`, error mentions the path on stderr.
6. **`test_regrade_missing_index_exits_1`** — `tmp_path` exists but has no
   `index.jsonl` → `1`.
7. **`test_regrade_parses`** (optional) — `build_parser().parse_args(
   ["regrade", "--out", "c"])` → command `regrade`, out `c`; default
   `./corpus`.

### 4. `README.md` — usage section

Add one line to the Usage code block (after the `grade` line):

```sh
uv run prdy regrade --out ./corpus
```

and, directly under the block, one sentence: `regrade` re-runs the rubric on
every saved document and rewrites `grade_*` in the index and sidecars, leaving
the `llm_*` fields alone; it exits 1 when the corpus or its index is missing.

## Verification

```sh
uv run pytest            # full suite must stay green (was: 147 passed, 1 skipped)
uv run prdy regrade --out ./corpus   # smoke if a local corpus exists
```

## Out of scope

- No re-fetch from GitHub; only the saved markdown on disk is graded.
- No `--llm` flag on regrade; `llm_*` fields are never modified.
- No changes to `grade.py` itself.
