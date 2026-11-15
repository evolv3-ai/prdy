# Docs Audit

<!-- Written by the docs auditor (/gsd-path-inspect, logical task inspect_docs).
     Every verdict carries evidence; a verdict without evidence is a defect. -->

Repo root: /home/wsladmin/dev/prdy
Audited: 2026-11-15
Audited HEAD: bf8dbcbd2d0c9447781f0178c51ccc00b81734c5
Alignment mode: no

## Summary

| Verdict | Count |
|---------|-------|
| verified | 130 |
| stale | 17 |
| aspirational | 10 |
| unverifiable | 9 |
| descriptive docs (no testable claims) | 11 |

Worst drift: The sandbox and factory skill docs tell operators to pass `adws/adw_sssf_config/sssf.frontier.config.yaml` (and three more rosters) and to run `just rosters` and `just kill`, none of which exist in this repo, and `references/models.md` describes a default roster that does not match `sssf.config.yaml`.

Method notes. Project commands (`uv sync`, `uv run pytest`, `uv run prdy ...`, `just --list`, `uv run exedev ... --help`) ran only in the verify sidecar at the audited HEAD. Commands that spend money or touch external state (GitHub crawl, OpenRouter, exe.dev, `just demo`, `just sbx ...`) were not run; their claims rest on static evidence or are `unverifiable`. Line numbers for `prdy/*.py` are per file.

Scope. AGENTS.md, WORKFLOW.md and .claude/CLAUDE.md describe the installed GSD Path pipeline; its internals are an excluded dependency, so only their claims about files this repo carries were audited. Their source-checkout paths (`skills/`, `scripts/`, `plugin.json`) are stated by those docs not to apply to a consuming project.

Doc-vs-doc contradictions found: `.claude/skills/sssf/SKILL.md:76` (visualizer "ships in a later pass") against `.claude/skills/sssf/cookbooks/run_adw.md:122` (visualizer available through `just obs`); `.claude/skills/sssf-sandbox-orchestrator/references/models.md:21-30` (default roster on deepseek) against `.claude/skills/sssf/SKILL.md:76` and `.claude/skills/sssf/cookbooks/sssf_overview.md:40` (default model gemini-3.6-flash); `docs/superpowers/specs/2026-09-02-prdy-v1-design.md:181-183` (regrade out of scope) against `README.md:27,32` and `specs/61c66de7_regrade-command.md` (regrade built). Each side is recorded in its own section below.

## Doc: .claude/CLAUDE.md

| Claim | Type | Verdict | Evidence |
|-------|------|---------|----------|
| "@../AGENTS.md" and "@../WORKFLOW.md" imports resolve | structure | verified | AGENTS.md and WORKFLOW.md exist at repo root (git ls-files); .claude/CLAUDE.md:1-2 |

## Doc: .claude/skills/herdr/SKILL.md

| Claim | Type | Verdict | Evidence |
|-------|------|---------|----------|
| Cookbook and reference links: `cookbooks/live-config-reload.md`, `cookbooks/setup-disable-network-checks.md`, `references/command-reference.md` | structure | verified | all three exist under .claude/skills/herdr/ |

## Doc: .claude/skills/herdr/references/command-reference.md

| Claim | Type | Verdict | Evidence |
|-------|------|---------|----------|
| "herdr Command Reference (validated against 0.7.1)" | integration | unverifiable | command-reference.md:1; herdr is an external binary with no source in this repo; needs a herdr 0.7.1 install to replay the listed commands |
| Points to `SKILL.md` and `cookbooks/setup-disable-network-checks.md` | structure | verified | .claude/skills/herdr/SKILL.md and .claude/skills/herdr/cookbooks/setup-disable-network-checks.md exist |

## Doc: .claude/skills/sandbox-exe-dev/SKILL.md

| Claim | Type | Verdict | Evidence |
|-------|------|---------|----------|
| "`EXEDEV_CLI_PATH`: `.claude/skills/sandbox-exe-dev/exedev_cli/`" and "uv run exedev --help" | command | verified | sidecar: `uv run exedev --help` in that directory -> lists browser, doctor, exec, files, init, share, vm, whoami |
| "six core command groups plus three top-level helpers"; vm verbs list, info, stat, kill, restart, rename, resize, tag, comment, snapshot | feature | verified | sidecar: `uv run exedev vm --help` -> the same ten verbs; top-level help lists init, vm, exec, files, share, browser plus doctor and whoami (the doc itself names only two helpers) |
| exec flags `--cwd`, `--env`, `--root`, `--shell`, `--stdin`, `--background`, `--timeout` | command | verified | sidecar: `uv run exedev exec --help` -> all seven flags present |
| "mod? sbx 'just/sandbox/mod.just'" | config | stale | SKILL.md:332; justfile:93 reads `mod sbx 'just/sandbox/mod.just'` (no `?`, so the module is required, not optional) |
| Phase recipe tree under `just/sandbox/` and "just sbx lifecycle setup my-run" / "just sbx mount my-run" | structure | verified | just/sandbox/{mod,mount}.just, lifecycle/{create,fill,setup,execute,observe,teardown}.just, manage/{list,harvest,reap}.just, run/, orch/ tracked |
| Sources `ai_docs/exedev/faq-host-key.md`, `ai_docs/exedev/all.md`, `ai_docs/exedev/https-api.md` | structure | unverifiable | SKILL.md:29,263,310; no ai_docs/ directory in this repo; the doc says they live "in the project that drove the parity exercise" |
| "The full per-row parity table ... is at `/tmp/sandbox-parity/AGENT_SANDBOXES_FEATURE_PARITY.md`" | structure | unverifiable | SKILL.md:104,264; a /tmp path on the authoring machine, outside the repo |
| "uv run exedev doctor" expected output ends with `doctor: OK` | command | unverifiable | SKILL.md:26-28; needs a registered exe.dev account and outbound ssh; not run (external state) |

## Doc: .claude/skills/sandbox-exe-dev/cookbook/browser.md

| Claim | Type | Verdict | Evidence |
|-------|------|---------|----------|
| browser verbs init, start, nav, eval and the rest of the browser group | command | verified | sidecar: `uv run exedev browser --help` -> a11y, click, close, cookies, dom, eval, init, nav, pick, press, screenshot, scroll, start, status, type |
| Same content as `/agent-sandboxes/cookbook/browser.md` | structure | unverifiable | browser.md:170; the agent-sandboxes skill is not in this repo (no .claude/skills/agent-sandboxes) |

## Doc: .claude/skills/sandbox-exe-dev/cookbook/fleet.md

| Claim | Type | Verdict | Evidence |
|-------|------|---------|----------|
| Scripts `scripts/fleet-download-all.sh` and `scripts/fleet-restore.sh` | structure | verified | .claude/skills/sandbox-exe-dev/scripts/fleet-download-all.sh and fleet-restore.sh tracked; not executed (they act on live VMs) |

## Doc: .claude/skills/sandbox-exe-dev/examples/01_quickstart.md

| Claim | Type | Verdict | Evidence |
|-------|------|---------|----------|
| "uv run exedev init --name "$WORKFLOW_ID" --cpu 2 --memory 4GB --tag demo" | command | verified | sidecar: `uv run exedev init --help` -> --name, --cpu, --memory, --tag present; VM not created |
| Walkthrough "exercises every command group" against a live VM | integration | unverifiable | needs an exe.dev account and creates a billable VM; not run |

## Doc: .claude/skills/sandbox-exe-dev/exedev_cli/README.md

| Claim | Type | Verdict | Evidence |
|-------|------|---------|----------|
| Quick reference: files, vm, share, browser verb lists | command | verified | sidecar: `uv run exedev files --help` (13 verbs), `vm --help` (10), `share --help` (9), `browser --help` (15) match the README lists |
| Link to `../../agent-sandboxes/sandbox_cli/README.md` | structure | aspirational | README.md:3; .claude/skills/agent-sandboxes does not exist in this repo |
| "The full parity table lives at `/tmp/sandbox-parity/AGENT_SANDBOXES_FEATURE_PARITY.md`" | structure | unverifiable | README.md:58; a /tmp path outside the repo |
| See also: `../SKILL.md`, `../cookbook/browser.md` | structure | verified | both exist |

## Doc: .claude/skills/sssf-admin/SKILL.md

