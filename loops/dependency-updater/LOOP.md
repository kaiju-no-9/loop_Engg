# LOOP.md — dependency-updater

> Safely scan, upgrade, and verify package dependencies weekly — keeping dependencies secure and up-to-date.

---

## Loop Definition

```yaml
name: dependency-updater
version: "1.0"

objective: "Check for outdated dependencies, upgrade them safely, verify the test suite passes, and open a pull request with the updates"
# The loop succeeds when all targeted dependencies are updated and the test suite passes.

cadence: "0 0 * * 1"        # Every Monday at midnight UTC

tools:
  - bash                    # Run package manager update commands and test suites
  - file_edit               # Modify package.json, lockfiles, and local loop logs
  - git                     # Commit atomic updates and push PR branch

file_scope:
  allow:
    - "package.json"        # Node dependency manifest
    - "package-lock.json"   # Node package lockfile
    - "yarn.lock"           # Yarn lockfile
    - "pnpm-lock.yaml"      # pnpm lockfile
    - "go.mod"              # Go module file
    - "go.sum"              # Go sum file
    - "requirements.txt"    # Python dependency file
    - "Gemfile"             # Ruby Gem file
    - "Gemfile.lock"
    - "Cargo.toml"          # Rust dependency manifest
    - "Cargo.lock"
    - ".loops/dependency-updater/**" # Local state, configuration, and update logs
  deny:
    - "src/**"              # Deny access to source code (updates shouldn't edit logic)
    - "test/**"             # Deny writing to tests
    - "tests/**"
    - "infrastructure/**"   # Never touch infra/deployment code
    - ".github/**"          # Never touch CI configuration itself

verifier:
  type: test_suite
  command: "npm test"        # Ensure that package updates did not break the codebase
  timeout_seconds: 300

termination:
  success:
    - all_updates_verified   # verifier exits 0 for all attempted updates
  failure:
    - max_iterations: 15     # Max 15 package update attempts per run
    - budget_exhausted       # Stops if API limits or safety cost limits hit
    - no_progress_detected

budget:
  max_tokens: 60000          # Large context required to analyze dependency conflicts
  max_cost_usd: 2.50         # spend cap per run

approval_required_for:
  - push_to_main             # Direct pushes are strictly forbidden; always use PRs
  - delete_files
  - major_upgrade            # Require human review before upgrading major package versions

triggers:
  on_success:
    - notify-slack           # Notify developers of the opened updates PR
  on_failure:
    - notify-slack           # Notify developers that a dependency broke tests and update blocked

recovery:
  strategy: rollback_last_commit # Roll back the lockfile changes if verification fails
  max_retries: 2
  escalation: human

merge_strategy: pr
branch_prefix: loop/dependency-updater

state_file: .loops/dependency-updater/STATE.md
skill_file: .loops/dependency-updater/SKILL.md
```

---

## How This Loop Works

### The Cycle

```
1. Loop runs on scheduling (every Monday at midnight)
2. Planner runs checks to identify outdated dependencies (e.g. `npm outdated`)
3. Planner prioritizes updates (patch versions first, minor versions next)
4. For each dependency:
   - Worker increments version in package.json and updates lockfile via package manager
   - Verifier runs tests (`npm test`)
   - If tests pass -> commit update atomically (one commit per dependency update)
   - If tests fail -> rollback change, record failure, skip package, and flag for review
5. Once all updates are attempted, open a unified pull request summarizing the changes
6. Update STATE.md and post report
```

### Dry Run

```bash
claude /loop dependency-updater --dry-run
```

Scans the package manifest, identifies outdated packages, projects the monthly/weekly change roadmap, and proposes update candidates without modifying package files.

### One-Shot Run

```bash
claude /loop dependency-updater
```

Executes the full update-test-commit cycle once, pushing the results to a pull request branch.

---

## What "Done" Means

The loop is **COMPLETE** when:
- Outdated dependencies are processed (either successfully updated or flagged as broken).
- The verifier script (`npm test`) passes on the updated files.
- A pull request detailing updated packages, their changelogs, and test results is opened.

The loop is **BLOCKED** when:
- A critical dependency update fails tests and cannot be updated cleanly (reverts and logs).
- Compilation or environment lockfile errors occur that require manual resolution.
- Budget cap ($2.50) is reached.

---

## Scoping Rules

- **Write access:** Dependency configuration files (`package.json`, `package-lock.json`, `requirements.txt`, etc.) and state logs.
- **Read access:** Whitelisted files only.
- **Never touch:** Source code logic, unit/integration test code, or production infrastructure.
