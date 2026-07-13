# LOOP.md — code-repair

> Fix failing tests by repairing the source code — not the tests — with the smallest possible diff, triggered on any test failure.

---

## Loop Definition

```yaml
name: code-repair
version: "1.0"

objective: "Diagnose test failures, trace them to source code bugs, and apply minimal production-code fixes that make the test suite pass"
# The loop succeeds when the verifier command exits 0 (all tests pass).

cadence: "event-driven"      # Triggered on test failure (CI failure, manual invocation)

tools:
  - bash                    # Run test suites, git commands, and build tools
  - file_edit               # Read and write source code and test files
  - git                     # Commit atomic fixes and push PR branch

file_scope:
  allow:
    - "src/**"              # Source code — primary fix target
    - "lib/**"              # Library code
    - "app/**"              # Application code (Rails, Next.js)
    - "pkg/**"              # Package code (Go convention)
    - "internal/**"         # Internal packages (Go convention)
    - "test/**"             # Test files (read to understand assertions; write only when test is wrong)
    - "tests/**"            # Alternative test directory
    - "__tests__/**"        # Jest convention
    - "spec/**"             # RSpec / Jasmine convention
    - "*.config.js"         # Config files (read-only context)
    - "*.config.ts"
    - "package.json"        # Read — to understand scripts and dependencies
    - "tsconfig.json"       # Read — TypeScript configuration
    - "go.mod"              # Read — Go module configuration
    - "requirements.txt"    # Read — Python dependencies
    - ".loops/code-repair/**"  # Local state, configuration, and logs
  deny:
    - ".env*"               # Never touch environment files
    - "*.secret"            # Never touch secrets
    - "*.key"               # Never touch keys
    - "infrastructure/**"   # Never touch infra
    - "terraform/**"        # Never touch IaC
    - "k8s/**"              # Never touch k8s manifests
    - ".github/**"          # Never touch CI config
    - "node_modules/**"     # Never touch dependencies
    - "dist/**"             # Never touch build output
    - "build/**"            # Never touch build output
    - "vendor/**"           # Never touch vendored dependencies
    - "migrations/**"       # Never touch database migrations

verifier:
  type: test_suite
  command: "npm test"        # Loop succeeds when this exits 0
  timeout_seconds: 600       # 10 minutes — source fixes may require longer test runs

termination:
  success:
    - all_tests_pass         # verifier.command exits 0
  failure:
    - max_iterations: 15     # Hard stop after 15 fix-verify cycles (higher than ci-sweeper)
    - no_progress_detected   # Stops if two consecutive runs touch the same files with no test improvement
    - budget_exhausted       # Stops when token or dollar limit is hit

budget:
  max_tokens: 80000          # Large context — needs to understand source + test + error traces
  max_cost_usd: 3.00         # Higher budget than ci-sweeper — source fixes are more complex

approval_required_for:
  - push_to_main             # Always ask before merging to main
  - delete_files             # Always ask before deleting any file
  - modify_public_api        # Ask before changing exported function signatures
  - refactor_beyond_scope    # Ask if a fix requires changing >3 files

triggers:
  on_success: []
  on_failure:
    - notify-slack           # Alert the team if the loop fails

recovery:
  strategy: rollback_last_commit   # git revert HEAD — undo the last atomic commit
  max_retries: 2                   # Retry twice before escalating
  escalation: human                # Final fallback is always human review

merge_strategy: pr                 # Open a PR for review (critical for source code changes)
branch_prefix: loop/code-repair

state_file: .loops/code-repair/STATE.md
skill_file: .loops/code-repair/SKILL.md
```

---

## How This Loop Works

### The Cycle

```
1. Loop triggers on test failure (CI event, manual invocation)
2. Planner reads STATE.md + SKILL.md, runs the test suite, captures failure output
3. Planner traces each failure to a root cause in the source code (not the test)
4. Planner produces a prioritized fix plan targeting source code (dry-run stops here)
5. Worker applies fixes to source code — one fix per atomic commit
6. Verifier runs the full test suite in a fresh context
7. If all tests pass → update STATE.md, mark COMPLETE
8. If tests still fail → iterate (up to max_iterations)
9. If stuck → recovery protocol (rollback, retry, escalate)
```

### Key Difference from ci-sweeper

| Aspect | ci-sweeper | code-repair |
|---|---|---|
| **Fix target** | Tests first, source as fallback | Source code first, tests only if test is wrong |
| **Trigger** | Nightly cron | Event-driven (on test failure) |
| **Budget** | $2.00 / 50k tokens | $3.00 / 80k tokens |
| **Max iterations** | 10 | 15 |
| **Complexity** | Medium | Heavy |
| **Scope** | Primarily test files | Primarily source files |

### Dry Run

```bash
claude /loop code-repair --dry-run
```

Runs the test suite, analyzes failures, traces root causes to source code, and produces a fix plan without modifying any files.

### One-Shot Run

```bash
claude /loop code-repair
```

Executes the full diagnose-fix-verify cycle once. Review the PR it opens.

---

## What "Done" Means

The loop is **COMPLETE** when:
- The test suite passes (exit code 0)
- All source code fixes are committed atomically (one commit per bug fix)
- A PR is opened with a summary of bugs found and fixes applied
- STATE.md is updated with run results

The loop is **BLOCKED** when:
- `max_iterations` (15) reached without all tests passing
- Budget exhausted ($3.00 or 80,000 tokens)
- Two consecutive iterations changed the same files with no test improvement
- A fix requires architectural changes beyond minimal diff
- A fix requires installing or updating dependencies
- `waiting_for_human: true` is set in STATE.md

---

## Scoping Rules

- **Write access:** Source code (`src/**`, `lib/**`, `app/**`, `pkg/**`) — primary fix target. Test files only when the test itself is wrong.
- **Read access:** All allowed files — to understand code under test, error context, and configuration
- **Never touch:** Environment files, secrets, infrastructure, CI config, node_modules, dist, migrations
- **One loop = one scope:** code-repair fixes source code bugs that cause test failures. It does not write new tests (use `test-coverage-grower`), update dependencies (use `dependency-updater`), or fix CI pipelines.