| Claim | Type | Verdict | Evidence |
|-------|------|---------|----------|
| Runbook recipes: sbx manage doctor/reap/list/harvest, sbx mount, sbx lifecycle execute/teardown, sbx run agent, sessions, phases | command | verified | `just --list --list-submodules` at audited HEAD in the verify sidecar |
| "`just sbx lifecycle execute <run-id> "<prompt>" [CONFIG] [ADW]`" | command | verified | recipe signature: execute RUN_ID PROMPT CONFIG="" ADW="sdlc" *EXTRA (`just --list --list-submodules` at audited HEAD in the verify sidecar) |
| Composes skills `sssf-sandbox-orchestrator`, `herdr`, `sssf`; reads references/build_patterns.md | structure | verified | all three SKILL.md files and .claude/skills/sssf-admin/references/build_patterns.md exist |
| "as of 0.8.0 the waits are `pane wait-output` and `agent wait`, both namespaced - there is no top-level `wait`" | integration | unverifiable | SKILL.md:35-37; herdr is an external binary with no source in this repo; needs `herdr --help` from a 0.8.0 install |

## Doc: .claude/skills/sssf-admin/references/build_patterns.md

| Claim | Type | Verdict | Evidence |
|-------|------|---------|----------|
| Marker table recipes: sbx manage doctor/harvest, sbx mount, sbx lifecycle create/fill/setup/execute/observe/teardown, sbx run agent/cmd | command | verified | `just --list --list-submodules` at audited HEAD in the verify sidecar |
| "`mount.just` resolves the run id by taking the **newest record** from `run_record.py list`" | feature | verified | just/sandbox/mount.just:15 |
| "`CONFIG` - a roster path (`adws/adw_sssf_config/sssf.frontier.config.yaml`)" | config | aspirational | build_patterns.md:104; `ls adws/adw_sssf_config` -> sssf.config.yaml only |

## Doc: .claude/skills/sssf-admin/references/fleet.md

| Claim | Type | Verdict | Evidence |
|-------|------|---------|----------|
| "The rosters live in `adws/adw_sssf_config/`: default (cheap), `frontier`, `deepestseek`, `open-weights`, `top-speed`." | config | aspirational | fleet.md:46-47,54; `ls adws/adw_sssf_config` -> sssf.config.yaml only |
| Recipes sbx manage list/reap, sbx mount, sbx lifecycle execute, sbx run agent/cmd, sessions, phases | command | verified | `just --list --list-submodules` at audited HEAD in the verify sidecar |

## Doc: .claude/skills/sssf-sandbox-orchestrator/SKILL.md

| Claim | Type | Verdict | Evidence |
|-------|------|---------|----------|
| Drive surface: `just sbx mount`, lifecycle create/fill/setup/execute/observe/teardown, manage list/harvest/reap/doctor, run cmd/agent, orch cc/pi | command | verified | `just --list --list-submodules` at audited HEAD in the verify sidecar lists all 15 |
| "It checks all six in one pass" and "Green ends with `sbx doctor: OK`" | command | stale | just/sandbox/manage/mod.just:28-36 runs seven checks (the extra one: "source repo resolves + clones anonymously"); the OK line is at mod.just:36 |
| "`just sbx mount RUN_ID [--limit N]` create -> fill -> setup -> observe. Never teardown." | command | verified | just/sandbox/mount.just:9-19 |
| "mint `sbx-<run-id>` ($50 default)" | config | verified | just/sandbox/lifecycle/create.just:22,138 |
| "The five gate assertions" A-E in setup | feature | verified | just/sandbox/lifecycle/setup.just:86,88,122,282-284 |
| "fetched into `refs/sandbox/<run-id>`" | feature | verified | just/sandbox/manage/harvest.just:39 |
| "The runtime key lives at `.sandbox/runs/<id>.key` (0600)" | config | verified | just/sandbox/lifecycle/create.just:132,161,168; .gitignore lists .sandbox/ |
| Cookbook and reference tables: eight cookbooks, five references | structure | verified | all 13 files exist under .claude/skills/sssf-sandbox-orchestrator/ |

## Doc: .claude/skills/sssf-sandbox-orchestrator/cookbooks/access_a_running_sandbox.md

| Claim | Type | Verdict | Evidence |
|-------|------|---------|----------|
| Every `just` recipe the doc invokes exists: sbx lifecycle execute, sbx manage harvest, sbx run agent, sbx run cmd | command | verified | `just --list --list-submodules` at audited HEAD in the verify sidecar; recipes not executed (they need exe.dev and a provisioning key) |
| Points to `.claude/skills/herdr/SKILL.md` | structure | verified | file tracked |

## Doc: .claude/skills/sssf-sandbox-orchestrator/cookbooks/debug_a_failed_gate.md

| Claim | Type | Verdict | Evidence |
|-------|------|---------|----------|
| "The SETUP gate (`just/sandbox/setup.just`, step 3/3) runs five assertions" | structure | stale | debug_a_failed_gate.md:3; the file is just/sandbox/lifecycle/setup.just (gate at setup.just:86); just/sandbox/setup.just does not exist |
| Recipes sbx lifecycle create/fill/setup/teardown and sbx run cmd; files `sandbox_mount/guest/provision.sh`, `sandbox_mount/guest/models.json.tmpl` | command | verified | `just --list --list-submodules` at audited HEAD in the verify sidecar; both files tracked |

## Doc: .claude/skills/sssf-sandbox-orchestrator/cookbooks/execute_work.md

| Claim | Type | Verdict | Evidence |
|-------|------|---------|----------|
| Every `just` recipe the doc invokes exists: sbx lifecycle execute, sbx run agent, sbx run cmd | command | verified | `just --list --list-submodules` at audited HEAD in the verify sidecar; recipes not executed (they need exe.dev and a provisioning key) |

## Doc: .claude/skills/sssf-sandbox-orchestrator/cookbooks/fan_out_n.md

| Claim | Type | Verdict | Evidence |
|-------|------|---------|----------|
| "ARMS=(sssf.config.yaml sssf.frontier.config.yaml)" | config | aspirational | fan_out_n.md:40,84,94; `ls adws/adw_sssf_config` -> sssf.config.yaml only |
| Recipes obs, sbx lifecycle create/fill/setup/execute/observe, sbx manage harvest/list/reap, sbx mount, sbx run cmd | command | verified | `just --list --list-submodules` at audited HEAD in the verify sidecar |

## Doc: .claude/skills/sssf-sandbox-orchestrator/cookbooks/just_command_model.md

| Claim | Type | Verdict | Evidence |
|-------|------|---------|----------|
| Every `just` recipe the doc invokes exists: adw plan, adw scout, adw sdlc, sbx lifecycle create/fill/setup/execute/observe/teardown, sbx manage reap, sbx run agent, sbx run cmd | command | verified | `just --list --list-submodules` at audited HEAD in the verify sidecar; recipes not executed (they need exe.dev and a provisioning key) |
| Names `just/adws.just` and `sandbox_mount/host/run_record.py` | structure | verified | both tracked |

## Doc: .claude/skills/sssf-sandbox-orchestrator/cookbooks/mount_one.md

| Claim | Type | Verdict | Evidence |
|-------|------|---------|----------|
| Every `just` recipe the doc invokes exists: sbx mount, sbx lifecycle create/fill/setup/execute/observe/teardown, sbx manage list, sbx manage reap, sbx run agent | command | verified | `just --list --list-submodules` at audited HEAD in the verify sidecar; recipes not executed (they need exe.dev and a provisioning key) |

## Doc: .claude/skills/sssf-sandbox-orchestrator/cookbooks/observe_and_report.md

| Claim | Type | Verdict | Evidence |
|-------|------|---------|----------|
| Every `just` recipe the doc invokes exists: obs, sbx lifecycle observe, sbx lifecycle setup, sbx manage harvest, sbx mount, sbx run agent, sbx run cmd | command | verified | `just --list --list-submodules` at audited HEAD in the verify sidecar; recipes not executed (they need exe.dev and a provisioning key) |

## Doc: .claude/skills/sssf-sandbox-orchestrator/cookbooks/teardown_and_reap.md

| Claim | Type | Verdict | Evidence |
|-------|------|---------|----------|
| Every `just` recipe the doc invokes exists: sbx lifecycle teardown, sbx manage reap, sbx mount | command | verified | `just --list --list-submodules` at audited HEAD in the verify sidecar; recipes not executed (they need exe.dev and a provisioning key) |

