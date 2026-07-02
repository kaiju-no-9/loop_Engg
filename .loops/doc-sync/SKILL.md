---
name: doc-sync-skill
description: >
  Scans git diffs for code changes and updates corresponding markdown docs.
  Trigger on "sync docs", "update documentation", or "fix README". Do NOT use
  for editing source code or tests.
---

# Documentation Sync Skill

An agent skill for scanning codebase updates, finding documentation that has become stale, and revising specifications, READMEs, and tutorials to align with the source code. The agent reads code signatures, docstrings, and inline comments, translates technical details into clear developer-facing documentation, and validates formatting and link integrity. It never alters application logic or test files.

---

## When to Use This Skill

Use this skill when:
- Function signatures, API endpoints, or database structures change, requiring updates to documents.
- The repository README needs updating to reflect new features, CLI commands, or installation steps.
- Code blocks inside guides or tutorials must match the actual source files.
- Documentation drift is detected by the CI pipeline.

Do NOT use this skill for:
- Writing or refactoring source code (use `code-repair` instead).
- Fixing or updating test suites (use `ci-sweeper` instead).
- Writing marketing copies or content unrelated to the technical codebase.
- Updating dependencies, lockfiles, or configurations.

---

## Quick Reference

| Concept | Description |
|---|---|
| **API Drift** | Discrepancy between code declarations and what is documented in Markdown specs. |
| **Docstrings** | Inline documentation inside source files (`/** ... */`, `"""..."""`) used as source of truth. |
| **Markdown Linting** | Ensuring doc formatting respects Markdown specifications (headers, lists, tables). |
| **Broken Link Check** | Validating internal and external URLs inside documents. |

---

## Workflow: Sync Documentation

1. **Extract changes** — Retrieve the list of modified source files by running git diff against the target branch (e.g. `origin/main`):
   ```bash
   git diff --name-only origin/main | grep -E '\.(js|ts|py|go|rs|java)$'
   ```
2. **Identify stale documents** — For each modified source file:
   - Identify corresponding markdown documents (e.g., if `src/auth.js` changes, check `docs/auth.md` or `docs/security.md`).
   - Read the git diff of the source file to understand the change:
     ```bash
     git diff origin/main -- <source_file>
     ```
   - Compare the updated function/class declarations with the declarations documented in the markdown files.
3. **Draft documentation updates** — For each documentation gap:
   - Formulate clear, concise updates that match the project's writing style.
   - Ensure parameter names, return types, and exceptions match the code exactly.
   - Update code blocks in tutorials/examples to use the new API syntax.
4. **Apply changes** — Modify the documentation files. Ensure changes are minimal, precise, and targeted.
5. **Verify link and build integrity** — Run link checkers or documentation compile scripts:
   ```bash
   npm run docs:verify
   ```
6. **Commit atomically** — Commit doc modifications per component with a descriptive message: `docs: update auth API parameters in docs/auth.md to match JWT refactor`
7. **Log execution** — Record updated files and validation results in `STATE.md`.

---

## Decision Rules

- **If an API has been deprecated** → Mark the API as `[DEPRECATED]` in the documentation, specify the version it was deprecated in, and document the replacement API. Do not delete the documentation of the deprecated API immediately unless requested.
- **If the documentation does not exist for a new source file** → Create a new markdown file in `docs/` named after the component (e.g. `docs/new-feature.md`), populate it with standard sections (Overview, API reference, Usage examples), and add a link to it in the main table of contents/sidebar.
- **If a documentation change is ambiguous** → Flag in `STATE.md` with `waiting_for_human: true`, detailing the unresolved question (e.g., "JWT expires parameter added in auth.js; clarify if default expiration should be documented as 1h or 24h").
- **If the verifier script fails** → Roll back the last document edit, fix the formatting/link error, and re-verify.

---

## Example

**Input:**
Source code diff shows a signature change in `src/utils.js`:
```diff
- export function formatDate(date, format = 'YYYY-MM-DD') {
+ export function formatDate(date, format = 'YYYY-MM-DD', locale = 'en-US') {
```
And `docs/utils.md` still documents:
```markdown
### formatDate(date, format)
Formats a Date object or ISO string.
- `date`: Date or string
- `format`: String default YYYY-MM-DD
```

**Steps the agent takes:**
1. Scans the diff of `src/utils.js` and identifies the new parameter `locale` with default value `'en-US'`.
2. Locates `docs/utils.md` as the corresponding documentation.
3. Updates `docs/utils.md`:
   ```markdown
   ### formatDate(date, format, locale)
   Formats a Date object or ISO string.
   - `date`: Date or string
   - `format`: String default YYYY-MM-DD
   - `locale`: String default 'en-US' (new in v1.1)
   ```
4. Verifies links and build.
5. Commits change: `docs: document locale parameter for formatDate utility`.

**Output in STATE.md:**
```yaml
last_run: 2026-06-28T09:12:00Z
status: COMPLETE
docs_updated: 1
files_analyzed: 1
```

---

## Guardrails

- Never touch any source code files (`src/**`), tests, or deployment configs.
- Never document hypothetical features that have not been implemented in the source code yet.
- Never write credentials, test passwords, or private environment variables into the documentation.
- Maintain formatting standards; do not introduce broken markdown tags or invalid HTML.
