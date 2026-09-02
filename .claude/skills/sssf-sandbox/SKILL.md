---
name: sssf-sandbox
description: Install the Super Simple Software Factory plus its exe.dev sandbox surface into any repo, and run the non-billable preflight. Use for `/sssf-sandbox install`, "stamp the factory into this repo", "add sandboxes to sssf", or `just sbx manage doctor`. Operation (mount, execute, observe, harvest, teardown) belongs to sssf-sandbox-orchestrator; managed builds belong to sssf-admin.
argument-hint: "[install|doctor]"
---

# SSSF Sandbox — the installer

This skill stamps a complete factory-with-sandboxes into the current repo and stops.
It never creates a VM, mints a key, or calls a model.

## What gets stamped

| Into the target | What it is | Who drives it |
|---|---|---|
| `adws/`, `justfile`, `.env.sample` | upstream SSSF: deterministic ADWs, plus an OpenRouter-only roster on a fresh repo (the VM holds only an OpenRouter key) | `sssf` skill |
| `just/adws.just` (`just adw …`) | in-sandbox execution layer, one recipe per ADW | the VM, via `execute` |
| `just/sandbox/` (`just sbx …`) | out-of-sandbox lifecycle: create, fill, setup, observe, execute, teardown; manage: list, harvest, reap, doctor | `sssf-sandbox-orchestrator` |
| `sandbox_mount/host/` | run records, runs table, source-repo resolution | the recipes |
| `sandbox_mount/guest/` | provisioner and pi model registry the VM runs | `setup` |
| `.claude/skills/{sssf, sssf-sandbox, sssf-sandbox-orchestrator, herdr, sandbox-exe-dev, sssf-admin}` | the six operating skills | you, next session |

## Install

From the target repo root, with this distribution's `.claude/skills/` present
(clone `evolv3ai/sssf-sandbox` and copy its `.claude/skills` in, or install into the clone itself):

```bash
uv run .claude/skills/sssf-sandbox/scripts/install.py          # idempotent; --force overwrites
cp .env.sample .env                                             # set OPENROUTER_PROVISIONING_KEY
git add -A && git commit -m "Install SSSF sandbox"              # the VM clones what is pushed
git push                                                        # the remote must be PUBLIC over https
just sbx manage doctor                                          # preflight, non-billable
```

## `.env` knobs the sandbox reads

| Key | Meaning | Default |
|---|---|---|
| `OPENROUTER_PROVISIONING_KEY` | mints/revokes the capped per-run runtime keys. Host only, never enters a VM | required |
| `SBX_SOURCE_REPO` | public https URL the VM clones | `origin`, git@/ssh:// GitHub forms rewritten to https |
| `SBX_TAG` | exe.dev tag on every VM this repo creates | `sssf-sandbox` |
| `SBX_APP_DIR` | app under development, relative to the clone root; empty = no app, the trace UI is proxied instead | empty |
| `SBX_APP_CMD` | how observe starts it, run inside `SBX_APP_DIR` | `bun run server.ts` |
| `SBX_APP_PORT` | port it binds (must bind 0.0.0.0) | `4501` |

## Then

- Operate one sandbox or fan out N: read `.claude/skills/sssf-sandbox-orchestrator/SKILL.md`.
- Hand a whole build over and get a report back: `/sssf-admin build "<what to build>"`.

## Hard rules

1. `install` and `doctor` never create a VM, mint a key, or call a model API.
2. The provisioning key never leaves the host. Never print, copy, or ssh it.
3. Never run an ADW on the host through this skill. Work happens inside a VM.
4. Teardown is a human decision, never chained after mount or execute.
