# Failure Modes and Mitigations

When running autonomous loops, things will occasionally go wrong. This guide covers common failure patterns and how to prevent them.

## 1. Infinite Loops
- **Description**: The loop never hits a termination condition and keeps iterating.
- **Symptoms**: `max_iterations` is hit frequently; high cost per run; repetitive commits.
- **Mitigation**: The runner will kill the loop at `max_iterations` or when the budget is exhausted.
- **Prevention**: Write a clear, testable `objective`. Ensure `verifier` is robust.

## 2. Scope Creep
- **Description**: The agent modifies files unrelated to its objective.
- **Symptoms**: Unexpected files appear in `files_changed` in `STATE.md`.
- **Mitigation**: Revert the atomic commits and pause the loop.
- **Prevention**: Define tight `file_scope.allow` and `file_scope.deny` patterns. Do not give the loop tools it doesn't need.

## 3. Budget Blowout
- **Description**: A loop consumes excessive tokens or dollars.
- **Symptoms**: Surprise API bills; budget exhaustion termination condition fires early.
- **Mitigation**: The runner strictly enforces `max_cost_usd`.
- **Prevention**: Set a low `max_cost_usd`. Be careful with chained loops which multiply cost.

## 4. Silent Failures
- **Description**: The loop fails but nobody knows.
- **Symptoms**: Tests remain broken; `state.json` shows FAILED but no notification is sent.
- **Mitigation**: Check `loop-dashboard` regularly.
- **Prevention**: Define a `recovery` strategy with `escalation: human`. Use `triggers.on_failure` to send Slack alerts.

## 5. Drift
- **Description**: The loop's actual behavior diverges from `LOOP.md` over time.
- **Symptoms**: Commits are technically correct but structurally messy.
- **Mitigation**: Audit the `loop-run-log.md` and refine `SKILL.md`.
- **Prevention**: Use the 4-week Trust Ramp to monitor output closely.

## 6. Circular Chains
- **Description**: Loop A triggers Loop B, which triggers Loop A (A → B → A).
- **Symptoms**: Loops run continuously; budgets exhaust rapidly.
- **Mitigation**: Stop the orchestrator; clear the trigger queues.
- **Prevention**: `loop-audit` detects circular chains. Design linear or DAG composition.

## 7. Self-Grading Worker
- **Description**: The worker who wrote the code is evaluating if it's correct.
- **Symptoms**: Loop reports success but objective is not met.
- **Mitigation**: Reset state and require manual approval.
- **Prevention**: Always use a separate `verifier` (a fresh model instance) to evaluate success.
