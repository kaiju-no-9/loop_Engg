# STATE — accessibility-audit

<!-- This file is auto-managed by the loop runtime. Do not edit manually. -->
<!-- The Verifier agent updates this file after every loop run. -->

## Current Run

```yaml
last_run:                    # ISO 8601 timestamp of the most recent run
status:                      # COMPLETE | BLOCKED | FAILED | RUNNING | IDLE
run_id:                      # Unique run identifier (e.g., a11y-audit-2026-07-06)
triggered_by:                # cron | manual | event | chain
```

## Audit Results

```yaml
pages_scanned:               # Number of pages/components scanned by axe-core
violations_found:            # Total violations detected at start of run
violations_fixed:            # Number of violations resolved by this run
violations_remaining:        # Number of violations still present after this run
  # - rule_id: "reason it can't be auto-fixed"
  # - color-contrast: "requires design system color palette change"
  # - aria-required-children: "third-party carousel component"
violations_by_impact:
  critical:                  # Count of critical-impact violations found
  serious:                   # Count of serious-impact violations found
  moderate:                  # Count of moderate-impact violations found
  minor:                     # Count of minor-impact violations found
```

## Changes Made

```yaml
files_changed:               # List of files modified in this run
  # - src/components/HeroBanner.jsx
  # - styles/typography.css
commits_made:                # Number of atomic commits created (one per violation rule)
branch:                      # Branch name (e.g., loop/accessibility-audit/2026-07-06)
pr_url:                      # URL of the opened PR (if merge_strategy: pr)
```

## Budget

```yaml
cost_usd:                    # Actual dollar cost of this run
tokens_used:                 # Total tokens consumed
iterations_used:             # Number of scan-fix cycles completed
max_iterations:              # Hard limit from LOOP.md (default: 12)
```

## Human Interaction

```yaml
waiting_for_human: false     # true if the loop needs human input to resolve blocks
human_action_needed:         # Description of what the human should do
  # e.g., "3 color-contrast violations require design system palette changes — review suggested colors"
```

## Scheduling

```yaml
next_run:                    # ISO 8601 timestamp of the next scheduled run
triggered_next:              # Loops triggered by this run's completion
  # - notify-slack           (on failure)
```

## Run History

```yaml
run_log: .loops/accessibility-audit/loop-run-log.md
# Full audit trail of every scan, every violation, every fix applied.
# Read this file when debugging why the loop made a specific change.
```

## Machine-Readable Sidecar

<!-- state.json is auto-generated alongside this file for use by loop-dashboard -->
<!-- See docs/OBSERVABILITY.md for the state.json schema -->
