# STATE — daily-triage

<!-- This file is auto-managed by the loop runtime. Do not edit manually. -->
<!-- The Verifier agent updates this file after every loop run. -->

## Current Run

```yaml
last_run:                    # ISO 8601 timestamp of the most recent run
status:                      # COMPLETE | BLOCKED | FAILED | RUNNING | IDLE
run_id:                      # Unique run identifier (e.g., daily-triage-2026-06-28)
triggered_by:                # cron | manual | event | chain
```

## Issue Triage Results

```yaml
issues_found:                # Total number of untriaged issues detected at start
issues_triaged:              # Number of issues successfully labeled and assigned
issues_remaining:            # Number of issues still lacking triage metadata
untriageable:                # Issues that couldn't be automatically triaged
  # - issue_number: "reason (e.g. empty description, ambiguous domain)"
```

## Actions Taken

```yaml
labels_applied:              # Count of labels applied in this run
assignees_recommended:       # Count of owner assignments or recommendations made
updates_posted:              # Count of info-request comments posted
```

## Budget

```yaml
cost_usd:                    # Actual dollar cost of this run
tokens_used:                 # Total tokens consumed
iterations_used:             # Number of batches processed
max_iterations:              # Hard limit from LOOP.md (default: 5)
```

## Human Interaction

```yaml
waiting_for_human: false     # true if the loop needs human input to resolve blocks
human_action_needed:         # Description of what the human should do
  # e.g., "Review 2 issues flagged as duplicate or lacking sufficient details"
```

## Scheduling

```yaml
next_run:                    # ISO 8601 timestamp of the next scheduled run
triggered_next:              # Loops or alerts triggered by this run's completion
  # - notify-slack
```

## Run History

```yaml
run_log: .loops/daily-triage/loop-run-log.md
# Full audit trail of every issue evaluated, decision made, and API call executed.
```

## Machine-Readable Sidecar

<!-- state.json is auto-generated alongside this file for use by loop-dashboard -->
<!-- See docs/OBSERVABILITY.md for the state.json schema -->
