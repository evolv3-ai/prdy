---
pipeline: gsd-path/v2
project: prdy
milestone: corpus-integrity
phase: build
                    # inspect only for brownfield; greenfield starts at define
                    # roadmap only in program flow (CHARTER.md exists)
status: blocked
branch: gsd-path/M001
                    # the router rebinds before any next-milestone file change
                    # the bound branch is never main; ship integrates it there
archive: null       # persisted archive transaction path; never recomputed
integration_default: direct # direct | pull-request | external-landing; project setting
integration: direct # current milestone; may override the default before build
integration_source: default # default | milestone; preserves override provenance
default_branch: main # origin default branch; initialization records it once, nothing changes it
---

# Project State

One file, always current. The router reads this first; every phase updates
it on completion. If this file and the artifacts disagree, the artifacts win
— fix this file.

## Log

<!-- append one line per transition: date, phase, event -->
- 2026-11-15 — inspect — project initialized
- 2026-11-15 — inspect — router bound initial milestone
- 2026-11-15 — inspect — inspection artifacts passed
- 2026-11-15 — define — definition started
- 2026-11-15 — define — milestone intent approved
- 2026-11-15 — plan — planning started
- 2026-11-15 — plan — plan approved
- 2026-11-15 — build — build started
- 2026-11-15 — build — wave 1 cycle 1 blocked on SC7; user ruling: "Require a crawl that saves something" and README line 26 "Fix it now"
