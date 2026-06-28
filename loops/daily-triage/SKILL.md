---
name: daily-triage-skill
description: >
  Scans, labels, and recommends owners for incoming GitHub issues. Trigger on
  "triage open issues", "label new bugs", or "assign maintainers". Do NOT use
  for writing code or closing issues.
---

# Daily Triage Skill

An agent skill for automated categorization, prioritization, labeling, and owner assignment recommendations for GitHub issues. The agent utilizes repository-specific triage rules and developer mapping, ensuring incoming bug reports and feature requests are directed to the right maintainers with correct metadata. It never closes issues on its own and never overrides active developer assignments.

---

## When to Use This Skill

Use this skill when:
- Incoming GitHub issues need daily triage to prevent backlog accumulation.
- Bugs need prioritization based on severity and impact metrics.
- Issues need routing to specific teams or code owners based on file components.
- Standard issue labels (e.g., `bug`, `feature`, `documentation`, `ci`) must be applied consistently.

Do NOT use this skill for:
- Writing source code or fixing reported bugs (use `ci-sweeper` or `code-repair` instead).
- Closing GitHub issues autonomously (closing always requires human validation).
- Engaging in conversations with users or writing comments in issues.
- Modifying repository configuration or CI settings.

---

## Quick Reference

| Term / Concept | Description |
|---|---|
| **Untriaged Issue** | Any issue labeled `needs-triage` or missing categorization labels. |
| **Component Label** | Labels designating codebase areas (e.g., `area:auth`, `area:ui`, `area:db`). |
| **Priority Level** | Categorization of impact: `P0` (blocker/hotfix), `P1` (critical), `P2` (standard), `P3` (minor). |
| **Owner Recommendation** | Assigning or suggesting developers based on CODEOWNERS mapping. |
| **Rate Limit Handoff** | Action taken if GitHub API rate limits are encountered. |

---

## Workflow: Triage GitHub Issues

1. **Fetch untriaged issues** — Run GitHub CLI command to retrieve open issues labeled with `needs-triage` or those lacking categorization:
   ```bash
   gh issue list --state open --label "needs-triage" --json number,title,body,labels,author
   ```
2. **Analyze each issue** — For each issue:
   - Read the title and body description to identify the core problem.
   - Detect components involved (e.g., database, frontend, API, auth) by analyzing keywords or stack traces.
   - Determine severity:
     - **P0**: Security vulnerabilities, system outages, completely broken critical paths (auth, billing).
     - **P1**: Broken non-blocking features, performance regressions.
     - **P2**: Minor feature requests, usability issues, missing documentation.
     - **P3**: Cosmetic changes, typos.
3. **Map to area ownership** — Read the project `triage-rules.md` (or CODEOWNERS) to identify which engineer owns the identified components.
4. **Formulate label/assignment plan** — Draft the metadata to apply:
   - Identify primary label: `bug`, `enhancement`, `docs`, `chore`.
   - Identify component label: `area:<component>`.
   - Identify priority label: `priority:p0` through `priority:p3`.
   - Identify owner assignment: `assignee:<username>`.
5. **Apply triage update** — Modify the issue using the GitHub CLI, applying labels and removing `needs-triage`:
   ```bash
   gh issue edit <issue_number> --add-label "bug,area:auth,priority:p1" --remove-label "needs-triage" --add-assignee "nishchaykumar"
   ```
6. **Log execution** — Record the processed issue number, action taken, and labels applied in `STATE.md`.

---

## Decision Rules

- **If the issue body is empty or lacks description** → Apply the `needs-info` label and request description from the reporter via a standardized message, but do not close.
- **If the issue is a duplicate** → Search recent issues (`gh issue list --state all --limit 100`) to find matching reports. If a duplicate is found, apply `duplicate` label and link it to the original issue, leaving it for human verification before closing.
- **If the issue reports a security vulnerability** → Apply `security` and `priority:p0` immediately, do NOT discuss publicly, and notify the security team.
- **If the owner assignment is ambiguous** → Recommending assignee instead of directly assigning; assign to the Lead Maintainer as fallback.
- **If GitHub API rate limit is reached** → Stop processing, save progress to `STATE.md`, set `waiting_for_human: true` and write the reason as "API Rate Limit hit".

---

## Example

**Input:**
Untriaged issue retrieved:
```json
{
  "number": 104,
  "title": "Login page throws 500 error when clicking Login button",
  "body": "Steps to reproduce:\n1. Go to /login\n2. Click button\n3. Console shows: TypeError: Cannot read properties of undefined (reading 'jwt')",
  "labels": [{"name": "needs-triage"}]
}
```

**Steps the agent takes:**
1. Parses issue #104.
2. Identifies:
   - Core component: Authentication / login (`area:auth`)
   - Issue type: `bug`
   - Severity: critical login failure prevents access → `priority:p0`
   - Owner from code mapping: @nishchaykumar handles auth.
3. Formulates action:
   - Add labels: `bug`, `area:auth`, `priority:p0`
   - Remove label: `needs-triage`
   - Assignee: `nishchaykumar`
4. Executes:
   ```bash
   gh issue edit 104 --add-label "bug,area:auth,priority:p0" --remove-label "needs-triage" --add-assignee "nishchaykumar"
   ```
5. Updates STATE.md run logs.

**Output in STATE.md:**
```yaml
last_run: 2026-06-28T08:00:00Z
status: COMPLETE
issues_found: 1
issues_triaged: 1
issues_remaining: 0
```

---

## Guardrails

- Do NOT post automated comments on issues unless requesting missing info.
- Do NOT close issues under any circumstances.
- Do NOT modify issues that already have developer assignments or custom labels (leave them as triaged).
- Do NOT assign issues to users who are not listed in the repository's contributor/maintainer whitelist.
- Respect API budgets and call rate limits strictly.
