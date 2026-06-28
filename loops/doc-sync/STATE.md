# STATE — doc-sync

<!-- This file is auto-managed by the loop runtime. Do not edit manually. -->
<!-- The Verifier agent updates this file after every loop run. -->

## Current Run

```yaml
last_run:                    # ISO 8601 timestamp of the most recent run
status:                      # COMPLETE | BLOCKED | FAILED | RUNNING | IDLE
run_id:                      # Unique run identifier (e.g., doc-sync-2026-06-28)
triggered_by:                # cron | manual | event | chain
```

## Sync Results

```yaml
files_analyzed:              # Total number of code files scanned for diffs
docs_updated:                # Number of documentation files successfully modified
docs_created:                # Number of new documentation files created
links_verified:              # Count of markdown links verified
```

## Changes Made

```yaml
files_changed:               # List of markdown files modified in this run
  # - docs/auth.md
  # - README.md
commits_made:                # Number of atomic commits created
branch:                      # Branch name (e.g., loop/doc-sync/2026-06-28)
pr_url:                      # URL of the opened PR (if merge_strategy: pr)
```

## Budget

```yaml
cost_usd:                    # Actual dollar cost of this run
tokens_used:                 # Total tokens consumed
iterations_used:             # Number of cycles completed
max_iterations:              # Hard limit from LOOP.md (default: 5)
```

## Human Interaction

```yaml
waiting_for_human: false     # true if the loop needs human input to resolve blocks
human_action_needed:         # Description of what the human should do
  # e.g., "API in payment.js was removed; review whether docs/billing.md should be fully deleted"
```

## Scheduling

```yaml
next_run:                    # ISO 8601 timestamp of the next scheduled run
triggered_next:              # Loops triggered by this run's completion
  # - changelog-drafter
```

## Run History

```yaml
run_log: .loops/doc-sync/loop-run-log.md
# Full audit trail of code diffs analyzed, markdown sections modified, and validation logs.
```

## Machine-Readable Sidecar

<!-- state.json is auto-generated alongside this file for use by loop-dashboard -->
<!-- See docs/OBSERVABILITY.md for the state.json schema -->
