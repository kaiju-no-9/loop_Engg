# LOOP.md — changelog-drafter

> Automatically scan git history, categorize commits, and draft beautiful release notes in CHANGELOG.md.

---

## Loop Definition

```yaml
name: changelog-drafter
version: "1.0"

objective: "Collect git commit logs and pull requests, categorize them, and draft/update the CHANGELOG.md file for the upcoming release tag"
# The loop succeeds when CHANGELOG.md is successfully updated and validated with release entries.

cadence: "on_release"        # Triggered when a new release tag is pushed or deployment succeeds

tools:
  - bash                    # Run git log, git tag, and extract merge PR details
  - file_edit               # Read and write CHANGELOG.md and local release draft assets
  - git                     # Commit and push updated changelog to branch

file_scope:
  allow:
    - "CHANGELOG.md"        # Primary changelog file
    - "docs/releases/**"    # Storage directory for historical release note drafts
    - ".loops/changelog-drafter/**" # Local state, configuration, and draft templates
  deny:
    - "src/**"              # Deny access to source files
    - "test/**"             # Deny writing to tests
    - "tests/**"
    - "infrastructure/**"   # Never touch infrastructure
    - ".github/**"          # Never touch CI configuration

verifier:
  type: script
  command: "git diff --name-only | grep -q CHANGELOG.md"
  # Loop succeeds if it successfully registers modifications inside CHANGELOG.md.
  timeout_seconds: 120

termination:
  success:
    - changelog_drafted      # verifier finds modified changelog entry
  failure:
    - max_iterations: 3      # Changelog compilation is straightforward; max 3 runs
    - budget_exhausted       # Stops if API usage limits reached
    - no_progress_detected

budget:
  max_tokens: 30000          # Low-medium budget
  max_cost_usd: 1.00         # spend cap per run

approval_required_for:
  - push_to_main             # Review and approve changelog pull requests before merging
  - delete_files

triggers:
  on_success:
    - notify-slack           # Post the drafted release notes to team Slack channel
  on_failure:
    - notify-slack

recovery:
  strategy: pause
  max_retries: 1
  escalation: human

merge_strategy: pr
branch_prefix: loop/changelog-drafter

state_file: .loops/changelog-drafter/STATE.md
skill_file: .loops/changelog-drafter/SKILL.md
```

---

## How This Loop Works

### The Cycle

```
1. Loop triggered by code deployment or push of a release tag (e.g. v1.1.0)
2. Planner identifies the range of git commits (between previous release tag and current tag / HEAD)
3. Planner fetches git history and extracts commit descriptions and pull request descriptions
4. Planner categorizes commits into: Added, Changed, Fixed, Security, Deprecated, Removed
5. Planner generates the formatted markdown entry for CHANGELOG.md (dry-run stops here)
6. Worker writes the formatted release entry to CHANGELOG.md
7. Verifier checks that CHANGELOG.md is successfully updated
8. Loop commits change, pushes branch, opens PR, and posts drafted notes
```

### Dry Run

```bash
claude /loop changelog-drafter --dry-run
```

Scans the git history since the last release tag, categorizes commits, and prints the proposed markdown entry for the changelog, modifying no files.

### One-Shot Run

```bash
claude /loop changelog-drafter
```

Runs the changelog compile cycle once, writes the entry, and pushes a PR.

---

## What "Done" Means

The loop is **COMPLETE** when:
- Git commits since the last release are categorized and formatted.
- `CHANGELOG.md` is updated at the top with the new version heading and date.
- A pull request containing the updated `CHANGELOG.md` is successfully opened.

The loop is **BLOCKED** when:
- Git log is empty or no changes since the last version tag are found.
- The repository has no prior tags (preventing range detection).
- Budget cap ($1.00) is exceeded.

---

## Scoping Rules

- **Write access:** `CHANGELOG.md`, `docs/releases/**`, and local loop configuration.
- **Read access:** Whitelisted files only.
- **Never touch:** Code base logic, test files, or CI workflow files.
