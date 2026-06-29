---
name: git-committer
description: >
  Creates atomic commits, writes conventional messages, and handles git workflows. Trigger on "commit changes", "push branch", or when done. Do NOT use for deciding what code to write.
---

# Git Committer

This skill enables the agent to interact safely with version control, ensuring that changes are grouped logically into atomic commits with descriptive messages, and that destructive actions pass approval gates.

---

## When to Use This Skill

Use this skill when:
- The Worker agent has finished a step and needs to save its progress.
- A loop needs to open a Pull Request.

Do NOT use this skill for:
- Running tests (use `test-runner`).
- Deciding what changes to make (that is the Planner/Worker's job).

---

## Quick Reference

| Action | Command | Notes |
|--------|---------|-------|
| Atomic Commit | `git add <file> && git commit -m "msg"` | One logical change per commit. |
| Revert | `git revert HEAD` | Undo the last atomic commit. |

---

## Workflow: Create an Atomic Commit

1. **Review changes**: Check `git status` and `git diff` to see what was modified.
2. **Stage specific files**: Only stage the files related to the specific logical change (avoid `git add .` if multiple unrelated files changed).
3. **Format message**: Use conventional commits (e.g., `fix:`, `feat:`, `chore:`, `docs:`).
4. **Commit**: Execute the commit.

---

## Decision Rules

- If multiple independent issues were fixed → create separate commits for each.
- If asked to push to `main` or `master` → STOP and require human approval, unless explicitly authorized in `LOOP.md`.
- If asked to `git push --force` → STOP and require human approval.

---

## Example

**Input:** "I fixed the navbar alignment in `header.css` and updated the readme."

**Steps the agent takes:**
1. Stages `header.css`.
2. Commits with message `fix(ui): align navbar items`.
3. Stages `README.md`.
4. Commits with message `docs: update setup instructions`.

**Output:**
```bash
git add header.css
git commit -m "fix(ui): align navbar items"
git add README.md
git commit -m "docs: update setup instructions"
```

---

## Guardrails

- Do NOT use `git commit -am` or `git add .` unless you are absolutely sure every changed file belongs in the same commit.
- Never force push without explicit human consent.
