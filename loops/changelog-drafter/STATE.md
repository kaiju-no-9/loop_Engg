# STATE — changelog-drafter

<!-- This file is auto-managed by the loop runtime. Do not edit manually. -->
<!-- The Verifier agent updates this file after every loop run. -->

## Current Run

```yaml
last_run:                    # ISO 8601 timestamp of the most recent run
status:                      # COMPLETE | BLOCKED | FAILED | RUNNING | IDLE
run_id:                      # Unique run identifier (e.g., changelog-drafter-2026-06-28)
triggered_by:                # cron | manual | event | chain
```

## Draft Results

```yaml
commits_analyzed:            # Total number of commits scanned
prs_analyzed:                # Total number of pull requests scanned
version_tag:                 # Target version tag processed (e.g., v1.1.0)
changelog_drafted: false     # true if updates were compiled and written
```

## Changes Made

```yaml
files_changed:               # List of files modified in this run
  # - CHANGELOG.md
commits_made:                # Number of atomic commits created
branch:                      # Branch name (e.g., loop/changelog-drafter/2026-06-28)
pr_url:                      # URL of the opened PR (if merge_strategy: pr)
```

## Budget

```yaml
cost_usd:                    # Actual dollar cost of this run
tokens_used:                 # Total tokens consumed
iterations_used:             # Number of draft cycles completed
max_iterations:              # Hard limit from LOOP.md (default: 3)
```

## Human Interaction

```yaml
waiting_for_human: false     # true if the loop needs human input to resolve blocks
human_action_needed:         # Description of what the human should do
  # e.g., "No tags detected; tag the repository or specify range in config manually"
```

## Scheduling

```yaml
next_run:                    # ISO 8601 timestamp of the next scheduled run
triggered_next:              # Loops triggered by this run's completion
  # - notify-slack
```

## Run History

```yaml
run_log: .loops/changelog-drafter/loop-run-log.md
# Full audit trail of tags analyzed, commits parsed, draft categories mapped, and files written.
```

## Machine-Readable Sidecar

<!-- state.json is auto-generated alongside this file for use by loop-dashboard -->
<!-- See docs/OBSERVABILITY.md for the state.json schema -->
