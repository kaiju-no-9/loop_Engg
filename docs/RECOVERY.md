# Recovery Strategies

Autonomous loops will eventually encounter states they cannot fix. The `recovery` field in `LOOP.md` dictates how the loop responds to irrecoverable errors.

## The Recovery Field
```yaml
recovery:
  strategy: rollback_last_commit
  max_retries: 2
  escalation: human
```

## Available Strategies

### 1. `rollback_last_commit`
- **Behavior**: Runs `git revert HEAD` to undo the last atomic commit, then retries the loop.
- **Best for**: Code modification loops (`ci-sweeper`, `code-repair`).

### 2. `open_issue`
- **Behavior**: Creates a GitHub issue with the failure context and pauses the loop.
- **Best for**: Non-urgent loops or those lacking write access.

### 3. `notify_slack`
- **Behavior**: Sends a webhook notification with failure details and pauses the loop.
- **Best for**: High-priority or infrastructure-related loops.

### 4. `pause`
- **Behavior**: Sets `status: BLOCKED` and `waiting_for_human: true` in `STATE.md`, then stops.
- **Best for**: Destructive loops or when budget is exhausted.

## Escalation
Regardless of the strategy, if `max_retries` is reached, the loop *always* escalates to a human. The loop will not continue until a human intervenes, reviews the state, and manually clears the block.
