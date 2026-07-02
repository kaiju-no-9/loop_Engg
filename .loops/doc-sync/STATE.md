# STATE — doc-sync

<!-- This file is auto-managed by the loop runtime. Do not edit manually. -->
<!-- The Verifier agent updates this file after every loop run. -->

## Current Run

```yaml
last_run:                    # ISO 8601 timestamp of the most recent run
status:                      # COMPLETE | BLOCKED | FAILED | RUNNING | IDLE
run_id:                      # Unique run identifier (date-based)
triggered_by:                # cron | manual | event | chain
```

## Test Results

```yaml
tests_found:                 # Total number of failing tests detected at start
tests_fixed:                 # Number of tests this run successfully fixed
tests_remaining:             # Number of tests still failing after this run
```

## Changes Made

```yaml
files_changed:               # List of files modified in this run
commits_made:                # Number of atomic commits created
branch:                      # Branch name
pr_url:                      # URL of the opened PR (if merge_strategy: pr)
```

## Budget

```yaml
cost_usd:                    # Actual dollar cost of this run
tokens_used:                 # Total tokens consumed
iterations_used:             # Number of fix-verify cycles completed
```

## Human Interaction

```yaml
waiting_for_human: false     # true if the loop needs human input to continue
human_action_needed:         # Description of what the human should do
```

## Scheduling

```yaml
next_run:                    # ISO 8601 timestamp of the next scheduled run
triggered_next:              # Loops triggered by this run's completion
```

## Run History

```yaml
run_log: .loops/doc-sync/loop-run-log.md
```

## Machine-Readable Sidecar

<!-- state.json is auto-generated alongside this file for use by loop-dashboard -->
