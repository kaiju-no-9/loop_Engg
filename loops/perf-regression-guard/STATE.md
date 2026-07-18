# STATE — perf-regression-guard

<!-- This file is auto-managed by the loop runtime. Do not edit manually. -->
<!-- The Verifier agent updates this file after every loop run. -->

## Current Run

```yaml
last_run:                    # ISO 8601 timestamp of the most recent run
status:                      # COMPLETE | BLOCKED | FAILED | RUNNING | IDLE
run_id:                      # Unique run identifier (e.g., perf-guard-2026-07-06)
triggered_by:                # cron | manual | event | chain
```

## Performance Results

```yaml
scanned_routes:              # List of routes/endpoints audited
  # - /home
  # - /api/v1/products
baseline_established:        # true | false
regressions_detected:        # List of regression details
  # - metric: "LCP"
  #   route: "/home"
  #   delta: "+1.1s"
  #   threshold: "+0.5s"
metrics_by_route:
  # /home:
  #   lighthouse_score: 85
  #   lcp_ms: 2500
  #   tbt_ms: 150
```

## Changes Made

```yaml
files_changed:               # List of files modified in this run (e.g., config optimizations)
commits_made:                # Number of atomic commits created
branch:                      # PR branch name (e.g., loop/perf-regression-guard/pr-12)
pr_url:                      # URL of the pull request
comment_posted:              # true | false (if PR comment was added)
```

## Budget

```yaml
cost_usd:                    # Actual dollar cost of this run
tokens_used:                 # Total tokens consumed
iterations_used:             # Number of audit-report cycles completed
max_iterations:              # Hard limit from LOOP.md (default: 5)
```

## Human Interaction

```yaml
waiting_for_human: false     # true if the loop needs human input to resolve performance regressions
human_action_needed:         # Description of what the human should do
  # e.g., "p95 latency exceeded by 200% on /api/v1/products — optimize DB queries manually"
```

## Scheduling

```yaml
next_run:                    # ISO 8601 timestamp of the next scheduled run (if applicable)
triggered_next:              # Loops triggered by this run's completion
  # - notify-slack           (on failure)
```

## Run History

```yaml
run_log: .loops/perf-regression-guard/loop-run-log.md
# Full audit trail of every performance audit, comparison, and PR posting.
```

## Machine-Readable Sidecar

<!-- state.json is auto-generated alongside this file for use by loop-dashboard -->
<!-- See docs/OBSERVABILITY.md for the state.json schema -->
