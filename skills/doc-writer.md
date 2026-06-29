---
name: doc-writer
description: >
  Generates and updates markdown documentation, keeping it in sync with code. Trigger on "update docs", "write README", or "document this feature". Do NOT use for writing executable code.
---

# Document Writer

This skill allows the agent to produce high-quality, structured markdown documentation, ensuring that project specs, READMEs, and changelogs remain accurate and up-to-date as the codebase evolves.

---

## When to Use This Skill

Use this skill when:
- The `doc-sync` or `changelog-drafter` loop runs.
- Code has changed and the corresponding documentation is now stale.
- You need to generate API references from source code.

Do NOT use this skill for:
- Writing or refactoring source code.
- Making architectural decisions.

---

## Workflow: Update Stale Documentation

1. **Analyze code changes**: Review the git diff to understand what feature was added or modified.
2. **Locate docs**: Find the relevant markdown files (e.g., `README.md`, `docs/api.md`).
3. **Identify stale sections**: Determine which paragraphs or code examples are no longer accurate.
4. **Draft updates**: Rewrite the text and code snippets to match the new reality.
5. **Apply changes**: Save the updated markdown file.

---

## Decision Rules

- If updating a changelog → group changes by `Added`, `Changed`, `Deprecated`, `Removed`, `Fixed`, and `Security`.
- If documenting an API → always include a code example showing how to call it.
- If unsure how a new feature works → flag it with a TODO comment rather than guessing.

---

## Example

**Input:** "Update the API docs to reflect that `getUser` now takes an optional `includeRoles` boolean."

**Steps the agent takes:**
1. Opens `docs/api.md`.
2. Locates the `getUser(id)` section.
3. Updates the signature to `getUser(id, includeRoles = false)`.
4. Adds a description of the new parameter.

**Output:**
Updates the file and reports:
"Updated `docs/api.md` to include the `includeRoles` parameter in the `getUser` documentation."

---

## Guardrails

- Do NOT delete existing documentation unless you are certain the feature was completely removed.
- Always use standard GitHub Flavored Markdown (GFM).
- Ensure code examples in the documentation are syntactically valid.
