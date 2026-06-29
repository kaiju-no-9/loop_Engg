---
name: issue-triager
description: >
  Reads, labels, and categorizes GitHub issues. Trigger on "triage issues", "label this bug", or "categorize feedback". Do NOT use for fixing the issues or writing code.
---

# Issue Triager

This skill allows the agent to organize project backlogs by reading new issues, inferring their domain, applying appropriate labels, and suggesting assignees.

---

## When to Use This Skill

Use this skill when:
- The `daily-triage` loop runs to organize incoming issues.
- You need to classify a large batch of user feedback.

Do NOT use this skill for:
- Writing code to resolve the issue.
- Closing issues without human authorization.

---

## Workflow: Triage an Issue

1. **Read the issue**: Analyze the title and body of the issue.
2. **Determine type**: Is it a Bug, Feature Request, Question, or Documentation update?
3. **Assess priority**: 
   - P0: Site down, data loss, security flaw.
   - P1: Core feature broken for many users.
   - P2: Standard bug or feature request.
   - P3: Minor cosmetic issue or nitpick.
4. **Identify domain**: Determine which parts of the codebase are affected (e.g., frontend, database, API).
5. **Apply labels**: Output the appropriate labels to be applied.

---

## Decision Rules

- If the issue contains a stack trace → label as `bug`.
- If the issue mentions security or vulnerabilities → label as `security`, `P0`, and escalate immediately.
- If the issue is vague and lacks reproduction steps → label as `needs-info`.

---

## Example

**Input:** "Triage this issue: 'Login button is overlapping with the logo on mobile screens.'"

**Steps the agent takes:**
1. Reads the description.
2. Identifies it as a visual defect on mobile.
3. Determines it's not blocking core functionality but looks bad.

**Output:**
```markdown
## Triage Result

**Labels to apply**: `bug`, `ui/ux`, `mobile`
**Priority**: `P2`
**Suggested Action**: Assign to frontend team.
```

---

## Guardrails

- Do NOT close issues just because they seem low priority.
- Always err on the side of caution with security issues (assume P0).
