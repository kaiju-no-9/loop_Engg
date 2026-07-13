# STATE — api-consumer-notifier

<!-- This file is auto-managed by the loop runtime. Do not edit manually. -->
<!-- The Verifier agent updates this file after every loop run. -->

## Current Run

```yaml
last_run:                    # ISO 8601 timestamp of the most recent run
status:                      # COMPLETE | BLOCKED | FAILED | RUNNING | IDLE
run_id:                      # Unique run identifier (e.g., api-notify-2026-07-10)
triggered_by:                # cron | manual | event | chain
trigger_source:              # PR number or commit SHA that triggered this run
```

## Change Detection Results

```yaml
spec_version_old:            # Git ref of the previous OpenAPI spec (e.g., HEAD~1)
spec_version_new:            # Git ref of the current OpenAPI spec (e.g., HEAD)
breaking_changes_found:      # Total number of breaking changes detected
non_breaking_changes_found:  # Total number of non-breaking changes (not notified)
breaking_changes:            # Details of each breaking change
  # - endpoint: "GET /api/users/{id}"
  #   change: "field 'email' removed from response"
  #   impact: critical
  # - endpoint: "POST /api/payments"
  #   change: "required field 'currency' added to request body"
  #   impact: serious
```

## Consumer Impact

```yaml
consumers_affected:          # Number of consumer services affected
consumers_details:           # Per-consumer breakdown
  # - service: mobile-app
  #   endpoints_affected: ["GET /api/users/{id}"]
  #   breaking_changes: 2
  # - service: billing-service
  #   endpoints_affected: ["POST /api/payments"]
  #   breaking_changes: 1
untracked_endpoints:         # Endpoints with breaking changes but no registered consumer
  # - "DELETE /api/sessions/{id}"
```

## Notifications Sent

```yaml
notifications_total:         # Total notifications sent across all channels
notifications_sent:          # Per-notification log
  # - consumer: mobile-app
  #   channel: github-issue
  #   status: delivered
  #   issue_url: https://github.com/org/mobile-app/issues/87
  # - consumer: mobile-app
  #   channel: slack
  #   status: delivered
notifications_failed:        # Notifications that failed delivery
  # - consumer: admin-dashboard
  #   channel: slack
  #   status: failed
  #   error: "webhook returned 403"
```

## Budget

```yaml
cost_usd:                    # Actual dollar cost of this run
tokens_used:                 # Total tokens consumed
iterations_used:             # Number of detect-notify cycles completed
max_iterations:              # Hard limit from LOOP.md (default: 5)
```

## Human Interaction

```yaml
waiting_for_human: false     # true if the loop needs human input to resolve blocks
human_action_needed:         # Description of what the human should do
  # e.g., "Consumer registry missing — create consumers.yaml with endpoint-to-service mappings"
```

## Scheduling

```yaml
next_run:                    # ISO 8601 timestamp or "event-driven"
triggered_next:              # Loops triggered by this run's completion
  # - notify-slack           (on failure)
```

## Run History

```yaml
run_log: .loops/api-consumer-notifier/loop-run-log.md
# Full audit trail of every spec diff, every notification sent, and delivery confirmations.
# Read this file when debugging missed or duplicate notifications.
```

## Machine-Readable Sidecar

<!-- state.json is auto-generated alongside this file for use by loop-dashboard -->
<!-- See docs/OBSERVABILITY.md for the state.json schema -->
