# Loop Observability

When you have 5+ loops running autonomously, you need an aggregate view of their behavior, cost, and health.

## The `state.json` Sidecar
Every loop run generates a `state.json` file alongside `STATE.md`. This is a machine-readable record of the run.

### Schema
```json
{
  "loop": "ci-sweeper",
  "run_id": "2026-06-28-0214",
  "status": "COMPLETE",
  "tests_fixed": 4,
  "files_changed": ["src/auth.js"],
  "commits": 2,
  "cost_usd": 0.43,
  "tokens_used": 12400,
  "duration_seconds": 87,
  "triggered_by": "cron",
  "triggered_next": ["changelog-drafter"],
  "waiting_for_human": false
}
```

## Using the Dashboard
The `loop-dashboard` CLI aggregates all `state.json` files to give you a unified view.
```bash
npx loop-dashboard .
```
It shows:
- Total cost across all loops.
- Loops waiting for human intervention.
- Commit frequency and token usage.

## Key Metrics to Monitor
- **Cost Anomalies**: Sudden spikes in `cost_usd`.
- **Iteration Bloat**: Increasing loop durations or token usage indicating degraded performance.
- **Success Rate**: The ratio of `COMPLETE` to `FAILED` or `BLOCKED` runs.

## External Integrations
Because `state.json` is simple JSON, you can easily ingest it into Datadog, Grafana, or ELK stacks using standard log forwarders or custom scripts.
