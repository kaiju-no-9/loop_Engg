# STATE — migration-writer

<!-- This file is auto-managed by the loop runtime. Do not edit manually. -->
<!-- The Verifier agent updates this file after every loop run. -->

## Current Run

```yaml
last_run:                    # ISO 8601 timestamp of the most recent run
status:                      # COMPLETE | BLOCKED | FAILED | RUNNING | IDLE
run_id:                      # Unique run identifier (e.g., db-migrate-2026-07-06)
triggered_by:                # cron | manual | event | chain
```

## Schema Changes

```yaml
detected_drift:              # true | false (if models differed from database)
destructive_changes:         # List of any destructive changes flagged
  # - table: "User"
  #   action: "DROP COLUMN password"
generated_migrations:        # List of migration files created in this run
  # - prisma/migrations/20260718143000_add_phone_to_user/migration.sql
validation_status:           # PASSED | FAILED
```

## Changes Made

```yaml
files_changed:               # List of files modified in this run
  # - prisma/schema.prisma
  # - prisma/migrations/...
commits_made:                # Number of atomic commits created (usually 1)
branch:                      # Feature branch name (e.g., loop/migration-writer/add-phone)
pr_url:                      # URL of the pull request
```

## Budget

```yaml
cost_usd:                    # Actual dollar cost of this run
tokens_used:                 # Total tokens consumed
iterations_used:             # Number of generate-verify cycles completed
max_iterations:              # Hard limit from LOOP.md (default: 8)
```

## Human Interaction

```yaml
waiting_for_human: false     # true if the loop needs human input to resolve destructive migrations
human_action_needed:         # Description of what the human should do
  # e.g., "Destructive migration detected (dropping table 'Session'). Review and confirm."
```

## Scheduling

```yaml
next_run:                    # ISO 8601 timestamp of the next scheduled run
triggered_next:              # Loops triggered by this run's completion
  # - notify-slack           (on failure)
```

## Run History

```yaml
run_log: .loops/migration-writer/loop-run-log.md
# Full audit trail of every schema scan, CLI generation output, and validation.
```

## Machine-Readable Sidecar

<!-- state.json is auto-generated alongside this file for use by loop-dashboard -->
<!-- See docs/OBSERVABILITY.md for the state.json schema -->
