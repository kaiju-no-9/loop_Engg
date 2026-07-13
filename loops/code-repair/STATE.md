# STATE — code-repair

<!-- This file is auto-managed by the loop runtime. Do not edit manually. -->
<!-- The Verifier agent updates this file after every loop run. -->

## Current Run

```yaml
last_run:                    # ISO 8601 timestamp of the most recent run
status:                      # COMPLETE | BLOCKED | FAILED | RUNNING | IDLE
run_id:                      # Unique run identifier (e.g., code-repair-2026-07-10)
triggered_by:                # cron | manual | event | chain
trigger_source:              # CI job URL, commit SHA, or PR number that triggered this run
```

## Repair Results

```yaml
tests_found:                 # Total number of failing tests detected at start
bugs_fixed:                  # Number of distinct source code bugs fixed
tests_fixed:                 # Number of tests that now pass as a result of the fixes
bugs_remaining:              # Number of bugs that could not be auto-fixed
root_causes:                 # Summary of root causes identified
  # - "Missing import of regionConfig after refactor"
  # - "Off-by-one in pagination logic"
unfixable:                   # Bugs flagged as requiring human intervention
  # - bug: "Race condition in WebSocket handler"
  #   reason: "Fix requires architectural change to connection lifecycle"
  # - bug: "Test depends on external API availability"
  #   reason: "External service timeout — not a code bug"
```

## Changes Made

```yaml
files_changed:               # List of source files modified in this run
  # - src/services/order.js
  # - src/utils/pagination.js
tests_modified:              # List of test files modified (only if test was provably wrong)
  # - tests/services/order.test.js
commits_made:                # Number of atomic commits created (one per bug fix)
branch:                      # Branch name (e.g., loop/code-repair/2026-07-10)
pr_url:                      # URL of the opened PR (if merge_strategy: pr)
```

## Budget

```yaml
cost_usd:                    # Actual dollar cost of this run
tokens_used:                 # Total tokens consumed
iterations_used:             # Number of fix-verify cycles completed
max_iterations:              # Hard limit from LOOP.md (default: 15)
```

## Human Interaction

```yaml
waiting_for_human: false     # true if the loop needs human input to continue
human_action_needed:         # Description of what the human should do
  # e.g., "2 bugs require architectural changes beyond minimal diff — review suggested approaches"
needs_human_review:          # Fixes that were applied but flagged for extra review
  # - file: "src/auth/session.js"
  #   reason: "Fix changes exported function signature — verify consumer compatibility"
```

## Scheduling

```yaml
next_run:                    # ISO 8601 timestamp or "event-driven"
triggered_next:              # Loops triggered by this run's completion
  # - notify-slack           (on failure)
```

## Run History

```yaml
run_log: .loops/code-repair/loop-run-log.md
# Full audit trail of every diagnosis, every fix attempt, every test result.
# Read this file when debugging why the loop made a specific source code change.
```

## Machine-Readable Sidecar

<!-- state.json is auto-generated alongside this file for use by loop-dashboard -->
<!-- See docs/OBSERVABILITY.md for the state.json schema -->