## Doc: .claude/skills/sssf-sandbox-orchestrator/references/gotchas.md

| Claim | Type | Verdict | Evidence |
|-------|------|---------|----------|
| "The root justfile sets `shell := [zsh, -ic]`" (quoting simplified) | config | stale | gotchas.md:38; `grep -n shell justfile` -> no match at audited HEAD; just/adws.just:15-18 repeats the same statement |
| "`just/adws.just` re-declares `set positional-arguments`, `set dotenv-load`, and its own `config :=`" and declares its own `default:` | config | verified | `just --list adw` shows default and ask recipes; just/adws.just:7,11-13,22 |
| "the function is `quality.run_inkwell_tests(run)`" | structure | stale | gotchas.md:100-102; adws/adw_modules/quality.py:149 defines run_tests; callers at adws/adw_build_test.py:56, adws/adw_plan_build_test.py:56, adws/adw_simple_sdlc.py:101,137 call quality.run_tests(run); no run_inkwell_tests anywhere |

## Doc: .claude/skills/sssf-sandbox-orchestrator/references/kickoff_paths.md

| Claim | Type | Verdict | Evidence |
|-------|------|---------|----------|
| Every `just` recipe the doc invokes exists: adw, obs, sbx lifecycle execute, sbx run agent | command | verified | `just --list --list-submodules` at audited HEAD in the verify sidecar; recipes not executed (they need exe.dev and a provisioning key) |

## Doc: .claude/skills/sssf-sandbox-orchestrator/references/models.md

| Claim | Type | Verdict | Evidence |
|-------|------|---------|----------|
| "`defaults.model: openrouter/deepseek/deepseek-v4-flash-0731`" with planner gemini-3.6-flash, reviewer glm-5.2, builder and scout inheriting deepseek | config | stale | models.md:21-30; adws/adw_sssf_config/sssf.config.yaml:5 default is openrouter/google/gemini-3.6-flash, :41 planner kimi-k3, :107 reviewer gpt-5.6-terra, :125 documenter gpt-5.6-luna |
| "### `adws/adw_sssf_config/sssf.frontier.config.yaml` - the frontier roster" | config | aspirational | models.md:32,41; `ls adws/adw_sssf_config` -> sssf.config.yaml only |
| Runtime key is `sbx-<run-id>`, `$50` default; model registry at `sandbox_mount/guest/models.json.tmpl` with four-field cost blocks | config | verified | just/sandbox/lifecycle/create.just:22,138; just/sandbox/manage/mod.just:34 asserts the four cost fields; template lists 10 model ids |
| Per-million rate table and ZDR routing notes | integration | unverifiable | models.md:95-111; provider prices and routing are OpenRouter facts, not checkable from the repo; needs the live OpenRouter model list |

## Doc: .claude/skills/sssf-sandbox-orchestrator/references/phases.md

| Claim | Type | Verdict | Evidence |
|-------|------|---------|----------|
| Phase contract: create, fill, setup, execute, observe, teardown, plus run cmd, manage harvest, run agent outside the phase list | command | verified | `just --list --list-submodules` at audited HEAD in the verify sidecar |
| "`git switch -c sbx/<run-id>`" run branch | feature | verified | just/sandbox/lifecycle/fill.just:78 |
| Names just/adws.just, just/sandbox/manage/list.just, just/sandbox/orch/mod.just, sandbox_mount/host/runs_table.py, adws/adw_sssf_config/sssf.config.yaml | structure | verified | all tracked |

## Doc: .claude/skills/sssf-sandbox-orchestrator/references/run_record.md

| Claim | Type | Verdict | Evidence |
|-------|------|---------|----------|
| "## The twelve fields" and "The schema is **closed**" | structure | verified | sandbox_mount/host/run_record.py:43-56 FIELDS has 12 names matching the table; :121,140 reject unknown fields |
| "`.sandbox/` is gitignored." | config | verified | .gitignore lists .sandbox/ |
| "Default `50.00`, per-run via `just sbx lifecycle create <id> --limit N`" | config | verified | just/sandbox/lifecycle/create.just:22,28-29 |

## Doc: .claude/skills/sssf-sandbox/SKILL.md

| Claim | Type | Verdict | Evidence |
|-------|------|---------|----------|
| What gets stamped: `adws/`, `justfile`, `.env.sample`, `just/adws.just`, `just/sandbox/`, `sandbox_mount/host/`, `sandbox_mount/guest/`, six skills | structure | verified | git ls-files lists all; .claude/skills/{sssf,sssf-sandbox,sssf-sandbox-orchestrator,herdr,sandbox-exe-dev,sssf-admin}/SKILL.md exist |
| "uv run .claude/skills/sssf-sandbox/scripts/install.py" | command | verified | script tracked; not executed (it stamps files) |
| "just sbx manage doctor" is the preflight | command | verified | just/sandbox/manage/mod.just:24-36; not executed (it contacts exe.dev over ssh) |
| `.env` knobs and defaults: OPENROUTER_PROVISIONING_KEY, SBX_SOURCE_REPO, SBX_TAG `sssf-sandbox`, SBX_APP_DIR empty, SBX_APP_CMD `bun run server.ts`, SBX_APP_PORT `4501` | config | verified | .env.sample:33-47; just/sandbox/lifecycle/create.just:85; just/sandbox/lifecycle/observe.just:37-39; sandbox_mount/host/source_repo.py:25 |
| "lifecycle: create, fill, setup, observe, execute, teardown; manage: list, harvest, reap, doctor" | command | verified | `just --list --list-submodules` at audited HEAD in the verify sidecar |

## Doc: .claude/skills/sssf/SKILL.md

| Claim | Type | Verdict | Evidence |
|-------|------|---------|----------|
| Routing table and deep-spec links: eight cookbooks and three references | structure | verified | all of cookbooks/{sssf_overview,install,create_adw,update_adw,create_config,update_config,update_modules,how_to_prompt_for_the_eng,run_adw}.md and references/{config,handoff,observability}.md exist under .claude/skills/sssf/ |
| "An orchestrator that improvised a status board queried a `runs` table and a `payload` column - neither exists (`sessions`, `payload_json`)" | structure | verified | adws/adw_modules/tracer.py:18 (sessions), 45,55 (payload_json); no runs table among the seven CREATE TABLE statements |
| "every ADW declares `REQUIRED_AGENTS` and calls `agents.validate()` first" | structure | stale | `grep -L REQUIRED_AGENTS adws/adw_*.py` -> adws/adw_prompt.py; it validates only the chosen agent at adw_prompt.py:23 |
| "Every ADW ends in `run.finish()`" | structure | verified | `grep -L "finish(" adws/adw_*.py` -> no files |
| "Pi coding agent only (`coding_agent: pi`), default model `gemini-3.6-flash` via openrouter, thinking `medium`. `claude_code` is schema-valid but stubbed until v2." | config | verified | adws/adw_sssf_config/sssf.config.yaml:4-6; adws/adw_modules/agent_cc.py:4,12 raises NotImplementedError |
| "The visualizer app ships in a later pass - observe via sqlite queries until then." | status | stale | SKILL.md:76; .claude/skills/sssf/apps/visualizer/ is tracked (package.json, server/, src/) and justfile:88-89 `obs` boots it; contradicts .claude/skills/sssf/cookbooks/run_adw.md:122 |

## Doc: .claude/skills/sssf/cookbooks/create_adw.md

| Claim | Type | Verdict | Evidence |
|-------|------|---------|----------|
| "uv run .claude/skills/sssf/scripts/make_adw.py --name review_docs --agents scout,builder" | command | verified | .claude/skills/sssf/scripts/make_adw.py tracked; not executed (it writes adws/adw_review_docs.py) |
| Links to update_adw.md, update_config.md, update_modules.md and names `adws/adw_sssf_config/sssf.config.yaml` | structure | verified | all four paths exist |

## Doc: .claude/skills/sssf/cookbooks/create_config.md

| Claim | Type | Verdict | Evidence |
|-------|------|---------|----------|
| Config is stamped at `adws/adw_sssf_config/sssf.config.yaml` by `make_config.py` | structure | verified | adws/adw_sssf_config/sssf.config.yaml and .claude/skills/sssf/scripts/make_config.py tracked |

## Doc: .claude/skills/sssf/cookbooks/how_to_prompt_for_the_eng.md

