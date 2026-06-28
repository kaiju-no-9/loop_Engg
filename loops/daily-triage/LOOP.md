# LOOP.md — daily-triage

> Scan open GitHub issues every morning, label them by category/severity, and suggest assignees based on area ownership.

---

## Loop Definition

```yaml
name: daily-triage
version: "1.0"

objective: "Triaging all untriaged open issues by labeling them and assigning/recommending owners without human intervention"
# The loop succeeds when no issues matching the untriaged criteria remain.

cadence: "0 8 * * *"        # Every morning at 8am local/UTC time

tools:
  - bash                    # Run gh CLI to fetch, label, and update issues
  - file_edit               # Write and edit local logs or cache in .loops/daily-triage/
  - git                     # Commit and push state and triage logs

file_scope:
  allow:
    - ".loops/daily-triage/**" # Local state, logs, and execution cache
    - "triage-rules.md"        # Localized repository triage mapping rules (read-only)
  deny:
    - "src/**"                 # Deny access to source code
    - "test/**"                # Deny access to test suites
    - "tests/**"
    - "lib/**"
    - ".github/workflows/**"   # Never modify CI workflows

verifier:
  type: script
  command: "gh issue list --state open --label \"needs-triage\" --limit 1"
  # Loop is considered successful if there are 0 issues with the "needs-triage" label.
  timeout_seconds: 120

termination:
  success:
    - no_untriaged_issues    # verifier.command returns no issues
  failure:
    - max_iterations: 5      # Triage in batches; stop after 5 iterations
    - no_progress_detected   # Stop if same issues fail to triage repeatedly
    - budget_exhausted       # Token or cost limits reached

budget:
  max_tokens: 30000          # Triage is cheap; low token cap
  max_cost_usd: 1.00         # Hard stop budget limit per run

approval_required_for:
  - delete_files             # Protect against any accidental file deletions
  - close_issue              # Never close issues autonomously without human approval

triggers:
  on_success:
    - notify-slack           # Post daily triage report to team Slack channel
  on_failure:
    - notify-slack           # Notify maintainers if triage fails or runs out of budget

recovery:
  strategy: pause            # Pause the loop, wait for human
  max_retries: 1
  escalation: human

merge_strategy: pr
branch_prefix: loop/daily-triage

state_file: .loops/daily-triage/STATE.md
skill_file: .loops/daily-triage/SKILL.md
```

---

## How This Loop Works

### The Cycle

```
1. Orchestrator triggers the loop (cron at 8am or manual run)
2. Planner reads STATE.md, rules in triage-rules.md, and fetches untriaged issues using `gh`
3. Planner generates a triage plan detailing labels and assignees (dry-run stops here)
4. Worker executes the plan by invoking `gh issue edit` for each issue
5. Verifier checks if any issue remains with "needs-triage" label
6. If 0 remaining -> update STATE.md, post Slack update, complete
7. If issues remain -> iterate until max_iterations or budget exhausted
```

### Dry Run

```bash
claude /loop daily-triage --dry-run
```

Shows the issues fetched, proposed labels, and assignee recommendations without modifying any GitHub issues or writing files.

### One-Shot Run

```bash
claude /loop daily-triage
```

Executes the triage loop once. Updates the GitHub issues directly and writes the triage logs.

---

## What "Done" Means

The loop is **COMPLETE** when:
- No open issues carry the `needs-triage` label (or the designated untriaged marker).
- All processed issues have appropriate labels and assigned developers.
- `STATE.md` and `state.json` are updated with the run statistics.

The loop is **BLOCKED** when:
- Triage limits (`max_iterations: 5`) are reached with untriaged issues remaining.
- GitHub API rate limits are hit or the GitHub CLI fails.
- The budget cap ($1.00) is exceeded.

---

## Scoping Rules

- **Write access:** Local loop state and logs (`.loops/daily-triage/**`).
- **Read access:** Repository triage rules (`triage-rules.md` or `.github/triage-rules.md`).
- **Never touch:** Codebases (`src/**`), tests (`test/**`), configuration files, or deployment pipelines.
