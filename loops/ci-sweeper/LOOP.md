# LOOP.md — ci-sweeper

> Fix all failing CI tests overnight with minimal diff — while you sleep.

---

## Loop Definition

```yaml
name: ci-sweeper
version: "1.0"

objective: "Fix all failing CI tests in the project with minimal, targeted code changes"
# Must be ONE testable sentence. The loop succeeds when `verifier.command` exits 0.

cadence: "0 2 * * *"        # Every night at 2am UTC

tools:
  - bash                    # Run shell commands (test suite, git)
  - file_edit               # Read and write source/test files
  - git                     # Commit and push changes

file_scope:
  allow:
    - "src/**"              # Read access to understand code under test
    - "lib/**"              # Read access to library code
    - "test/**"             # Read + write — primary working area
    - "tests/**"            # Alternative test directory
    - "__tests__/**"        # Jest convention
    - "spec/**"             # RSpec / Jasmine convention
    - "*.config.js"         # Test config files (jest.config, vitest.config, etc.)
    - "*.config.ts"
    - "package.json"        # Read — to understand test scripts
    - "tsconfig.json"       # Read — to understand TypeScript config
  deny:
    - ".env*"               # Never touch environment files
    - "*.secret"            # Never touch secrets
    - "*.key"               # Never touch keys
    - "infrastructure/**"   # Never touch infra
    - "terraform/**"        # Never touch IaC
    - "k8s/**"              # Never touch k8s manifests
    - ".github/**"          # Never touch CI config itself
    - "node_modules/**"     # Never touch dependencies
    - "dist/**"             # Never touch build output

verifier:
  type: test_suite
  command: "npm test"        # Loop succeeds when this exits 0
  timeout_seconds: 300       # Kill the test run after 5 minutes

termination:
  success:
    - all_tests_pass         # verifier.command exits 0
  failure:
    - max_iterations: 10     # Hard stop after 10 passes through the loop
    - no_progress_detected   # Stops if two consecutive runs touch the same files with no test improvement
    - budget_exhausted       # Stops when token or dollar limit is hit

budget:
  max_tokens: 50000          # Per-run token cap
  max_cost_usd: 2.00         # Hard stop — never exceed this per run

approval_required_for:
  - push_to_main             # Always ask before merging to main
  - delete_files             # Always ask before deleting any file
  - modify_config            # Always ask before changing config files

triggers:
  on_success:
    - changelog-drafter      # Draft release notes after successful fixes
  on_failure:
    - notify-slack           # Alert the team if the loop fails

recovery:
  strategy: rollback_last_commit   # git revert HEAD — undo the last atomic commit
  max_retries: 2                   # Retry twice before escalating
  escalation: human                # Final fallback is always human review

merge_strategy: pr                 # Open a PR for review (recommended)
branch_prefix: loop/ci-sweeper     # Branch naming convention

state_file: .loops/ci-sweeper/STATE.md
skill_file: .loops/ci-sweeper/SKILL.md
```

---

## How This Loop Works

### The Cycle

```
1. Orchestrator triggers the loop (cron at 2am or manual)
2. Planner reads STATE.md + SKILL.md, runs `npm test`, analyzes failures
3. Planner produces a step-by-step fix plan (dry-run stops here)
4. Worker executes the plan — one fix per atomic commit
5. Verifier runs `npm test` in a fresh context
6. If tests pass → update STATE.md, trigger changelog-drafter
7. If tests fail → iterate (up to max_iterations)
8. If stuck → recovery protocol (rollback, retry, escalate)
```

### Dry Run

```bash
claude /loop ci-sweeper --dry-run
```

Shows the Planner's analysis and proposed fixes without making any changes. Always start here.

### One-Shot Run

```bash
claude /loop ci-sweeper
```

Executes the full loop once. Review the PR it opens.

### Scheduled Run

Push `.github/workflows/ci-sweeper.yml` to enable nightly runs at 2am UTC.

---

## What "Done" Means

The loop is **COMPLETE** when:
- `npm test` exits with code 0 (all tests pass)
- All changes are committed atomically (one commit per fix)
- A PR is opened with a summary of fixes
- STATE.md is updated with run results

The loop is **BLOCKED** when:
- `max_iterations` (10) reached without all tests passing
- Budget exhausted ($2.00 or 50,000 tokens)
- Two consecutive iterations changed the same files with no improvement
- `waiting_for_human: true` is set in STATE.md

---

## Scoping Rules

- **Write access:** test files only (`test/**`, `tests/**`, `__tests__/**`, `spec/**`)
- **Read access:** source files (`src/**`, `lib/**`) — to understand the code under test
- **Never touch:** env files, secrets, infrastructure, CI config, node_modules, dist
- **One loop = one scope:** ci-sweeper only fixes tests. It does not refactor source code, update dependencies, or modify CI pipelines.