| Claim | Type | Verdict | Evidence |
|-------|------|---------|----------|
| "just phases" and links to run_adw.md and create_adw.md | command | verified | justfile:71-72; both cookbook files exist |

## Doc: .claude/skills/sssf/cookbooks/install.md

| Claim | Type | Verdict | Evidence |
|-------|------|---------|----------|
| "uv run .claude/skills/sssf/scripts/install.py" | command | verified | .claude/skills/sssf/scripts/install.py tracked; not executed (it stamps files into the cwd) |
| What gets stamped table: config, `.env.sample`, `adws/adw_*.py` "the twelve starter ADWs", adw_modules, prompt_engineering for five agents, harness_engineering, justfile | structure | verified | git ls-files: 12 adws/adw_*.py files, adws/adw_modules/, adws/adw_data/prompt_engineering/{planner,builder,scout,reviewer,documenter}/, adws/adw_data/harness_engineering/subagents.ts, .env.sample, justfile |
| "`install.py` appends `adws/adw_data/sessions/`, `adws/adw_data/sssf.db*`, and `.env`" to .gitignore | config | verified | .gitignore lists .env, adws/adw_data/sessions/, adws/adw_data/sssf.db*; .claude/skills/sssf/scripts/install.py:51-56 ensure_gitignore |
| "`just demo` runs two cheap read-only workflows back to back" | command | verified | justfile:29-34 (adw_prompt then adw_scout); not executed (calls a paid model) |

## Doc: .claude/skills/sssf/cookbooks/run_adw.md

| Claim | Type | Verdict | Evidence |
|-------|------|---------|----------|
| "just rosters" prints every roster on disk | command | aspirational | run_adw.md:31; no `rosters` recipe in `just --list --list-submodules` at audited HEAD in the verify sidecar; justfile:5 says rosters lives on "the example branch" |
| "just kill <adw_id>" stops a hung run | command | aspirational | run_adw.md:111,114; no `kill` recipe in `just --list --list-submodules` at audited HEAD in the verify sidecar; justfile:5 says kill lives on "the example branch" |
| "adws/adw_sssf_config/sssf.frontier.config.yaml" is a roster to pass with --config or SSSF_CONFIG | config | aspirational | run_adw.md:40,58-59; `ls adws/adw_sssf_config` -> sssf.config.yaml only |
| "the justfile recipes read `SSSF_CONFIG`" | config | verified | justfile:13 config := env_var_or_default("SSSF_CONFIG", ...) |
| "just phases <adw_id>" and "just procs <adw_id>" | command | verified | justfile:71-72,79-80; listed in `just --list --list-submodules` at audited HEAD in the verify sidecar |
| Observe queries use tables phases, events, gate_results, sessions in `adws/adw_data/sssf.db` | structure | verified | adws/adw_modules/tracer.py:18,28,38,60 CREATE TABLE statements; adws/adw_sssf_config/sssf.config.yaml:36 |
| "the visualizer app in the skill (`just obs`, ... :4600 + ... :4601)" | command | verified | justfile:87-89; .claude/skills/sssf/apps/visualizer/ tracked; not booted |

## Doc: .claude/skills/sssf/cookbooks/sssf_overview.md

| Claim | Type | Verdict | Evidence |
|-------|------|---------|----------|
| Layout of a stamped repo lists ten ADW scripts and adw_modules data_types, agents, runner, agent_pi, agent_cc, gates, changes, prompts, session, tracer, console, git_helper, utils | structure | stale | sssf_overview.md:13-38; every listed file exists, but adws/adw_quality.py, adws/adw_plan_build_test_quality.py, adws/adw_modules/permissions.py and adws/adw_modules/quality.py are tracked and not shown |
| "`coding_agent: pi`, default model `gemini-3.6-flash`, thinking `medium`" | config | verified | adws/adw_sssf_config/sssf.config.yaml:4-6 |

## Doc: .claude/skills/sssf/cookbooks/update_adw.md

| Claim | Type | Verdict | Evidence |
|-------|------|---------|----------|
| Names adw_plan_build.py, adw_plan_build_test.py, adw_simple_sdlc.py, adw_build_test.py, adw_modules/gates.py, adw_modules/agents.py, quality.py | structure | verified | each exists under adws/ or adws/adw_modules/ (git ls-files) |

## Doc: .claude/skills/sssf/cookbooks/update_config.md

| Claim | Type | Verdict | Evidence |
|-------|------|---------|----------|
| Names `sssf.config.yaml`, `adw_modules/data_types.py`, `references/config.md`, update_modules.md | structure | verified | adws/adw_sssf_config/sssf.config.yaml, adws/adw_modules/data_types.py, .claude/skills/sssf/references/config.md, .claude/skills/sssf/cookbooks/update_modules.md exist |

## Doc: .claude/skills/sssf/cookbooks/update_modules.md

| Claim | Type | Verdict | Evidence |
|-------|------|---------|----------|
| Module map: data_types.py, agents.py, runner.py, agent_pi.py, agent_cc.py, gates.py, changes.py, prompts.py, session.py, tracer.py, console.py, git_helper.py, utils.py | structure | verified | all 13 exist under adws/adw_modules/ (git ls-files) |

## Doc: .claude/skills/sssf/references/config.md

| Claim | Type | Verdict | Evidence |
|-------|------|---------|----------|
| "It lives at `adws/adw_sssf_config/sssf.config.yaml` - the default path every `adw_*.py` and the justfile resolve" | config | verified | justfile:13; file tracked |
| "set `SSSF_CONFIG` for the justfile" | config | verified | justfile:11-13 |
| Enforcement lives in `adw_modules/permissions.py` | structure | verified | adws/adw_modules/permissions.py tracked; adws/adw_sssf_config/sssf.config.yaml:23 |

## Doc: .claude/skills/sssf/references/handoff.md

