# Loop Library
<img width="804" height="294" alt="PHOTO-2026-07-01-16-09-49" src="https://github.com/user-attachments/assets/1c94bd63-d1c5-4589-8cb1-77cc8288b386" />


> **Every AI coding tool has a model. None of them has
 the loop runtime. This is the missing layer.**

An open-source library of reusable AI agent loops — pre-designed autonomous workflows you install into your project and run with any major coding agent.


---

## What Is a Loop?

A **loop** is a repeating cycle in which an AI agent takes an action, receives feedback from its environment, uses that feedback to decide the next move, and continues until a defined termination condition is met.

Instead of prompting an AI agent 40 times a day, you design a loop once and review a `STATE.md` file once a day.

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│  ORCHESTRATOR │────▶│    PLANNER   │────▶│    WORKER    │────▶│   VERIFIER   │
│  (cron/event) │     │  (makes plan)│     │ (executes)   │     │  (checks)    │
└──────────────┘     └──────────────┘     └──────────────┘     └──────────────┘
```

---

## Quick Start & Installation

### Step 1: Install the Loop Wizard CLI
Install the official unified CLI tool to manage and scaffold loops in your projects:

```bash
# Install via PyPI
pip install loop-wizard

# Or for local development from source
pip install -e tools/loop-wizard
```

### Step 2: Initialize a Loop in your project
Navigate to the root of your target project directory and run the initialization wizard:
```bash
loop-wizard init .
```
This launches an interactive fuzzy-search picker to select a loop pattern (e.g., `ci-sweeper`, `daily-triage`, `doc-sync`) and choose your AI coding tool (e.g., `antigravity`, `claude-code`, `gemini-cli`).

Alternatively, scaffold non-interactively:
```bash
loop-wizard init . --pattern ci-sweeper --tool antigravity --yes
```

### Step 3: Configure `LOOP.md`
Open the generated folder `.loops/<pattern-name>/` in your project and edit the `LOOP.md` file to set up your specific verification command and token/cost budgets:
```yaml
verifier:
  type: test_suite
  command: "npm test"     # Set this to your test runner command
budget:
  max_tokens: 50000
  max_cost_usd: 2.00      # Set your budget safety guardrails
```

### Step 4: Run a Dry Run (Safe Mode)
Perform a safe test run to see the plan the AI agent would make without modifying any of your source code:
```bash
# For Antigravity
antigravity /loop ci-sweeper --dry-run

# For Claude Code
claude /loop ci-sweeper --dry-run
```

### Step 5: Run the Loop
Start the autonomous fix-verify cycle:
```bash
antigravity /loop ci-sweeper
```

### Step 6: Monitor Execution & Status
Track execution statistics and state changes using the CLI status dashboard:
```bash
# Check current results
loop-wizard status ci-sweeper

