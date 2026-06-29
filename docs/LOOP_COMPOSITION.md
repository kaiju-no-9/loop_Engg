# Loop Composition

Loops can trigger other loops or skills, allowing you to build complex autonomous pipelines. This is managed via the `triggers` field in `LOOP.md`.

## The Triggers Field
```yaml
triggers:
  on_success:
    - changelog-drafter      # Chain loops: runs next if this loop succeeds
  on_failure:
    - notify-slack           # Skills can be triggered too
```

## Composition Rules
1. **No circular chains**: A → B → A is prohibited. `loop-audit` will reject this configuration.
2. **Budget is per-loop**: If `ci-sweeper` has a $2 budget and triggers `changelog-drafter` with a $1 budget, the total chain cost is up to $3. Budgets do *not* pool.
3. **Failure Isolation**: If Loop A fails, Loop B (triggered by A) does not run, unless you explicitly set `cascade_failure: true`.
4. **Triggers are optional**: A loop with no triggers simply stops when complete.

## Safe Patterns

### 1. Linear Chain
A straight sequence where each step depends on the previous.
`ci-sweeper` → `changelog-drafter` → `deployment-trigger`

### 2. Fan-out
One loop's success triggers multiple independent loops.
`dependency-updater` → [ `perf-regression-guard`, `security-scan` ]

### 3. Conditional
Triggers fire based on success or failure of the verifier.
`api-contract-sync` (success) → `api-consumer-notifier`
`api-contract-sync` (failure) → `notify-slack`

## Anti-Patterns

- **Circular Chains**: Will quickly exhaust budgets.
- **Cascading Failure**: Running downstream loops when upstream failed usually results in garbage output.
- **Shared State Mutation**: Two loops running concurrently and trying to edit the same files will cause conflict. Use `file_scope` to isolate them.

## Detecting Cycles
Run `npx loop-audit .` to automatically detect circular dependencies in your triggers.
