# Loop Budget Guide

> Every loop must have a budget. A loop without a budget is a loop that will eventually bankrupt your API account.

---

## Why Budgets Matter

Autonomous loops run without human supervision. A single misstep — an infinite retry, a verbose model, a chained trigger — can consume thousands of dollars in tokens before anyone notices. Budget caps are your circuit breaker.

---

## Budget Fields in LOOP.md

Every loop must define these in its LOOP.md:

```yaml
budget:
  max_tokens: 50000        # Per-run token cap (input + output combined)
  max_cost_usd: 2.00       # Per-run dollar cap — hard stop, never exceeded
```

### What Happens When Budget Is Exhausted

1. The loop **stops immediately** — mid-iteration if necessary
2. `status` in STATE.md is set to `BLOCKED`
3. `budget_exhausted` termination condition fires
4. Any pending changes are committed (atomic commit principle)
5. If `triggers.on_failure` is defined, it fires (e.g., `notify-slack`)

---

## Recommended Budget Caps by Loop Complexity

| Complexity | Token Cap | Dollar Cap | Example Loops |
|-----------|-----------|------------|---------------|
| **Light** | 10,000–20,000 | $0.25–$0.75 | changelog-drafter, stale-branch-janitor, daily-triage |
| **Medium** | 30,000–50,000 | $1.00–$2.00 | ci-sweeper, doc-sync, dependency-updater |
| **Heavy** | 50,000–100,000 | $2.00–$5.00 | code-repair, test-coverage-grower, migration-writer |
| **Intensive** | 100,000–200,000 | $5.00–$10.00 | accessibility-audit (full site), security-scan (large codebase) |

> **Rule of thumb:** Start low. You can always increase the budget after reviewing a few runs. You can never un-spend tokens.

---

## Cost Per Model

Token pricing varies dramatically by model. Choose the cheapest model that can do the job.

| Model | Input (per 1M tokens) | Output (per 1M tokens) | Best For |
|-------|----------------------|------------------------|----------|
| Claude 3.5 Haiku | $0.25 | $1.25 | Verification, triage, simple fixes |
| GPT-4o-mini | $0.15 | $0.60 | Lightweight loops, classification |
| Gemini 1.5 Pro | $1.25 | $5.00 | Medium complexity, good balance |
| Claude 3.5 Sonnet | $3.00 | $15.00 | Standard loops, code generation |
| GPT-4o | $2.50 | $10.00 | Standard loops, broad capability |
| Claude 3 Opus | $15.00 | $75.00 | Complex planning, architecture |
| GPT-4 | $30.00 | $60.00 | Legacy — avoid for loops |

---

## Cadence Multipliers

Budget is **per run**, but cost accumulates by cadence:

| Cadence | Runs/Month | $2/run = $/month |
|---------|-----------|-------------------|
| Hourly | ~720 | $1,440 |
| Every 6 hours | ~120 | $240 |
| Daily | ~30 | $60 |
| Nightly | ~30 | $60 |
| Weekly | ~4 | $8 |
| On PR | ~20 (estimate) | $40 |
| On release | ~2–4 | $4–$8 |

> **Warning:** A nightly loop at $2/run is $60/month. Three nightly loops is $180/month. Five is $300/month. Monitor with `loop-dashboard`.

---

## Chained Loop Budgets

When loops trigger other loops via the `triggers` field, costs multiply:

```
ci-sweeper ($2) → changelog-drafter ($0.50) → notify-slack ($0.05)
Total per trigger: $2.55
Nightly: $76.50/month
```

### Rules for chained budgets

1. **Budget is per-loop, not per-chain.** Each loop in the chain has its own `max_cost_usd`.
2. **Failure doesn't cascade by default.** If loop B fails, loop C does not run.
3. **Always calculate the full chain cost** before scheduling.
4. **Use `loop-cost`** to estimate before enabling chains:

```bash
npx loop-cost --pattern ci-sweeper --cadence nightly
```

---

## Budget Optimization Strategies

### 1. Use the right model tier

| Agent Role | Recommended Tier | Why |
|-----------|-----------------|-----|
| Planner | Standard (Sonnet/GPT-4o) | Needs reasoning for good plans |
| Worker | Standard or Lightweight | Execution is more mechanical |
| Verifier | Lightweight (Haiku/GPT-4o-mini) | Just checking pass/fail |

### 2. Minimize iteration count

- Write a clear, testable `objective` in LOOP.md — vague goals = more iterations
- Set `max_iterations` conservatively (5–10)
- Enable `no_progress_detected` to stop spinning

### 3. Scope files tightly

- Smaller `file_scope.allow` = fewer files read = fewer tokens
- Always set `file_scope.deny` for large directories (node_modules, dist, vendor)

### 4. Use report-only mode first

- Week 1–3 of the trust ramp: the loop plans but doesn't merge
- This catches budget surprises before they compound

### 5. Monitor with loop-dashboard

```bash
npx loop-dashboard .
```

Review weekly:
- Which loop costs the most?
- Is any loop's cost trending up?
- Are iterations-per-run increasing? (sign of degradation)

---

## Emergency: What If a Loop Overspends?

1. **It won't** — `max_cost_usd` is a hard stop enforced by the runner
2. If the runner fails to enforce (bug), the model provider's spending limits are your second line of defense
3. Set spending limits on your API account:
   - **Anthropic:** Usage limits in Console → Settings
   - **OpenAI:** Usage limits in Platform → Settings → Limits
   - **Google:** Budget alerts in Cloud Console

---

## Quick Reference

```yaml
# Minimum viable budget config in LOOP.md
budget:
  max_tokens: 50000
  max_cost_usd: 2.00

# Conservative budget for new loops
budget:
  max_tokens: 20000
  max_cost_usd: 0.50

# Heavy workload budget
budget:
  max_tokens: 100000
  max_cost_usd: 5.00
```

> **Golden rule:** If you don't know the right budget, start at `max_cost_usd: 0.50` and increase after 3 successful runs.