# Watch live updates (auto-refreshes every 30s)
loop-wizard status ci-sweeper --watch
```

### Step 7: Automate on GitHub Actions
The wizard automatically generated a GitHub Action workflow file in `.github/workflows/<pattern-name>.yml`. To deploy it to run on a schedule:
1. Commit and push the `.loops/` configs and the workflow file to your GitHub repository:
   ```bash
   git add .loops/ .github/workflows/
   git commit -m "ci: integrate ci-sweeper loop"
   git push origin main
   ```
2. Add your AI tool API Key (e.g., `GEMINI_API_KEY`, `ANTHROPIC_API_KEY`) as a **GitHub Secret** in your repository settings under `Settings -> Secrets and variables -> Actions`.

---

## Loop Catalog

### General / Meta

| Loop | What It Does | Cadence |
|------|-------------|---------|
| [`daily-triage`](loops/daily-triage/) | Scans GitHub issues, labels and assigns them | Daily, 8am |
| [`changelog-drafter`](loops/changelog-drafter/) | Drafts release notes from merged PRs | On release tag |
| [`dependency-updater`](loops/dependency-updater/) | Updates packages, runs tests, opens a PR | Weekly |
| [`stale-branch-janitor`](loops/stale-branch-janitor/) | Lists stale branches, cleans up with approval | Weekly |

### Backend

| Loop | What It Does | Cadence |
|------|-------------|---------|
| [`ci-sweeper`](loops/ci-sweeper/) | Fixes failing CI tests overnight | Nightly, 2am |
| [`code-repair`](loops/code-repair/) | Fixes failing tests with minimal diff | On test failure |
| [`api-contract-sync`](loops/api-contract-sync/) | Keeps OpenAPI spec in sync with routes | On file change |
| [`security-scan`](loops/security-scan/) | Scans deps, flags CVEs, opens issues | Weekly |
| [`migration-writer`](loops/migration-writer/) | Detects schema changes, generates migrations | On schema change |
| [`api-consumer-notifier`](loops/api-consumer-notifier/) | Detects breaking API changes, notifies dependents | On merge to main |

### Frontend

| Loop | What It Does | Cadence |
|------|-------------|---------|
| [`ui-test-sweeper`](loops/ui-test-sweeper/) | Fixes broken Playwright/Cypress selectors | Nightly |
| [`accessibility-audit`](loops/accessibility-audit/) | Runs axe-core, proposes and applies fixes | Weekly |
| [`perf-regression-guard`](loops/perf-regression-guard/) | Runs Lighthouse/k6, flags regressions | On PR |

### Quality

| Loop | What It Does | Cadence |
|------|-------------|---------|
| [`test-coverage-grower`](loops/test-coverage-grower/) | Finds untested functions, writes tests, opens PR | Weekly |

### Infrastructure / DevOps

| Loop | What It Does | Cadence |
|------|-------------|---------|
| [`cost-anomaly-detector`](loops/cost-anomaly-detector/) | Reads cloud cost data, flags anomalies | Daily |

### Docs

| Loop | What It Does | Cadence |
|------|-------------|---------|
| [`doc-sync`](loops/doc-sync/) | Keeps docs in sync when code changes | On commit |

---

## Repo Structure

```
loop-library/
├── loops/                    # Loop definitions (LOOP.md + SKILL.md + STATE.md)
├── skills/                   # Reusable agent capabilities
├── tools/                    # CLI tooling
│   ├── loop-init/            # Scaffold a loop into your project
│   ├── loop-audit/           # Score production readiness (0–100)
│   ├── loop-cost/            # Estimate token/dollar cost
│   └── loop-dashboard/       # Aggregate health across all loops
├── patterns/
│   └── registry.yaml         # Machine-readable catalog of all loops
├── docs/                     # Guides and references
├── loop-budget.md            # Token caps and cost guardrails
└── README.md
```

---

## CLI Tools

### `loop-wizard` — Unified Python CLI (recommended)

All tools in one command. Install with `pip install -e tools/loop-wizard`.

```bash
# Scaffold a loop (interactive search picker + 5-question setup wizard)
loop-wizard init .

# Score production readiness (0–100) with visual scorecard
loop-wizard audit . --suggest

# Estimate cost before running with token split allocation gauges
loop-wizard cost -p ci-sweeper

# Aggregate health overview dashboard
loop-wizard dashboard .

# Check loop execution results with status panel
loop-wizard status ci-sweeper
loop-wizard status ci-sweeper --watch   # live auto-refresh every 30s
loop-wizard status ci-sweeper --json    # machine-readable
```

### Supported Agent Tools

The `--tool` flag (and interactive picker) accepts any of these agents:

| Tool | Provider | Run Command | API Key Secret |
|------|----------|-------------|----------------|
| `claude-code` | Anthropic | `claude /loop <pattern>` | `ANTHROPIC_API_KEY` |
| `claude` | Anthropic | `claude /loop <pattern>` | `ANTHROPIC_API_KEY` |
| `gemini-cli` | Google | `gemini /loop <pattern>` | `GEMINI_API_KEY` |
| `antigravity` | Google DeepMind | `antigravity /loop <pattern>` | `GOOGLE_API_KEY` / `GEMINI_API_KEY` |
| `cursor` | Cursor / Anysphere | `cursor /loop <pattern>` | `OPENAI_API_KEY` / `ANTHROPIC_API_KEY` |
| `opencode` | SST / Open-source | `opencode run /loop <pattern>` | `OPENCODE_API_KEY` (+ provider key) |
| `codex` | OpenAI | `codex /loop <pattern>` | `OPENAI_API_KEY` |

> **OpenCode** is model-agnostic — it supports 75+ providers. Set whichever provider key (`ANTHROPIC_API_KEY`, `OPENAI_API_KEY`, etc.) matches your chosen backend model.

---

## The LOOP.md Schema

Every loop follows this schema:

```yaml
name: ci-sweeper
version: "1.0"
objective: "Fix all failing CI tests with minimal diff"
cadence: "0 2 * * *"
tools: [bash, file_edit, git]
file_scope:
  allow: ["src/**", "tests/**"]
  deny: [".env*", "infrastructure/**"]