| Claim | Type | Verdict | Evidence |
|-------|------|---------|----------|
| Output types live in `adw_modules/data_types.py`; prompts in `user.md` and `system.md`; examples cite adw_simple_sdlc.py and adw_plan.py | structure | verified | adws/adw_modules/data_types.py:85-123; adws/adw_data/prompt_engineering/*/{system,user}.md; adws/adw_simple_sdlc.py and adws/adw_plan.py tracked |

## Doc: .claude/skills/sssf/references/observability.md

| Claim | Type | Verdict | Evidence |
|-------|------|---------|----------|
| Trace schema is written by `tracer.py`; tables include sessions, phases, events, processes, agent_sessions | structure | verified | adws/adw_modules/tracer.py:18,28,38,49,60,71,80 |
| "`just procs <adw_id>` lists what is live" | command | verified | justfile:79-80 |
| "`just kill <adw_id>` stops children before the parent" | command | aspirational | observability.md:130; no `kill` recipe in `just --list --list-submodules` at audited HEAD in the verify sidecar |

## Doc: .claude/skills/sssf/templates/prompt_engineering/builder/user.md

| Claim | Type | Verdict | Evidence |
|-------|------|---------|----------|
| "Respond with ONLY valid JSON matching `BuildOutput`" | structure | verified | .claude/skills/sssf/templates/adws/adw_modules/data_types.py:93 class BuildOutput(EnvelopeBase); template file is byte-identical to the stamped copy under adws/ (cmp) |

## Doc: .claude/skills/sssf/templates/prompt_engineering/documenter/user.md

| Claim | Type | Verdict | Evidence |
|-------|------|---------|----------|
| "Respond with ONLY valid JSON matching `DocumentOutput`" | structure | verified | .claude/skills/sssf/templates/adws/adw_modules/data_types.py:123 class DocumentOutput(EnvelopeBase); template file is byte-identical to the stamped copy under adws/ (cmp) |

## Doc: .claude/skills/sssf/templates/prompt_engineering/planner/system.md

| Claim | Type | Verdict | Evidence |
|-------|------|---------|----------|
| "`subagent_create` / `_continue` / `_list` / `_remove`" tools are available | integration | verified | adws/adw_data/harness_engineering/subagents.ts:306,345,384,409 register the four tools; adws/adw_sssf_config/sssf.config.yaml wires the extension and names the tools for planner (lines 48-62) and scout (87-102); template prompt is byte-identical to the stamped copy under adws/ (cmp) |

## Doc: .claude/skills/sssf/templates/prompt_engineering/planner/user.md

| Claim | Type | Verdict | Evidence |
|-------|------|---------|----------|
| "Respond with ONLY valid JSON matching `PlanOutput`" | structure | verified | .claude/skills/sssf/templates/adws/adw_modules/data_types.py:85 class PlanOutput(EnvelopeBase); template file is byte-identical to the stamped copy under adws/ (cmp) |

## Doc: .claude/skills/sssf/templates/prompt_engineering/reviewer/user.md

| Claim | Type | Verdict | Evidence |
|-------|------|---------|----------|
| "Respond with ONLY valid JSON matching `ReviewOutput`" | structure | verified | .claude/skills/sssf/templates/adws/adw_modules/data_types.py:115 class ReviewOutput(EnvelopeBase); template file is byte-identical to the stamped copy under adws/ (cmp) |

## Doc: .claude/skills/sssf/templates/prompt_engineering/scout/system.md

| Claim | Type | Verdict | Evidence |
|-------|------|---------|----------|
| "`subagent_create` / `_continue` / `_list` / `_remove`" tools are available | integration | verified | adws/adw_data/harness_engineering/subagents.ts:306,345,384,409 register the four tools; adws/adw_sssf_config/sssf.config.yaml wires the extension and names the tools for planner (lines 48-62) and scout (87-102); template prompt is byte-identical to the stamped copy under adws/ (cmp) |

## Doc: .claude/skills/sssf/templates/prompt_engineering/scout/user.md

| Claim | Type | Verdict | Evidence |
|-------|------|---------|----------|
| "Respond with ONLY valid JSON matching `ScoutOutput`" | structure | verified | .claude/skills/sssf/templates/adws/adw_modules/data_types.py:103 class ScoutOutput(EnvelopeBase); template file is byte-identical to the stamped copy under adws/ (cmp) |

## Doc: AGENTS.md

| Claim | Type | Verdict | Evidence |
|-------|------|---------|----------|
| "Run the first successful interpreter with `-B .gsd-path/status_runtime.py --repo <absolute-root>`" | config | verified | AGENTS.md:86; .gsd-path/status_runtime.py is tracked (git ls-files). Launcher presence only; it was not executed because the sidecar has no .project/STATE.md |

## Doc: README.md

| Claim | Type | Verdict | Evidence |
|-------|------|---------|----------|
| "Python 3.12+ and uv" | config | verified | pyproject.toml:5 requires-python ">=3.12"; uv.lock tracked |
| "uv sync" then "uv run pytest" | command | verified | sidecar: `uv sync` rc=0; `uv run pytest -q` -> 152 passed, 1 skipped in 0.43s |
| "A GitHub token: `gh auth login`, or export `GITHUB_TOKEN`. Unauthenticated use is refused" | feature | verified | prdy/github.py:30-39 (gh auth token, else GITHUB_TOKEN); prdy/cli.py:73-76 prints message and returns 1 with no token |
| "Optional, for `--llm`: `OPENROUTER_API_KEY`" | config | verified | prdy/cli.py:68-69,79-82,120-122; prdy/llm.py:57-59 |
| Usage block: `prdy crawl` with --stars, --limit, --out, --topic (repeatable), --language, --llm, --model | command | verified | prdy/cli.py:30-40 defines every flag; `uv run prdy --help` lists crawl. Live crawl not run (needs GitHub network and token) |
| "uv run prdy grade ./corpus/acme__widgets/docs__prd__login.md" | command | verified | sidecar: `uv run prdy grade tests/fixtures/good_prd.md` -> "94 A" plus reasons, rc=0; prdy/cli.py:115-137 |
| "uv run prdy list --out ./corpus --min-grade B --sort stars" and "--json" | command | verified | prdy/cli.py:47-51,150-159; sidecar: `uv run prdy list --out ./nonexistent` -> "no PRDs in the index" rc=0; with --json -> [] |
| "`regrade` re-runs the rubric on every saved document and rewrites `grade_*` in the index and sidecars, leaving the `llm_*` fields alone; it exits 1 when the corpus or its index is missing" | feature | verified | prdy/cli.py:162-186; sidecar: `uv run prdy regrade --out ./nonexistent` -> "no corpus index at nonexistent/index.jsonl" rc=1; tests/test_regrade.py:18,25,31 pass |
| "`--limit` caps the number of repositories examined, not the number of PRDs found" | feature | verified | prdy/cli.py:37; prdy/github.py:134-154 search_repos yields at most `limit` repos |
| "Exit codes: `0` success (even when nothing was found); `1` usage or auth error; `2` the crawl aborted on an unrecoverable API error after partial progress" | feature | verified | prdy/cli.py:60-63 (argparse exit mapped to 1), 74-76, 90-92, 97-100; sidecar: `uv run prdy bogus` rc=1 |
| Corpus layout: `index.jsonl`, `acme__widgets/docs__prd__login.md`, `docs__prd__login.meta.json` "same fields as its index row" | structure | verified | prdy/store.py:10,85-94 (repo_dir, document_paths), 97-105 (write_meta dumps row.to_dict()), 67-82 (upsert) |
| "Row fields: repo, path, url, html_url, blob_sha, default_branch, fetched_at, stars, topics, repo_license, inline_license, size, title, grade_score, grade_letter, grade_reasons, llm_score, llm_critique, llm_model, skipped" | structure | verified | prdy/store.py:14-34 Row dataclass, same 20 fields in the same order |
| "Re-crawling skips any candidate whose `blob_sha` is already indexed" | feature | verified | prdy/crawl.py:86-95 (also re-fetches when --llm is set and llm_score is null, per the design spec) |
| "Skipped candidates (`tree truncated`, `over 1 MB`, `content sniff`, `fetch failed: <reason>`, `write failed: <reason>`) keep an index row" | feature | verified | prdy/crawl.py:75,107,114,118,133 each call record(row) -> store.upsert |
| "so they are not re-examined" (for a `tree truncated` row) | feature | aspirational | prdy/crawl.py:70-76: get_tree runs for every repo before any index lookup, and a truncated tree records the path "" row again on every crawl; only blob-level skips are short-circuited at crawl.py:93 |
| Rubric table: sections 8 each = 64; length band 0/6/12/8 = 12; headings 8; lists/table 8; date 4 + owner line 4 | feature | verified | prdy/grade.py:172-212; RUBRIC_TEXT grade.py:120-129; tests/test_grade.py passes |
| "A >= 85, B >= 70, C >= 55, D >= 40, F below. `prdy grade <file>` prints the score and every reason a check fell short" | feature | verified | prdy/grade.py:161-165; prdy/cli.py:125-127; sidecar: `uv run prdy grade tests/fixtures/weak_prd.md` -> "8 F" plus 12 reasons |
| "Design: `docs/superpowers/specs/2026-09-02-prdy-v1-design.md`" | structure | verified | file tracked (git ls-files) |

## Doc: WORKFLOW.md

| Claim | Type | Verdict | Evidence |
|-------|------|---------|----------|
| "Project installs record the selected runtime in `.gsd-path/runtime.json` and keep a stable launcher at `.gsd-path/status_runtime.py`" | config | verified | WORKFLOW.md:103-104; .gsd-path/runtime.json = schema gsd-path/runtime/v1, version 1.7.1; .gsd-path/status_runtime.py tracked |

## Doc: adws/adw_data/prompt_engineering/builder/user.md

| Claim | Type | Verdict | Evidence |
|-------|------|---------|----------|
| "Respond with ONLY valid JSON matching `BuildOutput`" | structure | verified | adws/adw_modules/data_types.py:93 class BuildOutput(EnvelopeBase) |

## Doc: adws/adw_data/prompt_engineering/documenter/user.md

| Claim | Type | Verdict | Evidence |
|-------|------|---------|----------|
| "Respond with ONLY valid JSON matching `DocumentOutput`" | structure | verified | adws/adw_modules/data_types.py:123 class DocumentOutput(EnvelopeBase) |

## Doc: adws/adw_data/prompt_engineering/planner/system.md

| Claim | Type | Verdict | Evidence |
|-------|------|---------|----------|
| "`subagent_create` / `_continue` / `_list` / `_remove`" tools are available | integration | verified | adws/adw_data/harness_engineering/subagents.ts:306,345,384,409 register the four tools; adws/adw_sssf_config/sssf.config.yaml wires the extension and names the tools for planner (lines 48-62) and scout (87-102) |

## Doc: adws/adw_data/prompt_engineering/planner/user.md

| Claim | Type | Verdict | Evidence |
|-------|------|---------|----------|
| "Respond with ONLY valid JSON matching `PlanOutput`" | structure | verified | adws/adw_modules/data_types.py:85 class PlanOutput(EnvelopeBase) |

## Doc: adws/adw_data/prompt_engineering/reviewer/user.md

| Claim | Type | Verdict | Evidence |
|-------|------|---------|----------|
| "Respond with ONLY valid JSON matching `ReviewOutput`" | structure | verified | adws/adw_modules/data_types.py:115 class ReviewOutput(EnvelopeBase) |

## Doc: adws/adw_data/prompt_engineering/scout/system.md

| Claim | Type | Verdict | Evidence |
|-------|------|---------|----------|
| "`subagent_create` / `_continue` / `_list` / `_remove`" tools are available | integration | verified | adws/adw_data/harness_engineering/subagents.ts:306,345,384,409 register the four tools; adws/adw_sssf_config/sssf.config.yaml wires the extension and names the tools for planner (lines 48-62) and scout (87-102) |

## Doc: adws/adw_data/prompt_engineering/scout/user.md

| Claim | Type | Verdict | Evidence |
|-------|------|---------|----------|
| "Respond with ONLY valid JSON matching `ScoutOutput`" | structure | verified | adws/adw_modules/data_types.py:103 class ScoutOutput(EnvelopeBase) |

## Doc: docs/superpowers/plans/2026-09-02-prdy-v1.md

| Claim | Type | Verdict | Evidence |
|-------|------|---------|----------|
| All 74 step checkboxes are unchecked (`- [ ]`) | status | stale | `grep -c "^- \[ \]"` -> 74, `grep -c "^- \[x\]"` -> 0; every task landed: git log 030c3db (Task 1) through 351c1cd (Task 14) and b7ba8cb |
| "Only runtime dependency: `httpx`. Dev dependency: `pytest`." | config | verified | pyproject.toml:6,12 |
| File Structure: "prdy/cli.py argparse; cmd_crawl / cmd_grade / cmd_list" and "tests/test_*.py one test module per source module, plus test_live.py" | structure | stale | plan.md:33-47; prdy/cli.py:64 also wires cmd_regrade; tests/test_regrade.py exists with no matching source module |
| File Structure: pyproject.toml, .gitignore, prdy/{__init__,cli,discover,grade,store,github,llm,crawl}.py, tests/conftest.py, six named fixtures | structure | verified | git ls-files lists every named path, including tests/fixtures/{search_page.json,tree_widgets.json,tree_notes.json,good_prd.md,weak_prd.md,install_notes.md} |
| "Document file naming: the original extension is dropped before `.md` is appended" | feature | verified | prdy/store.py:89-94 |
| "The 8-point ownership check is split 4 + 4 (date, owner line)" | feature | verified | prdy/grade.py:203-210 |
| "If `test_grade_good_prd` reports a score other than 94" | feature | verified | sidecar: `uv run prdy grade tests/fixtures/good_prd.md` -> 94 A |
| "Commit messages end with the session's `Co-Authored-By` and `Claude-Session` trailers." | status | verified | `git log -3 --format=%(trailers) b7ba8cb` -> Co-Authored-By and Claude-Session trailers on b7ba8cb, b347433, 351c1cd |

## Doc: docs/superpowers/specs/2026-09-02-prdy-v1-design.md

| Claim | Type | Verdict | Evidence |
|-------|------|---------|----------|
| "Status: approved in conversation, awaiting written review." | status | stale | design.md:3; v1 is implemented and merged: git log 030c3db..b7ba8cb (feat commits), 152 tests pass |
| CLI block lists three commands: crawl, grade, list | command | stale | design.md:26-32; prdy/cli.py:53-54,64 adds a fourth command `regrade`; `uv run prdy --help` -> {crawl,grade,list,regrade} |
| "`cli.py` argparse entry point; wires the others, no logic of its own" | structure | stale | design.md:50; prdy/cli.py:162-186 cmd_regrade holds the regrade loop (read index, grade, count, write) inside cli.py |
| Modules list: cli.py, github.py, discover.py, grade.py, llm.py, store.py | structure | stale | design.md:48-58; prdy/crawl.py exists and owns run_crawl (the plan records this as a refinement at plan.md:27) |
| "`cli.py` is the only module that prints." | structure | verified | `grep -rn "print(" prdy/` -> matches only in prdy/cli.py |
| github.py: token from `gh auth token` or `GITHUB_TOKEN`; search_repos pages `/search/repositories` sorted by stars; get_tree recursive with truncated flag; get_blob via contents API raw media type | feature | verified | prdy/github.py:30-39,134-154 (per_page=min(100, limit)),156-159,161-163; tests/test_github.py passes |
| "at 0 the client sleeps until `X-RateLimit-Reset` and retries. HTTP 403 with a secondary-rate-limit body sleeps 60 s. Network errors retry three times with backoff. 404 and other 403s raise `SkipRepo`." | feature | verified | prdy/github.py:79-86 (3 retries, 2**n backoff), 88-109 (60 s default, Retry-After honoured), 112-118, 130-132 |
| discover.py: is_prd_path extension set, `requirements.txt` never matches, whole-word prd, prd/prds directory, requirements names; looks_like_prd on first 2 KB; files over 1 MB skipped before fetch | feature | verified | prdy/discover.py:27-48,51,56-59; prdy/crawl.py:106-109; tests/test_discover.py passes |
| grade.py points table summing to 100 and letter thresholds | feature | verified | prdy/grade.py:1,161-212; tests/test_grade.py passes |
| llm.py: OpenRouter chat completion, key from `OPENROUTER_API_KEY`, default model in one constant, "a malformed reply is retried once, then recorded as `null` with the error in `critique`" | integration | verified | prdy/llm.py:14-15,57-78 (two attempts, LlmGrade(score=None, critique=last_error)); tests/test_llm.py passes. Live OpenRouter call not made |
| store.py corpus layout and "`upsert(row)` rewrites `index.jsonl` with the row replacing any existing row with the same `(repo, path)`" | structure | verified | prdy/store.py:67-82,85-94; tests/test_store.py passes |
| "a candidate whose `blob_sha` already matches the index is not fetched or re-graded unless `--llm` is set and `llm_score` is null" | feature | verified | prdy/crawl.py:86-95 |
| Inline license detection: first line matching license, licence, copyright, (c) sign, SPDX-License-Identifier, or CC BY, trimmed to 200 characters | feature | verified | prdy/discover.py:52,62-67 |
| Data flow step 5: "Print a summary: repos examined, candidates, saved, skipped, and the top five by score" | feature | verified | prdy/cli.py:103-112; prdy/crawl.py:140 (top 5); the summary also prints Unchanged |
| "Live smoke, skipped unless `PRDY_LIVE=1`: one real search with `--limit 1`." | command | verified | tests/test_live.py:8-12; sidecar pytest run reports 1 skipped |
| Out of scope for v1: "re-grading old rows when the rubric changes (a `regrade` command is the obvious next feature)" | status | stale | design.md:181-183; regrade shipped in bf5edfc: prdy/cli.py:162-186, tests/test_regrade.py |

## Doc: specs/61c66de7_regrade-command.md

| Claim | Type | Verdict | Evidence |
|-------|------|---------|----------|
| Behaviour spec: `prdy regrade [--out <dir>]`, exit 1 when the directory or index.jsonl is missing, skipped rows ignored, missing .md left untouched, one summary line, exit 0 | feature | verified | prdy/cli.py:53-54,162-186; tests/test_regrade.py passes (5 tests) |
| "`prdy/store.py` - add `write_meta`" and "Make `write_document` call `write_meta`" | structure | verified | prdy/store.py:97-105,108-116 |
| Tests section names seven tests, including `test_regrade_updates_meta_sidecar`, `test_regrade_preserves_llm_fields`, `test_regrade_parses` | structure | stale | spec.md:140-167; tests/test_regrade.py:9,18,25,31,91 defines five tests; the sidecar, score, and llm checks are merged into test_regrade_updates_scores_and_preserves_llm_fields and the parser test is test_regrade_flags_parse |
| README change: add `uv run prdy regrade --out ./corpus` and the one-sentence description | structure | verified | README.md:27,32 |
| "No changes to `grade.py` itself." | structure | verified | `git show --stat bf5edfc` -> README.md, prdy/cli.py, prdy/store.py, sandboxes.md, the spec, tests/test_regrade.py; no grade.py |
| "full suite must stay green (was: 147 passed, 1 skipped)" | command | verified | sidecar: `uv run pytest -q` -> 152 passed, 1 skipped (147 plus the five regrade tests) |

## Descriptive docs

- .claude/skills/herdr/cookbooks/live-config-reload.md
- .claude/skills/herdr/cookbooks/setup-disable-network-checks.md
- .claude/skills/sssf/templates/prompt_engineering/builder/system.md
- .claude/skills/sssf/templates/prompt_engineering/documenter/system.md
- .claude/skills/sssf/templates/prompt_engineering/reviewer/system.md
- adws/adw_data/prompt_engineering/builder/system.md
- adws/adw_data/prompt_engineering/documenter/system.md
- adws/adw_data/prompt_engineering/reviewer/system.md
- tests/fixtures/good_prd.md
- tests/fixtures/install_notes.md
- tests/fixtures/weak_prd.md

Scope reasons. The three `tests/fixtures/*.md` files are test input for the grader and crawler (sample PRDs and a decoy install note), not statements about this project. The builder, documenter and reviewer `system.md` prompts are instructions to an agent with no claim about the repo that reality can contradict. The two herdr cookbooks describe procedures for the external herdr binary and name nothing in this repository.

## Alignment (alignment mode only)

Not applicable: alignment mode is off for this run.

## User rulings

| Queue # | Ruling | User's words | Planned |
|---------|--------|--------------|---------|
| 1 | accept-drift | "if it's not critical to remove them, just keep the skills" (accept-drift proposed by define; user approved intent 2026-11-15: "approve intent") | n/a (accept-drift) |
| 2 | accept-drift | "if it's not critical to remove them, just keep the skills" (accept-drift proposed by define; user approved intent 2026-11-15: "approve intent") | n/a (accept-drift) |
| 3 | accept-drift | "if it's not critical to remove them, just keep the skills" (accept-drift proposed by define; user approved intent 2026-11-15: "approve intent") | n/a (accept-drift) |
| 4 | accept-drift | "if it's not critical to remove them, just keep the skills" (accept-drift proposed by define; user approved intent 2026-11-15: "approve intent") | n/a (accept-drift) |
| 5 | accept-drift | "if it's not critical to remove them, just keep the skills" (accept-drift proposed by define; user approved intent 2026-11-15: "approve intent") | n/a (accept-drift) |
| 6 | accept-drift | "if it's not critical to remove them, just keep the skills" (accept-drift proposed by define; user approved intent 2026-11-15: "approve intent") | n/a (accept-drift) |
| 7 | accept-drift | "if it's not critical to remove them, just keep the skills" (accept-drift proposed by define; user approved intent 2026-11-15: "approve intent") | n/a (accept-drift) |
| 8 | accept-drift | "if it's not critical to remove them, just keep the skills" (accept-drift proposed by define; user approved intent 2026-11-15: "approve intent") | n/a (accept-drift) |
| 9 | accept-drift | "if it's not critical to remove them, just keep the skills" (accept-drift proposed by define; user approved intent 2026-11-15: "approve intent") | n/a (accept-drift) |
| 10 | accept-drift | "if it's not critical to remove them, just keep the skills" (accept-drift proposed by define; user approved intent 2026-11-15: "approve intent") | n/a (accept-drift) |
| 11 | accept-drift | "if it's not critical to remove them, just keep the skills" (accept-drift proposed by define; user approved intent 2026-11-15: "approve intent") | n/a (accept-drift) |
| 12 | accept-drift | "if it's not critical to remove them, just keep the skills" (accept-drift proposed by define; user approved intent 2026-11-15: "approve intent") | n/a (accept-drift) |
| 13 | accept-drift | "if it's not critical to remove them, just keep the skills" (accept-drift proposed by define; user approved intent 2026-11-15: "approve intent") | n/a (accept-drift) |
| 14 | accept-drift | "if it's not critical to remove them, just keep the skills" (accept-drift proposed by define; user approved intent 2026-11-15: "approve intent") | n/a (accept-drift) |
| 15 | accept-drift | "if it's not critical to remove them, just keep the skills" (accept-drift proposed by define; user approved intent 2026-11-15: "approve intent") | n/a (accept-drift) |
| 16 | accept-drift | "if it's not critical to remove them, just keep the skills" (accept-drift proposed by define; user approved intent 2026-11-15: "approve intent") | n/a (accept-drift) |
| 17 | accept-drift | "if it's not critical to remove them, just keep the skills" (accept-drift proposed by define; user approved intent 2026-11-15: "approve intent") | n/a (accept-drift) |
| 18 | accept-drift | "if it's not critical to remove them, just keep the skills" (accept-drift proposed by define; user approved intent 2026-11-15: "approve intent") | n/a (accept-drift) |
| 19 | accept-drift | "if it's not critical to remove them, just keep the skills" (accept-drift proposed by define; user approved intent 2026-11-15: "approve intent") | n/a (accept-drift) |
| 20 | accept-drift | "if it's not critical to remove them, just keep the skills" (accept-drift proposed by define; user approved intent 2026-11-15: "approve intent") | n/a (accept-drift) |
| 21 | accept-drift | "if it's not critical to remove them, just keep the skills" (accept-drift proposed by define; user approved intent 2026-11-15: "approve intent") | n/a (accept-drift) |
| 22 | accept-drift | "if it's not critical to remove them, just keep the skills" (accept-drift proposed by define; user approved intent 2026-11-15: "approve intent") | n/a (accept-drift) |
| 23 | accept-drift | "if it's not critical to remove them, just keep the skills" (accept-drift proposed by define; user approved intent 2026-11-15: "approve intent") | n/a (accept-drift) |
| 24 | accept-drift | "if it's not critical to remove them, just keep the skills" (accept-drift proposed by define; user approved intent 2026-11-15: "approve intent") | n/a (accept-drift) |
| 25 | accept-drift | "if it's not critical to remove them, just keep the skills" (accept-drift proposed by define; user approved intent 2026-11-15: "approve intent") | n/a (accept-drift) |
| 26 | accept-drift | "if it's not critical to remove them, just keep the skills" (accept-drift proposed by define; user approved intent 2026-11-15: "approve intent") | n/a (accept-drift) |
| 27 | accept-drift | "if it's not critical to remove them, just keep the skills" (accept-drift proposed by define; user approved intent 2026-11-15: "approve intent") | n/a (accept-drift) |
| 28 | fix-doc | "defer to you" (define recommended: fix README) | T002 |
| 29 | accept-drift | "defer to you" (define recommended: accept drift in dated docs) | n/a (accept-drift) |
| 30 | accept-drift | "defer to you" (define recommended: accept drift in dated docs) | n/a (accept-drift) |
| 31 | accept-drift | "defer to you" (define recommended: accept drift in dated docs) | n/a (accept-drift) |
| 32 | accept-drift | "defer to you" (define recommended: accept drift in dated docs) | n/a (accept-drift) |
| 33 | accept-drift | "defer to you" (define recommended: accept drift in dated docs) | n/a (accept-drift) |
| 34 | accept-drift | "defer to you" (define recommended: accept drift in dated docs) | n/a (accept-drift) |
| 35 | accept-drift | "defer to you" (define recommended: accept drift in dated docs) | n/a (accept-drift) |
| 36 | accept-drift | "defer to you" (define recommended: accept drift in dated docs) | n/a (accept-drift) |

## Remediation queue

| # | Doc | Claim | Verdict | Class | Suggested action |
|---|-----|-------|---------|-------|------------------|
| 1 | .claude/skills/herdr/references/command-reference.md | "herdr Command Reference (validated against 0.7.1)" | unverifiable | NEEDS-USER | Confirm against the installed herdr version, or accept as vendor documentation |
| 2 | .claude/skills/sandbox-exe-dev/SKILL.md | "mod? sbx 'just/sandbox/mod.just'" | stale | fix-doc | Match the doc to the root justfile, or make the module optional |
| 3 | .claude/skills/sandbox-exe-dev/SKILL.md | Sources `ai_docs/exedev/faq-host-key.md`, `ai_docs/exedev/all.md`, `ai_docs/exedev/https-api.md` | unverifiable | fix-doc | Drop the references or vendor the files |
| 4 | .claude/skills/sandbox-exe-dev/SKILL.md | "The full per-row parity table ... is at `/tmp/sandbox-parity/AGENT_SANDBOXES_FEATURE_PARITY.md`" | unverifiable | fix-doc | Remove the /tmp pointer or commit the table |
| 5 | .claude/skills/sandbox-exe-dev/SKILL.md | "uv run exedev doctor" expected output ends with `doctor: OK` | unverifiable | NEEDS-USER | Run `exedev doctor` on a host with an exe.dev account |
| 6 | .claude/skills/sandbox-exe-dev/cookbook/browser.md | Same content as `/agent-sandboxes/cookbook/browser.md` | unverifiable | fix-doc | Drop the cross-reference or state that the skill is installed globally |
| 7 | .claude/skills/sandbox-exe-dev/examples/01_quickstart.md | Walkthrough "exercises every command group" against a live VM | unverifiable | NEEDS-USER | Run the quickstart on a host with an exe.dev account |
| 8 | .claude/skills/sandbox-exe-dev/exedev_cli/README.md | Link to `../../agent-sandboxes/sandbox_cli/README.md` | aspirational | fix-doc | Remove the link or point at the globally installed skill |
| 9 | .claude/skills/sandbox-exe-dev/exedev_cli/README.md | "The full parity table lives at `/tmp/sandbox-parity/AGENT_SANDBOXES_FEATURE_PARITY.md`" | unverifiable | fix-doc | Remove the /tmp pointer or commit the table |
| 10 | .claude/skills/sssf-admin/SKILL.md | "as of 0.8.0 the waits are `pane wait-output` and `agent wait`, both namespaced - there is no top-level `wait`" | unverifiable | NEEDS-USER | Confirm against the installed herdr version |
| 11 | .claude/skills/sssf-admin/references/build_patterns.md | "`CONFIG` - a roster path (`adws/adw_sssf_config/sssf.frontier.config.yaml`)" | aspirational | fix-doc | Use the existing sssf.config.yaml path or mark the path as an example |
| 12 | .claude/skills/sssf-admin/references/fleet.md | "The rosters live in `adws/adw_sssf_config/`: default (cheap), `frontier`, `deepestseek`, `open-weights`, `top-speed`." | aspirational | NEEDS-USER | Decide: add the four rosters or cut the list to what exists |
| 13 | .claude/skills/sssf-sandbox-orchestrator/SKILL.md | "It checks all six in one pass" and "Green ends with `sbx doctor: OK`" | stale | fix-doc | Say seven checks and name the source-repo probe |
| 14 | .claude/skills/sssf-sandbox-orchestrator/cookbooks/debug_a_failed_gate.md | "The SETUP gate (`just/sandbox/setup.just`, step 3/3) runs five assertions" | stale | fix-doc | Correct the path to just/sandbox/lifecycle/setup.just |
| 15 | .claude/skills/sssf-sandbox-orchestrator/cookbooks/fan_out_n.md | "ARMS=(sssf.config.yaml sssf.frontier.config.yaml)" | aspirational | NEEDS-USER | Decide: add a second roster file or mark the arm as an example |
| 16 | .claude/skills/sssf-sandbox-orchestrator/references/gotchas.md | "The root justfile sets `shell := [zsh, -ic]`" (quoting simplified) | stale | NEEDS-USER | Decide: set the shell in the root justfile, or correct the gotcha and the just/adws.just comment |
| 17 | .claude/skills/sssf-sandbox-orchestrator/references/gotchas.md | "the function is `quality.run_inkwell_tests(run)`" | stale | fix-doc | Remove or rewrite the "Pre-existing bug, now fixed" note; it does not describe this repo |
| 18 | .claude/skills/sssf-sandbox-orchestrator/references/models.md | "`defaults.model: openrouter/deepseek/deepseek-v4-flash-0731`" with planner gemini-3.6-flash, reviewer glm-5.2, builder and scout inheriting deepseek | stale | fix-doc | Regenerate the default-roster table from sssf.config.yaml |
| 19 | .claude/skills/sssf-sandbox-orchestrator/references/models.md | "### `adws/adw_sssf_config/sssf.frontier.config.yaml` - the frontier roster" | aspirational | NEEDS-USER | Decide: add the frontier roster or remove the section |
| 20 | .claude/skills/sssf-sandbox-orchestrator/references/models.md | Per-million rate table and ZDR routing notes | unverifiable | NEEDS-USER | Confirm rates against OpenRouter or mark the table with its capture date |
| 21 | .claude/skills/sssf/SKILL.md | "every ADW declares `REQUIRED_AGENTS` and calls `agents.validate()` first" | stale | NEEDS-USER | Decide: add REQUIRED_AGENTS to adw_prompt.py or note the single-agent exception in the rule |
| 22 | .claude/skills/sssf/SKILL.md | "The visualizer app ships in a later pass - observe via sqlite queries until then." | stale | fix-doc | Replace the sentence with a pointer to `just obs` |
| 23 | .claude/skills/sssf/cookbooks/run_adw.md | "just rosters" prints every roster on disk | aspirational | NEEDS-USER | Decide: add a `rosters` recipe or remove the command from the cookbook |
| 24 | .claude/skills/sssf/cookbooks/run_adw.md | "just kill <adw_id>" stops a hung run | aspirational | NEEDS-USER | Decide: add a `kill` recipe or remove the command from the cookbook |
| 25 | .claude/skills/sssf/cookbooks/run_adw.md | "adws/adw_sssf_config/sssf.frontier.config.yaml" is a roster to pass with --config or SSSF_CONFIG | aspirational | NEEDS-USER | Decide: add a frontier roster file or mark the path as an example |
| 26 | .claude/skills/sssf/cookbooks/sssf_overview.md | Layout of a stamped repo lists ten ADW scripts and adw_modules data_types, agents, runner, agent_pi, agent_cc, gates, changes, prompts, session, tracer, console, git_helper, utils | stale | fix-doc | Add the two quality ADWs and the permissions and quality modules to the layout |
| 27 | .claude/skills/sssf/references/observability.md | "`just kill <adw_id>` stops children before the parent" | aspirational | NEEDS-USER | Decide: add a `kill` recipe or remove the claim |
| 28 | README.md | "so they are not re-examined" (for a `tree truncated` row) | aspirational | NEEDS-USER | Decide: reword README to limit "not re-examined" to file-level skips, or make crawl skip repos already indexed as tree truncated |
| 29 | docs/superpowers/plans/2026-09-02-prdy-v1.md | All 74 step checkboxes are unchecked (`- [ ]`) | stale | fix-doc | Tick the steps or add a header line stating the plan is complete |
| 30 | docs/superpowers/plans/2026-09-02-prdy-v1.md | File Structure: "prdy/cli.py argparse; cmd_crawl / cmd_grade / cmd_list" and "tests/test_*.py one test module per source module, plus test_live.py" | stale | fix-doc | Add the regrade command and tests/test_regrade.py, or mark the plan as v1-only history |
| 31 | docs/superpowers/specs/2026-09-02-prdy-v1-design.md | "Status: approved in conversation, awaiting written review." | stale | fix-doc | Update the status line to reflect that v1 shipped |
| 32 | docs/superpowers/specs/2026-09-02-prdy-v1-design.md | CLI block lists three commands: crawl, grade, list | stale | fix-doc | Add `prdy regrade [--out]` to the CLI block or mark the spec as v1-only history |
| 33 | docs/superpowers/specs/2026-09-02-prdy-v1-design.md | "`cli.py` argparse entry point; wires the others, no logic of its own" | stale | NEEDS-USER | Decide: move the regrade loop out of cli.py, or drop the "no logic of its own" rule from the spec |
| 34 | docs/superpowers/specs/2026-09-02-prdy-v1-design.md | Modules list: cli.py, github.py, discover.py, grade.py, llm.py, store.py | stale | fix-doc | Add prdy/crawl.py to the module list |
| 35 | docs/superpowers/specs/2026-09-02-prdy-v1-design.md | Out of scope for v1: "re-grading old rows when the rubric changes (a `regrade` command is the obvious next feature)" | stale | fix-doc | Note that regrade has since been built, or mark the section as v1-only history |
| 36 | specs/61c66de7_regrade-command.md | Tests section names seven tests, including `test_regrade_updates_meta_sidecar`, `test_regrade_preserves_llm_fields`, `test_regrade_parses` | stale | fix-doc | Record the as-built test names, or leave as plan history |
