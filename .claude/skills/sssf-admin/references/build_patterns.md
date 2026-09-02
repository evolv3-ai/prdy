# Build patterns — herdr mechanics for one managed build

How to run one build through herdr panes: the topology, the verified output markers each phase
prints, the wait discipline, and how to know a detached SDLC is actually done. Everything quoted
here was read from the recipes in this repo — if a marker ever fails to appear, diff against the
recipe (`just --show sbx::lifecycle::<phase>`) before assuming the build is stuck.

herdr commands below were validated on **herdr 0.8.0**. herdr evolves fast and renames verbs
(0.7's top-level `wait output` became `pane wait-output` in 0.8) — trust `herdr --help` and
`herdr <cmd> --help` over anything written here, and read `herdr --skill` (the tool prints its
own agent instructions) when the surface has drifted.

## Topology: one workspace per build

```bash
# Capture BOTH ids — never rely on focus.
read WS ROOT < <(herdr workspace create --cwd "$PWD" --label sbx-<task> --no-focus \
  | jq -r '.result | "\(.workspace.workspace_id) \(.root_pane.pane_id)"')
CTL=$ROOT                                                          # control pane: runs the phases
LOG=$(herdr pane split $ROOT --direction down --no-focus | jq -r .result.pane.pane_id)  # tail pane
```

- The **control pane** runs the `just sbx` commands, one at a time, in order.
- The **log pane** exists only to `tail -f run.log` once the SDLC is running.
- Re-label the workspace with the resolved run id once you have it, so the human can find it:
  the label is the only thing they see in their terminal.
- Never close `$ROOT` while you still want the workspace — closing the last pane deletes it.
- Close the workspace only after the build's report is delivered (and teardown, if authorized).

## The verified marker table

Every phase prints a distinctive line on success. **Match markers that carry the run id wherever
one exists** — `wait output` also fires on matching text already in scrollback (a verified herdr
pitfall), and generic markers repeat across builds. A dedicated fresh pane per build plus
run-id-bearing markers makes stale matches impossible.

| Step | Command (in CTL pane) | Success marker | Failure marker | Timeout |
|---|---|---|---|---|
| preflight | `just sbx manage doctor` | `sbx doctor: OK` | any `fail` line, non-zero exit | 60s |
| mount (chain) | `just sbx mount <task>` — **single build only, never two concurrently** (see below) | `mounted: <run-id>` | see per-phase below | 300s |
| create | `just sbx lifecycle create <task>` | `created  <run-id>` | `create FAILED (exit` | 120s |
| fill | `just sbx lifecycle fill <run-id>` | `==> fill: app/.env written` | stderr, non-zero | 60s |
| setup | `just sbx lifecycle setup <run-id>` | `[setup] GATE PASSED — <run-id>` | `[setup] FAILED:` | 300s |
| observe | `just sbx lifecycle observe <run-id>` | `app  https://` (the URL banner) | `observe:` on stderr | 120s |
| execute | `just sbx lifecycle execute <run-id> "<prompt>" [CONFIG] [ADW]` | `pid` … `recorded; SDLC is running detached` | non-zero exit | 60s |
| harvest | `just sbx manage harvest <run-id>` | `harvest: <N> commit(s) ->` or `committed nothing` | `!! harvest:` | 120s |
| teardown | `just sbx lifecycle teardown <run-id>` | `✓ teardown complete for <run-id>` | `!! gate FAILED` = **key still live, escalate** | 180s |

**Why `mount` must never run twice at once (verified in the recipes):** after create returns,
`mount.just` resolves the run id by taking the **newest record** from `run_record.py list` — not
by parsing create's stdout. Create spends ~60–90s (VM boot, key mint, ssh wait) between writing
its record and returning, so any record another create writes in that window becomes "newest":
both mounts then drive one VM while the other sits orphaned, half-built, with a live minted key.
One build at a time is safe; anything concurrent uses the individual phases —
`lifecycle create <task>`, parse the resolved id from its `run id:  <id>` line, then
`fill` / `setup` / `observe` with that explicit id. Those phases look up state strictly by the id
argument and cannot cross-wire.

Two parse duties during mount/create:

- **The resolved run id**: create prints `run id:  <resolved>` early. If the name you passed had
  no `-<6 hex>` suffix, the resolved id gained `-<YYYYMMDD>-<hex>`. Capture it from the pane read;
  every later command, the record, the VM, and the public hostname use the resolved string.
- **The URLs**: observe ends with a boxed banner containing `app  https://<vm>.exe.xyz/` and
  `obs  https://<vm>.exe.xyz:4600/`. Both go in the report.

Wait, then verify — a fired wait proves the text appeared, not that all is well. After each wait,
`herdr pane read $CTL --source visible --lines 40` and read what actually happened.

## Watching the detached SDLC

`execute` detaches and returns immediately; the work runs in the box for 15–45 minutes. The
done-signal is the final banner the ADW writes to `run.log` — a boxed panel titled **`ADW
complete`** containing `status ✓ success` or `✗ fail`, plus phases, tokens, cost, and the
`adw_id`.

```bash
herdr pane run  $LOG "just sbx run cmd <run-id> 'tail -f run.log'"
herdr pane wait-output $LOG --match 'ADW complete' --timeout 2700000  # 45 min; ALWAYS pass --timeout (waits forever without it)
herdr pane read $LOG --source recent-unwrapped --lines 60             # the banner: status/tokens/cost/adw_id
```

- `pane wait-output` searches the pane's **existing output first** (including scrollback), then
  polls — a match already on screen fires instantly. That makes fresh panes non-negotiable:
  `run.log` is **truncated on every execute**, so the tail stream is this build's alone, but the
  pane must also be fresh for this build — never reuse a tail pane across executes.
- The `tail -f` never exits; after reading the banner, `ctrl+c` the pane
  (`herdr pane send-keys $LOG ctrl+c`) or just close it.
- Belt-and-braces done-check when the tail looks wedged or the wait timed out:
  `just sbx run cmd <run-id> 'kill -0 <pid> && echo RUNNING || echo DONE'` (pid from the run
  record: `sandbox_mount/host/run_record.py get <run-id> pid`), and the session status:
  `just sbx run cmd <run-id> 'sqlite3 adws/adw_data/sssf.db "select adw_id,status,total_tokens,round(total_cost,4) from sessions order by started_at desc limit 3"'`.
- A wait timing out is information, not failure: the box may be mid-build on a slow model. Check
  pid + sessions before declaring anything.
- Capture the **`adw_id`** from the banner — it is the handle for `just phases <adw_id>` and
  for `--adw-id` re-entry, and it is not the run id.

## Execute's full surface

```
just sbx lifecycle execute RUN_ID PROMPT [CONFIG] [ADW] [*EXTRA]
```

- `CONFIG` — a roster path (`adws/adw_sssf_config/sssf.frontier.config.yaml`). Empty = the
  default roster. This is how fan-out varies models per box: same prompt, different CONFIG per
  run. (`SSSF_CONFIG` as an env var does NOT cross `ssh vm "cmd"` — only this argument works.)
- `ADW` — any recipe name from `just adw` (`sdlc` default, `simple-sdlc`, `build-test`,
  `plan-build-test-quality`, `scout`, …). Prefer the cheap chains (`build-test`) for smoke tests
  before spending on a full SDLC.
- `*EXTRA` — verbatim ADW flags; most usefully `--adw-id <id>` to **rejoin an existing session**
  after a failure, so the agents keep their context instead of starting cold.

## Landing work the chain left uncommitted

**Harvest bundles only `commit_sha..refs/heads/sbx/<run-id>`** — the run branch fill created.
Uncommitted working-tree changes and commits on any other branch are silently dropped. Which
chains commit (verified in the ADW sources):

| Commits | Chains | Caveat |
|---|---|---|
| yes | `plan-build`, `sdlc` (plan-build-test), `plan-build-test-quality`, `simple-sdlc` | the test-gated ones leave code **uncommitted when the suite is red**; `simple-sdlc`'s plan commit always lands even when the code commit doesn't |
| never | `build-test`, `build`, `build-review`, `plan`, `document`, `prompt`, `quality`, `scout` | all work stays in the box's working tree |

So after a no-commit chain succeeds (or a test-gated chain fails but the work is worth keeping),
land it on the run branch from the host, then harvest:

```bash
just sbx run cmd <run-id> "git status --porcelain && git rev-parse --abbrev-ref HEAD"
just sbx run cmd <run-id> "git switch sbx/<run-id>"        # only if HEAD is elsewhere
just sbx run cmd <run-id> "git add -A && git commit -m 'sbx(<run-id>): <what and why>'"
just sbx manage harvest <run-id>
```

`run cmd` quoting rules (it interpolates your command verbatim into `ssh "$VM".exe.xyz
"cd app && …"`): pass the whole remote command as **one** quoted argument, use only single quotes
*inside* it (an inner double quote breaks the ssh wrapper), and skip any `cd` — `cd app` is
prepended for you. Pipes and heavy quoting can still mangle through the just→ssh double hop; for
anything non-trivial, drop to plain ssh — inspection is allowed:
`VM=$(sandbox_mount/host/run_record.py get <run-id> vm_name); ssh "$VM.exe.xyz" 'cd app && …'`.

## Delegated-agent mode

When the build needs judgment inside the box — a failing gate to diagnose, an ambiguous prompt to
interpret against the live code, steering mid-flight — hand off instead of scripting:

```bash
just sbx run agent <run-id> "If you have not already: READ and EXECUTE .claude/skills/sssf/SKILL.md. Then: <work>"
```

The session is resumable: the same command later continues the same conversation (the session id
lives in the run record). Use it to ask the box questions ("why did gate C fail?", "what did the
builder change?") — synchronous `run cmd` for reads you can name, `run agent` for reads that need
thinking. It can also launch ADWs itself (agent-mediated kickoff) when the user asked for
conversational control rather than a detached run.

For a **standing host-side operator** (the user wants an agent in their terminal they can keep
talking to about builds), launch one in a herdr pane:

```bash
herdr agent start sssf-operator --tab ${WS}:t1 --split right --cwd "$PWD" --no-focus -- \
  claude --dangerously-skip-permissions "READ and EXECUTE .claude/skills/sssf-sandbox-orchestrator/SKILL.md, then await instructions."
```

Then drive it with `herdr agent send sssf-operator "<instruction>"` +
`herdr agent wait sssf-operator --until idle --timeout <ms>`, and read its pane. An idle agent
has finished a turn, not necessarily succeeded — always read before reporting.

## Progress reporting cadence

While a build runs, do not narrate every line. Report at exactly these moments: mount complete
(run id + URLs), execute launched (pid), each ADW phase transition **if the user is actively
watching** (from the tail pane: the phase banner lines), the `ADW complete` banner, harvest
result, and — if authorized — teardown result. If the user has gone quiet, deliver one final
consolidated report instead.