verifier:
  type: test_suite
  command: "npm test"
termination:
  success: [all_tests_pass]
  failure: [max_iterations: 10, budget_exhausted]
budget:
  max_tokens: 50000
  max_cost_usd: 2.00
approval_required_for: [push_to_main, delete_files]
triggers:
  on_success: [changelog-drafter]
recovery:
  strategy: rollback_last_commit
  max_retries: 2
  escalation: human
```

---

## Safety Guardrails

Every loop ships with these built-in:

| Guardrail | How It Works |
|-----------|-------------|
| **Dry run mode** | `--dry-run` shows the plan, makes zero changes |
| **File scope** | `file_scope.allow` / `deny` enforced by runner |
| **Budget cap** | Hard token + dollar limit per run |
| **Iteration limit** | `max_iterations` prevents infinite loops |
| **No-progress detection** | Stops if two consecutive runs show no improvement |
| **Approval gates** | Destructive actions always require human confirmation |
| **Atomic commits** | Every change is one commit — easy to revert |
| **Separate verifier** | Fresh model instance checks "done" |
| **Recovery protocol** | Automatic rollback, retry, and human escalation |

---

## Trust Ramp

Start cautious. Build trust over 4 weeks:

| Week | Mode | What Happens |
|------|------|-------------|
| 1 | `--dry-run` | Read the plan, make no changes |
| 2 | Manual one-shot | Run it, review what it did |
| 3 | Scheduled, report-only | Opens a PR for you to merge |
| 4 | Fully autonomous | Merges within defined gates |

See [docs/TRUST_RAMP.md](docs/TRUST_RAMP.md) for the full protocol.

---

## Documentation

| Doc | What It Covers |
|-----|---------------|
| [DESIGN_CHECKLIST](docs/DESIGN_CHECKLIST.md) | What makes a loop production-ready |
| [CONTRIBUTING](docs/CONTRIBUTING.md) | How to add a new loop |
| [FAILURE_MODES](docs/FAILURE_MODES.md) | Common failures and mitigations |
| [LOOP_COMPOSITION](docs/LOOP_COMPOSITION.md) | How to safely chain loops |
| [TRUST_RAMP](docs/TRUST_RAMP.md) | 4-week trust-building protocol |
| [COST_GUIDE](docs/COST_GUIDE.md) | Cost benchmarks per model |
| [MODEL_SELECTION](docs/MODEL_SELECTION.md) | Which model for which loop |
| [OBSERVABILITY](docs/OBSERVABILITY.md) | Dashboards and monitoring |
| [RECOVERY](docs/RECOVERY.md) | Failure recovery strategies |

---

## Contributing

See [docs/CONTRIBUTING.md](docs/CONTRIBUTING.md) for full instructions.

**Quick version:**
1. Fork and clone this repo
2. Create your loop under `loops/<loop-name>/` with LOOP.md, SKILL.md, STATE.md
3. Run `npx loop-audit . --suggest` — aim for 80+
4. Open a PR with your `loop-cost` estimate

---

## Warnings

- **Token costs compound fast** with sub-agents and long-running loops. Always set a budget cap.
- **Chained loops multiply cost.** Monitor with `loop-dashboard`.
- **Unattended loops make unattended mistakes.** The audit trail is your safety net.
- **Scope loops tightly.** Use `file_scope` — a loop that can touch everything will eventually touch the wrong thing.

---

## License

MIT — use freely, contribute back.

---

*Inspired by Addy Osmani's "Loop Engineering" essay (June 2026), Peter Steinberger's original post, and Boris Cherny's work on Claude Code.*
