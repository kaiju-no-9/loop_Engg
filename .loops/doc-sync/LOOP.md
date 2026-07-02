# LOOP.md — doc-sync

> Keep documentation files, architecture notes, and the README in sync with code updates — automatically.

---

## Loop Definition

```yaml
# The loop succeeds when verifier checks confirm that docs reflect the latest code APIs.
  # Loop is successful when verification checks (such as link integrity and doc builds) pass.
name: doc-sync
version: '1.0'
objective: Updating documentation, specifications, and README files to match recent
  source code modifications without introducing code changes
cadence: 0 2 * * *
tools:
- bash
- file_edit
- git
file_scope:
  allow:
  - test/**
  deny:
  - test/**
  - tests/**
  - infrastructure/**
  - .github/**
verifier:
  type: script
  command: npm test
  timeout_seconds: 180
termination:
  success:
  - docs_updated_and_verified
  failure:
  - max_iterations: 5
  - budget_exhausted
  - no_progress_detected
budget:
  max_tokens: 40000
  max_cost_usd: 2.0
approval_required_for:
- delete_files
- push_to_main
triggers:
  on_success:
  - changelog-drafter
  on_failure:
  - notify-slack
recovery:
  strategy: rollback_last_commit
  max_retries: 2
  escalation: human
merge_strategy: pr
branch_prefix: loop/doc-sync
state_file: .loops/doc-sync/STATE.md
skill_file: .loops/doc-sync/SKILL.md
```

---

## How This Loop Works

### The Cycle

```
1. Loop triggered by git push event / commit hook containing changes under src/
2. Planner runs git diff against origin/main to find changed functions, classes, and APIs
3. Planner identifies matching docs in docs/ or README.md requiring sync updates
4. Planner designs markdown modifications (dry-run stops here)
5. Worker updates the markdown docs
6. Verifier builds documentation (if using tools like Docusaurus/VitePress) and checks link integrity
7. If tests/checks pass -> commit atomically, push branch, open PR
8. If checks fail -> rollback and escalate
```

### Dry Run

```bash
claude /loop doc-sync --dry-run
```

Scans the git diff, identifies the APIs that changed, and details which documentation blocks will be updated, making no file changes.

### One-Shot Run

```bash
claude /loop doc-sync
```

Executes the documentation generation/sync process once, updates files, and pushes a PR.

---

## What "Done" Means

The loop is **COMPLETE** when:
- All documentation files correspond to the code state (e.g. function signatures, parameter descriptions, setup guides are updated).
- The verifier script completes with 0 errors (links are correct, formatting is verified).
- A documentation pull request is successfully opened.

The loop is **BLOCKED** when:
- Major design decisions or ambiguous code refactorings make it unclear how docs should change.
- Compilation/link verification fails consistently.
- Budget cap ($1.50) is reached.

---

## Scoping Rules

- **Write access:** Markdown documentation files (`docs/**`, `README.md`, `tutorial/**`) and loop configuration.
- **Read access:** Core source code files (`src/**`, `lib/**`) to parse changes.
- **Never touch:** Code logic, tests, deploy files, databases, or environment keys.
