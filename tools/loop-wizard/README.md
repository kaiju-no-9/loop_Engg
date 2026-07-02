# Loop Wizard 🪐

The unified command-line tool for **Loop Engineering**. Scaffold, audit, estimate, and monitor autonomous AI agent loops in your projects.

---

## What is a Loop?
A **loop** is a repeating cycle in which an AI agent takes an action, receives feedback from its environment (such as test runs, git status, lint errors), uses that feedback to decide the next move, and continues until a defined termination condition is met.

Instead of prompting an AI agent dozens of times a day, you design a loop once and let it run autonomously (e.g. overnight in CI/CD) and review its status file once a day.

---

## Features & Commands

`loop-wizard` acts as a single control plane for all your loop engineering needs:

### 1. Scaffold a Loop
Initialize a pre-designed loop pattern into your project with a step-by-step interactive setup wizard.
```bash
loop-wizard init .
```
Or run non-interactively for automation:
```bash
loop-wizard init . --pattern ci-sweeper --tool claude-code --yes
```

### 2. Audit Production Readiness
Score a loop's configuration from 0 to 100 based on safety guardrails, budget limits, file scoping, and termination triggers.
```bash
loop-wizard audit . --suggest
```

### 3. Estimate Run Costs
Project token consumption and monthly dollar costs based on model selections, cadence presets, and token caps.
```bash
loop-wizard cost --pattern ci-sweeper --cadence daily
```

### 4. Monitor Loop Execution
Check the current state, recent runs, files changed, and budget usage of a running or completed loop.
```bash
loop-wizard status ci-sweeper
```
Add the `--watch` flag for a live terminal dashboard that auto-refreshes every 30 seconds:
```bash
loop-wizard status ci-sweeper --watch
```

### 5. Aggregate Health Dashboard
Generate an overview report summarizing active loops, accumulated costs, git commits made, and runs waiting for human approval.
```bash
loop-wizard dashboard .
```

---

## Installation

Install the package directly from PyPI:

```bash
pip install loop-wizard
```

For local development or custom modifications, clone the repository and run:

```bash
pip install -e tools/loop-wizard
```

---

## Supported AI Agent Tools

The wizard supports generating configurations and CI/CD pipelines for:
* **Claude Code** (`claude-code`, `claude`)
* **Gemini CLI** (`gemini-cli`)
* **Antigravity** (`antigravity` — by Google DeepMind)
* **Cursor** (`cursor`)
* **OpenCode** (`opencode`)
* **Codex** (`codex`)

---

## License
MIT — use freely, contribute back.
