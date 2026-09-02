# Fleet operations — many builds, shared state, and money

Everything beyond one build: fan-out, reconciling what the records claim against what actually
exists, spend accounting, resuming builds you did not start, and picking winners.

## The four sources of truth

They disagree in informative ways. Reconcile them in this order:

| Source | Command | Authoritative for |
|---|---|---|
| Run records | `just sbx manage list` | what this repo *believes*: state, VM name, created. **Its SPEND column is `-` for every open run** — spend is only written at teardown |
| exe.dev | `ssh exe.dev ls --json` | which VMs are *actually* alive, their tags and URLs |
| OpenRouter keys (live spend) | `curl -sS --max-time 30 "https://openrouter.ai/api/v1/keys" -H "Authorization: Bearer $OPENROUTER_PROVISIONING_KEY"` | **current per-key `usage` dollars, live, for every key including open runs.** Read-only GET (the same call reap/teardown make); returns names, hashes, usage, limits — never raw key material |
| OpenRouter keys (orphans) | `just sbx manage reap` (dry run) | `sbx-` keys whose VM/record is gone. It *skips* keys with a live VM, so it is orphan detection, **not** a live-spend read |
| Trace db | `just sessions` (host) / in-box via `run cmd` | the ADW runs *inside* a box — many per sandbox |

Match a key to its sandbox by stripping the `sbx-` prefix: the remainder is the run id, which is
also the VM name (the record's `vm_name` wins if it differs). For any money question, the key
list's `usage` field is the live answer; `manage list` only knows what teardown recorded. Never
gate anything on `GET /api/v1/key` (singular) — it still returns 200 for a deleted key; the
`/keys` LIST is authoritative.

Vocabulary guard: **a sandbox hosts many ADW runs.** `manage list` counts sandboxes (`run_id`);
`obs sessions` counts factory runs (`adw_id`). Never conflate the two handles in a report.

## Reconciliation: the orphan classes

Walk the diff between sources and classify. Each class has one right move:

| Finding | Meaning | Move |
|---|---|---|
| VM alive, no run record | created outside this flow (different tag, another repo/clone) | report it with its `created_at` and tag, **and check the key list for a matching `sbx-<vm-name>` key** — a record-less VM with a live key escapes *both* safety nets (teardown requires a record, reap skips live VMs) and can spend silently for weeks. Report the key's live `usage`; **touch nothing** without the user's word |
| Record `open`, VM gone | crashed mid-build or VM removed out-of-band | the key may still be live — check `reap` dry-run; recommend teardown (it is idempotent and each step guards on what exists) |
| Record `closed`, key still listed | teardown's revoke failed silently at some point | incident: report the hash and the manual revoke line; `reap --yes` only on the user's word |
| Live `sbx-` key, no record at all | the record was lost — the one unrecoverable state | `reap` dry-run shows it; recommend `reap --yes`, on the user's word |
| Record `open`, VM alive, no pid | mounted but never executed | a warm box ready for work — offer it before mounting a new one |

`reap` is dry-run by default and filters on the `sbx-` prefix at selection *and* deletion —
personal keys carry no prefix and are never touched. Run the dry run at the start of every
session; act with `--yes` only when the user says so.

## Fan-out: best-of-N

N is a loop over the same phases — one prompt, N rosters, N boxes, each in its own herdr
workspace. The rosters live in `adws/adw_sssf_config/`: default (cheap), `frontier`,
`deepestseek`, `open-weights`, `top-speed`.

**Never use `just sbx mount` for fan-out** — mount resolves the run id from the newest record on
disk, and concurrent creates cross-wire it (one VM driven twice, another orphaned with a live
key). Use the individual phases with explicitly parsed ids:

```bash
for CFG in sssf.config.yaml sssf.frontier.config.yaml sssf.top-speed.config.yaml; do
  # 1. create — parse the resolved id from the 'run id:  <id>' line of its stdout
  # 2. fill/setup/observe <id> — these resolve strictly by the id argument, race-free
  # 3. just sbx lifecycle execute <id> "<same prompt>" adws/adw_sssf_config/$CFG
done
```

- Creates run **sequentially** (each is seconds of work; parse each resolved id before the next);
  fills/setups may overlap once ids are in hand; the executes run **in parallel** — that is the
  point.
- Cap keys to the arm's real budget: `create <task> --limit 10` for cheap-roster arms — the
  default $50 cap × N arms is pointless exposure.
- One wait per tail pane, as parallel shell jobs, or check each in turn on a timer. N banners, N
  harvests, one comparison.
- Name workspaces by roster (`sbx-badge-frontier`), so the human can tell the arms apart.
- Budget note: N boxes = N × (SDLC cost + VM time). Say the expected ceiling in the brief echo
  before mounting (`N × ~$1` is the observed order of magnitude for a small SDLC on the cheap
  roster; frontier rosters cost more).

### Comparing the arms

Harvest every arm first — commits home before opinions. Then compare on the host, where all the
refs live:

```bash
git log --oneline main..refs/sandbox/<run-id>          # what each arm did
git diff --stat main..refs/sandbox/<run-id>            # how big
git diff refs/sandbox/<a>..refs/sandbox/<b> -- <path>  # arms against each other
```

Judge on: did the suite pass (the banner's phases count), diff size versus the ask (smallest
correct diff wins), cost, and anything the reviewer phase flagged (in-box:
`just phases <adw_id>`). Recommend a winner with a one-line reason per losing arm. **Harvest
never merges** — the refs are parked for the human; offer the merge command, don't run it.

## Spend accounting

Four numbers, and they answer different questions:

1. **The banner's `cost`** — what pi metered for one ADW run. Per-run, comparable across arms.
2. **Live key `usage`** — current dollars on the key *right now*, from the `/api/v1/keys` GET
   (sources table above). The only spend number that exists for an **open** run; also includes
   gate pings, which the banner does not.
3. **`manage list`'s `SPEND`** — what the key had cost when teardown read it. Final and durable,
   but `-` until teardown runs.
4. **The `--limit`** (default $50) — the blast radius, not a bill.

Report 1 always (it is in the banner); report 2 for anything still open when money is the
question; report 3 when it exists; mention 4 only when changing it (`--limit 10` for a cheap arm,
`--limit 200` for a big one).

## Resuming a build from an earlier session

The user says "check on the build" and you have no context. Rebuild it from disk — nothing about
a build lives only in a conversation:

1. `just sbx manage list` — find the run id, its state, whether the VM is alive.
2. `sandbox_mount/host/run_record.py get <run-id>` — the full record: pid, session_id, ports,
   commit_sha.
3. Is the SDLC still running? `just sbx run cmd <run-id> 'kill -0 <pid> && echo RUNNING || echo DONE'`.
4. What happened inside? `just sbx run cmd <run-id> 'tail -40 run.log'` — the banner is at the
   end if it finished; `just sbx run cmd <run-id> 'sqlite3 adws/adw_data/sssf.db "select adw_id,status,total_tokens from sessions order by started_at desc limit 5"'` for the run list.
5. Herdr panes from that session may still exist: `herdr workspace list` / `herdr agent list` —
   reattach to them rather than duplicating watchers.
6. Not yet harvested? Harvest now, then report as usual.

The resumable in-box agent also survives sessions: `just sbx run agent <run-id> "<question>"`
continues the same conversation (session id is in the record).
