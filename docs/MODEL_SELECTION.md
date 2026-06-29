# Model Selection Guide

Choosing the right model for your loop is a balance of capability, speed, and cost. A well-engineered loop often uses different models for different roles.

## Model Tiers

### 1. Flagship (Claude 3 Opus, GPT-4o)
- **Cost**: High
- **Speed**: Slow to Medium
- **Use for**: Complex reasoning, architecture design, planning complex changes.

### 2. Standard (Claude 3.5 Sonnet, Gemini 1.5 Pro)
- **Cost**: Medium
- **Speed**: Fast
- **Use for**: Most general tasks, code generation, standard bug fixes.

### 3. Lightweight (Claude 3.5 Haiku, GPT-4o-mini)
- **Cost**: Low
- **Speed**: Very Fast
- **Use for**: Verification, simple triage, classification, checking if tests passed.

## Loop Complexity Matrix

| Loop Type | Recommended Model | Example |
|-----------|-------------------|---------|
| Triage / Labeling | Lightweight | `daily-triage` |
| Routine Code Fixes | Standard | `ci-sweeper` |
| Dependency Updates | Standard | `dependency-updater` |
| Complex Refactors | Flagship | `migration-writer` |

## Multi-Model Strategy
The best loops use different models for the Planner, Worker, and Verifier roles:
- **Planner**: Standard (needs good reasoning to create a plan)
- **Worker**: Standard (executes the plan)
- **Verifier**: Lightweight (only needs to check if the goal was met)

This approach maintains high quality while significantly reducing costs.
