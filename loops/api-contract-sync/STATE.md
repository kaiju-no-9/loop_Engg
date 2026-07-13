# STATE — api-contract-sync

<!-- This file is auto-managed by the loop runtime. Do not edit manually. -->
<!-- The Verifier agent updates this file after every loop run. -->

## Current Run

```yaml
last_run:                    # ISO 8601 timestamp of the most recent run
status:                      # COMPLETE | BLOCKED | FAILED | RUNNING | IDLE
run_id:                      # Unique run identifier (e.g., api-sync-2026-07-10)
triggered_by:                # cron | manual | event | chain
trigger_source:              # File path or commit SHA that triggered this run
```

## Sync Results

```yaml
route_files_scanned:         # Number of route handler files parsed
endpoints_extracted:         # Total endpoints found in route handlers
endpoints_in_spec:           # Total endpoints currently in the OpenAPI spec
endpoints_added:             # New endpoints added to the spec
  # - "GET /api/orders"
  # - "GET /api/orders/{id}"
endpoints_modified:          # Existing endpoints updated in the spec
  # - "POST /api/users — added 'phone' field to request body"
endpoints_potentially_removed:  # Spec entries with no matching route handler (flagged for review)
  # - "DELETE /api/legacy/sessions — route handler not found"
endpoints_unparseable:       # Routes that couldn't be parsed (dynamic registration, metaprogramming)
  # - "src/routes/dynamic.js — uses programmatic route registration"
spec_lint_errors:            # Number of Redocly/Spectral lint errors after update
spec_lint_warnings:          # Number of lint warnings after update
```

## Changes Made

```yaml
files_changed:               # List of files modified in this run
  # - openapi.yaml
commits_made:                # Number of atomic commits created
branch:                      # Branch name (e.g., loop/api-contract-sync/2026-07-10)
pr_url:                      # URL of the opened PR (if merge_strategy: pr)
```

## Budget

```yaml
cost_usd:                    # Actual dollar cost of this run
tokens_used:                 # Total tokens consumed
iterations_used:             # Number of sync-validate cycles completed
max_iterations:              # Hard limit from LOOP.md (default: 8)
```

## Human Interaction

```yaml
waiting_for_human: false     # true if the loop needs human input to resolve blocks
human_action_needed:         # Description of what the human should do
  # e.g., "3 endpoints in spec have no matching route handler — confirm if removed or moved"
```

## Scheduling

```yaml
next_run:                    # ISO 8601 timestamp or "event-driven"
triggered_next:              # Loops triggered by this run's completion
  # - api-consumer-notifier  (on success)
  # - notify-slack           (on failure)
```

## Run History

```yaml
run_log: .loops/api-contract-sync/loop-run-log.md
# Full audit trail of every route scan, spec diff, and validation result.
# Read this file when debugging why the loop added or modified a spec entry.
```

## Machine-Readable Sidecar

<!-- state.json is auto-generated alongside this file for use by loop-dashboard -->
<!-- See docs/OBSERVABILITY.md for the state.json schema -->
