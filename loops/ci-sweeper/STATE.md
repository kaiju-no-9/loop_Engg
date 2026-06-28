# STATE — ci-sweeper

<!-- This file is auto-managed by the loop runtime. Do not edit manually. -->
<!-- The Verifier agent updates this file after every loop run. -->

## Current Run

```yaml
last_run:                    # ISO 8601 timestamp of the most recent run
status:                      # COMPLETE | BLOCKED | FAILED | RUNNING | IDLE
run_id:                      # Unique run identifier (date-based: 2026-06-28-0214)
triggered_by:                # cron | manual | event | chain
```

## Test Results

```yaml
tests_found:                 # Total number of failing tests detected at start
tests_fixed:                 # Number of tests this run successfully fixed
tests_remaining:             # Number of tests still failing after this run
unfixable:                   # Tests flagged as requiring human intervention
  # - test_name: "reason it can't be auto-fixed"
```

## Changes Made

```yaml
files_changed:               # List of files modified in this run
  # - src/auth.test.js
  # - src/utils.test.js
commits_made:                # Number of atomic commits created
branch:                      # Branch name (e.g., loop/ci-sweeper/2026-06-28)
pr_url:                      # URL of the opened PR (if merge_strategy: pr)
```

## Budget

```yaml
cost_usd:                    # Actual dollar cost of this run
tokens_used:                 # Total tokens consumed
iterations_used:             # Number of fix-verify cycles completed
max_iterations:              # Hard limit from LOOP.md (default: 10)
```

## Human Interaction

```yaml
waiting_for_human: false     # true if the loop needs human input to continue
human_action_needed:         # Description of what the human should do
  # e.g., "3 tests require dependency updates — review and install manually"
```

## Scheduling

```yaml
next_run:                    # ISO 8601 timestamp of the next scheduled run
triggered_next:              # Loops triggered by this run's completion
  # - changelog-drafter      (on success)
  # - notify-slack           (on failure)
```

## Run History

```yaml
run_log: .loops/ci-sweeper/loop-run-log.md
# Full audit trail of every run, every decision, every commit.
# Read this file when debugging why the loop made a specific change.
```

## Machine-Readable Sidecar

<!-- state.json is auto-generated alongside this file for use by loop-dashboard -->
<!-- See docs/OBSERVABILITY.md for the state.json schema -->
