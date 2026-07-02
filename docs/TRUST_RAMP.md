# Trust Ramp: The 4-Week Protocol

Do not let an autonomous loop commit directly to main on day one. Build trust progressively using this 4-week protocol.

## Week 1: Dry-Run Only
**Goal:** Verify the Planner understands the objective.
- **Action:** Run the loop manually with the `--dry-run` flag.
  ```bash
  claude /loop ci-sweeper --dry-run
  ```
- **What to check:** Read the proposed plan. Does it identify the right files? Are the steps logical?
- **Outcome:** The loop makes zero changes. Refine `LOOP.md` if the plan is poor.

## Week 2: Manual One-Shot
**Goal:** Verify the Worker can execute the plan successfully.
- **Action:** Run the loop manually, without scheduling.
  ```bash
  claude /loop ci-sweeper
  ```
- **What to check:** Did the tests pass? Was the code quality acceptable? Did the Verifier correctly evaluate success?
- **Outcome:** The loop executes, and you manually review the atomic commits.

## Week 3: Scheduled, Report-Only
**Goal:** Verify the loop runs reliably on its cadence without breaking things.
- **Action:** Schedule the loop (e.g., via cron/Actions), but configure `merge_strategy: pr`.
- **What to check:** Every morning, check the open PRs. Are the PRs well-formed? Is the loop staying within budget?
- **Outcome:** The loop runs autonomously but requires a human to click "Merge".

## Week 4: Fully Autonomous
**Goal:** The loop operates entirely on its own within defined guardrails.
- **Action:** Set `merge_strategy: auto` (or remove PR requirements for safe operations).
- **What to check:** Review `STATE.md` and use `loop-wizard dashboard .` weekly. Check for cost anomalies or increased iteration counts.
- **Outcome:** The loop fixes issues while you sleep.

## When to Pause and Reassess
If a loop fails in Week 3 or 4:
1. Revert its last commit (or use the `recovery` strategy).
2. Set `status: BLOCKED` in `STATE.md`.
3. Drop back to Week 1 (`--dry-run`) to debug the failure.
