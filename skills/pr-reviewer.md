---
name: pr-reviewer
description: >
  Reviews pull requests for quality, style, and correctness. Trigger on "review PR", "check diff", or before merging. Do NOT use for making commits or writing code.
---

# PR Reviewer

This skill enables the agent to act as a rigorous code reviewer, analyzing diffs to ensure quality, security, and adherence to project standards before code is merged.

---

## When to Use This Skill

Use this skill when:
- A loop produces a PR that needs automated review.
- You are asked to audit a specific commit or diff.
- A human requests a code review on their branch.

Do NOT use this skill for:
- Actually writing the code to fix the issues found.
- Running tests (use `test-runner` instead).

---

## Workflow: Review a Pull Request

1. **Fetch the diff**: Obtain the diff between the feature branch and the base branch.
2. **Analyze for correctness**: Look for logical errors, off-by-one mistakes, or unhandled edge cases.
3. **Analyze for style**: Ensure the code matches the surrounding conventions.
4. **Check for missing tests**: Identify if new logic lacks test coverage.
5. **Format feedback**: Group comments by file and severity (Blocking vs. Nitpick).

---

## Decision Rules

- If secrets or API keys are found in the diff → immediately block the PR and flag as CRITICAL.
- If changes involve database schema migrations → require explicit human approval.
- If the PR is massive (>500 lines) → suggest breaking it down into smaller PRs.

---

## Example

**Input:** "Review the changes in branch `feature/auth-refactor`."

**Steps the agent takes:**
1. Gets the diff for the branch.
2. Identifies a missing `await` on an async database call.
3. Notes that a new function was added without corresponding tests.

**Output:**
```markdown
## PR Review

**Status**: ❌ Request Changes

### Blocking Issues
- `src/auth.js:L45` - Missing `await` before `db.query()`. This will return a Promise instead of the user object.
- `src/auth.js` - Added `verifyToken` but no tests were added to `auth.test.js`.

### Nitpicks
- `src/utils.js:L12` - Variable `x` could have a more descriptive name.
```

---

## Guardrails

- Do NOT approve a PR that contains obvious security flaws.
- Always provide actionable feedback (explain *why* something is wrong).
- Do NOT make commits directly to the branch while reviewing.
