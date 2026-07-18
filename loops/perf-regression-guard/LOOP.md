# LOOP.md — perf-regression-guard

> Run Lighthouse/k6 performance audits on PRs, detect regressions, and flag them on pull requests automatically.

---

## Loop Definition

```yaml
name: perf-regression-guard
version: "1.0"

objective: "Run performance audits (Lighthouse/k6) on target routes, identify regressions relative to the baseline, and post reports on the pull request"
# The loop succeeds when performance audits run successfully and any detected regressions are logged and reported.

cadence: "event-driven"      # Triggered on pull requests

tools:
  - bash                    # Run performance audits, build commands
  - file_edit               # Adjust configuration or target files
  - gh                      # Comment on pull requests

file_scope:
  allow:
    - "src/**"              # Source components
    - "pages/**"            # Page-level components
    - "app/**"              # Next.js app directory
    - "public/**"           # Public assets
    - "package.json"        # Project configurations
    - ".loops/perf-regression-guard/**" # Local state, config, and logs
  deny:
    - ".env*"               # Never touch environment files
    - "*.secret"            # Never touch secrets
    - "*.key"               # Never touch keys
    - "infrastructure/**"   # Never touch infra
    - "node_modules/**"     # Never touch dependencies
    - "dist/**"             # Never touch build output
    - ".github/**"          # Never touch CI config

verifier:
  type: test_suite
  command: "npm run perf-test" # Performance check command (exits non-zero on regression)
  timeout_seconds: 300

termination:
  success:
    - no_regression_detected  # verifier.command exits 0
  failure:
    - max_iterations: 5      # Stops after 5 audit-compare runs
    - budget_exhausted       # Stops when token or dollar limit is hit

budget:
  max_tokens: 50000          # Per-run token cap
  max_cost_usd: 1.50         # Hard stop — never exceed this per run

approval_required_for:
  - push_to_main             # Always ask before merging
  - delete_files             # Always ask before deleting files

triggers:
  on_success: []
  on_failure:
    - notify-slack           # Alert team if the check fails or regressions are not resolvable

recovery:
  strategy: rollback_last_commit
  max_retries: 2
  escalation: human

merge_strategy: pr
branch_prefix: loop/perf-regression-guard

state_file: .loops/perf-regression-guard/STATE.md
skill_file: .loops/perf-regression-guard/SKILL.md
```

---

## How This Loop Works

### The Cycle

```
1. Loop triggers when a PR is opened or updated
2. Planner reads STATE.md + SKILL.md, runs performance audits on the PR branch
3. Planner compares metrics (Lighthouse score, p95 latency) against the main branch baseline
4. If a regression is detected:
   a. Planner diagnoses potential causes (bundle size, heavy assets, costly JS)
   b. Planner produces a report and proposes optimizations
   c. Worker applies minor config/asset optimization if safe (or requests human review)
5. Verifier runs performance checks to verify
6. If performance meets criteria -> update STATE.md, post a summary comment on the PR via gh
7. If regression persists -> iterate or escalate
```

### Dry Run

```bash
antigravity /loop perf-regression-guard --dry-run
```

Runs the performance audit and generates the regression analysis report without making any changes or posting to GitHub.

### One-Shot Run

```bash
antigravity /loop perf-regression-guard
```

Executes the full audit-compare-report cycle once and posts the report to the PR.

---

## What "Done" Means

The loop is **COMPLETE** when:
- Performance audits run successfully on all target routes
- Metrics are compared against the baseline with no regressions exceeding thresholds
- A summary report is posted to the pull request via GitHub CLI
- STATE.md is updated with the latest performance metrics

The loop is **BLOCKED** when:
- `max_iterations` (5) is reached
- Budget is exhausted ($1.50 or 50,000 tokens)
- Performance regression is detected but cannot be resolved without code refactoring
- `waiting_for_human: true` is set in STATE.md

---

## Scoping Rules

- **Write access:** Config files and state logs under `.loops/perf-regression-guard/**`, and minor CSS/assets in `public/**` or configs if safe.
- **Read access:** Source files (`src/**`, `pages/**`, `app/**`) to identify optimization targets.
- **Never touch:** Environment variables, CI files, backend logic, test suites.
- **One loop = one scope:** perf-regression-guard only monitors and alerts on performance. It does not perform major code refactoring.
