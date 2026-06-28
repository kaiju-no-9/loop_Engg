---
name: dependency-updater-skill
description: >
  Scans, updates, and tests project package dependencies in safe incremental
  batches. Trigger on "update packages", "upgrade dependencies", or "fix security CVEs".
  Do NOT use for refactoring source code.
---

# Dependency Updater Skill

An agent skill for checking package manager registries, identifying outdated or insecure libraries, applying updates in isolated batches, running verification tests, and opening detailed pull requests. The agent isolates each update to verify that no breaking changes are introduced. It never updates source code files, never commits broken builds, and rolls back packages immediately if tests fail.

---

## When to Use This Skill

Use this skill when:
- Project packages need weekly maintenance to stay current and secure.
- Vulnerability scans (e.g. `npm audit`, `snyk`) flag security CVEs that need immediate patching.
- Libraries need updating to patch versions or minor versions containing bug fixes.

Do NOT use this skill for:
- Writing or refactoring source code (use `code-repair` instead).
- Fixing or updating test code when tests fail due to package changes (tests shouldn't be altered to hide breaking dependency updates).
- Upgrading major versions of critical libraries (e.g., changing React v17 to v18) without human approval.
- Managing database migrations or server environment variables.

---

## Quick Reference

| Command / Tool | Stack | Action |
|---|---|---|
| `npm outdated` / `npm update` | Node.js | List and upgrade packages |
| `pip list --outdated` / `pip install -U` | Python | List and upgrade packages |
| `go list -m -u all` / `go get -u` | Go | List and upgrade modules |
| `cargo outdated` / `cargo update` | Rust | List and upgrade crates |
| `bundle outdated` / `bundle update` | Ruby | List and upgrade gems |

---

## Workflow: Manage Package Updates

1. **Scan for outdated packages** — Run the package manager's scan command to get the list of outdated dependencies:
   ```bash
   npm outdated --json
   ```
2. **Prioritize updates** — Parse the package list and sort them into a roadmap:
   - Group 1: Security vulnerability patches (highest priority).
   - Group 2: Patch updates (`1.0.x` → `1.0.y`).
   - Group 3: Minor updates (`1.x.0` → `1.y.0`).
   - Group 4: Major updates (require human review gate).
3. **Execute incremental updates** — For each package candidate:
   - Create a clean git branch named `loop/dependency-updater/<package-name>`.
   - Update the package to the target version:
     ```bash
     npm install <package-name>@<target-version>
     ```
   - Run the verifier command:
     ```bash
     npm test
     ```
   - **Decision Path:**
     - **If tests pass:** Commit the change with a semantic commit message: `chore(deps): bump <package-name> from <old-version> to <new-version>`.
     - **If tests fail:** Roll back the package immediately using git:
       ```bash
       git checkout -- package.json package-lock.json
       npm install
       ```
       Log the package and test failures in `STATE.md` under `unfixable` and continue to the next package.
4. **Compile PR** — Combine all successful updates into a single PR branch and push:
   ```bash
   gh pr create --title "chore(deps): update dependencies" --body "Detailed list of successfully updated packages and test results."
   ```
5. **Log execution** — Record processed packages, statuses, and PR links in `STATE.md`.

---

## Decision Rules

- **If the update is a major version bump** → Do NOT apply directly. Check if the major version has an approval override in `LOOP.md`. If not, list it in `STATE.md` under `waiting_for_human` with a recommendation, and skip.
- **If multiple packages are linked (peer dependencies)** → Update them in the same batch (e.g. `eslint` and its plugins). If the verifier fails, roll back all of them together.
- **If the lockfile becomes corrupt or has conflicts** → Run `npm clean-install` or the equivalent. If the corruption persists, halt the loop, set `waiting_for_human: true`, and escalate.
- **If a package update causes compilation failures (build errors)** → Treat it as a test failure: rollback immediately, log, and skip.

---

## Example

**Input:**
`npm outdated` output:
```json
{
  "lodash": {
    "current": "4.17.20",
    "wanted": "4.17.21",
    "latest": "4.17.21"
  },
  "axios": {
    "current": "0.21.0",
    "wanted": "0.21.4",
    "latest": "1.4.0"
  }
}
```

**Steps the agent takes:**
1. Focuses on `lodash` patch update (`4.17.20` → `4.17.21`).
2. Installs `lodash@4.17.21` and runs `npm test` → Tests pass.
3. Commits: `chore(deps): bump lodash from 4.17.20 to 4.17.21`.
4. Focuses on `axios` minor update (`0.21.0` → `0.21.4`).
5. Installs `axios@0.21.4` and runs `npm test` → Tests pass.
6. Commits: `chore(deps): bump axios from 0.21.0 to 0.21.4`.
7. Skips `axios` major update (`0.21.4` → `1.4.0`) because major updates require review.
8. Opens a PR combining both changes.

**Output in STATE.md:**
```yaml
last_run: 2026-06-28T10:00:00Z
status: COMPLETE
packages_updated:
  - lodash: "4.17.20 -> 4.17.21"
  - axios: "0.21.0 -> 0.21.4"
packages_skipped:
  - axios (major upgrade skipped: 0.21.4 -> 1.4.0)
```

---

## Guardrails

- Never rewrite or modify test assertions to force a failing dependency upgrade to pass.
- Never edit source files (`src/**`) to fix breaking updates (rollback and request human review instead).
- Keep changes atomic: never mix a package update with other feature development or chores.
- Never override pre-existing whitelisted lockfile resolutions without explicit permission.
