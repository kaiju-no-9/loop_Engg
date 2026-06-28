# STATE — dependency-updater

<!-- This file is auto-managed by the loop runtime. Do not edit manually. -->
<!-- The Verifier agent updates this file after every loop run. -->

## Current Run

```yaml
last_run:                    # ISO 8601 timestamp of the most recent run
status:                      # COMPLETE | BLOCKED | FAILED | RUNNING | IDLE
run_id:                      # Unique run identifier (e.g., dep-updater-2026-06-28)
triggered_by:                # cron | manual | event | chain
```

## Update Results

```yaml
packages_scanned:            # Total number of outdated packages detected
packages_updated:            # List of packages successfully updated with versions
  # - lodash: "4.17.20 -> 4.17.21"
packages_failed:             # List of packages that failed tests during updates
  # - pg: "8.5.1 -> 8.6.0 (tests failed: query timeout)"
packages_skipped:            # List of packages skipped due to major updates or rules
  # - webpack: "4.44.2 -> 5.0.0 (skipped major update)"
```

## Changes Made

```yaml
files_changed:               # List of dependency manifest files modified
  # - package.json
  # - package-lock.json
commits_made:                # Number of atomic commits created (one per package)
branch:                      # Branch name (e.g., loop/dependency-updater/2026-06-28)
pr_url:                      # URL of the opened PR (if merge_strategy: pr)
```

## Budget

```yaml
cost_usd:                    # Actual dollar cost of this run
tokens_used:                 # Total tokens consumed
iterations_used:             # Number of updates attempted
max_iterations:              # Hard limit from LOOP.md (default: 15)
```

## Human Interaction

```yaml
waiting_for_human: false     # true if the loop needs human input to resolve blocks
human_action_needed:         # Description of what the human should do
  # e.g., "webpack package failed tests when upgraded to 5.0.0; review build error logs"
```

## Scheduling

```yaml
next_run:                    # ISO 8601 timestamp of the next scheduled run
triggered_next:              # Loops triggered by this run's completion
  # - notify-slack
```

## Run History

```yaml
run_log: .loops/dependency-updater/loop-run-log.md
# Full audit trail of package checks, test output, package installs, and rollback logs.
```

## Machine-Readable Sidecar

<!-- state.json is auto-generated alongside this file for use by loop-dashboard -->
<!-- See docs/OBSERVABILITY.md for the state.json schema -->
