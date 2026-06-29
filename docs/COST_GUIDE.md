# Loop Cost Guide

Running autonomous loops involves API costs. This guide helps you estimate and control those costs.

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

## Estimated Cost per Loop Type (Using Sonnet)
- **Simple (e.g., triage)**: $0.10 - $0.30 per run
- **Medium (e.g., ci-sweeper)**: $0.50 - $1.50 per run
- **Complex (e.g., migration-writer)**: $2.00 - $5.00 per run

## Monthly Cost Projections
Assuming a Medium loop ($1.00/run):
- **Hourly**: ~$720/month
- **Nightly/Daily**: ~$30/month
- **Weekly**: ~$4/month

## Cost Optimization Tips
1. **Reduce Iterations**: Write clearer objectives to reduce the number of cycles.
2. **Tighten Scope**: Limit `file_scope` so the agent reads fewer files per run.
3. **Use Cheaper Models**: Downgrade the verifier to a lightweight model.

## Estimating Cost via CLI
Use the `loop-cost` tool to estimate expenses before activating a loop:
```bash
npx loop-cost --pattern ci-sweeper --cadence nightly --model claude-sonnet
```
