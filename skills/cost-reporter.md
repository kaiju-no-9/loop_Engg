---
name: cost-reporter
description: >
  Queries state files for cost, aggregates spending, and flags anomalies. Trigger on "how much did this cost", "generate cost report", or "check budget". Do NOT use for modifying files.
---

# Cost Reporter

This skill enables the agent to act as a financial observer, parsing `state.json` files to aggregate token usage and dollar costs across various loops and timeframes.

---

## When to Use This Skill

Use this skill when:
- The `cost-anomaly-detector` loop runs to audit spending.
- A human asks for a summary of API costs.
- You need to verify if a loop is nearing its budget limit.

Do NOT use this skill for:
- Running actual loops.
- Modifying `LOOP.md` budgets (unless explicitly requested).

---

## Workflow: Generate Cost Report

1. **Locate state files**: Find all `state.json` files in `.loops/*/`.
2. **Extract metrics**: Read the `cost_usd` and `tokens_used` fields from each file.
3. **Aggregate data**: Sum the costs by loop name, by day, or by week.
4. **Identify anomalies**: Flag any loop where the recent run cost is >2x its historical average.
5. **Format report**: Output a markdown table summarizing the findings.

---

## Decision Rules

- If a `state.json` file is missing or corrupted → skip it and note the error in the report.
- If total daily cost exceeds $10 (or a predefined threshold) → flag the report as WARNING.

---

## Example

**Input:** "Give me a cost breakdown for all loops."

**Steps the agent takes:**
1. Reads `.loops/ci-sweeper/state.json` ($0.43).
2. Reads `.loops/daily-triage/state.json` ($0.12).
3. Sums the totals and formats the output.

**Output:**
```markdown
## Loop Cost Report

| Loop | Tokens Used | Cost (USD) | Status |
|------|-------------|------------|--------|
| `ci-sweeper` | 12,400 | $0.43 | Normal |
| `daily-triage` | 3,100 | $0.12 | Normal |
| **Total** | **15,500** | **$0.55** | |
```

---

## Guardrails

- This is a READ-ONLY skill. Do not write or modify any `state.json` files.
- Always display costs in USD formatted to two decimal places.
