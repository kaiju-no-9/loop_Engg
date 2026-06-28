---
name: changelog-drafter-skill
description: >
  Scans git history and pull requests to draft release changelogs.
  Trigger on "draft release notes", "update changelog", or "generate release log".
  Do NOT use for changing source code.
---

# Changelog Drafter Skill

An agent skill for parsing git logs, extracting semantic details from commit histories and pull requests, categorizing changes according to standard release formats, and updating the project's `CHANGELOG.md`. The agent respects the "Keep a Changelog" formatting guidelines, grouping updates logically. It never invents updates and never modifies source files.

---

## When to Use This Skill

Use this skill when:
- A new release version tag has been created and needs documentation.
- The project `CHANGELOG.md` needs to be updated with recent features and fixes prior to a release.
- A summary of user-facing changes is required for team notifications or stakeholders.
- Semantic commit messages need parsing to document features vs fixes.

Do NOT use this skill for:
- Writing or refactoring source code (use `code-repair` instead).
- Writing comments or responses to users.
- Modifying project version files (e.g. `package.json` version numbers) unless explicit tasks allow it.
- Updating dependencies or test files.

---

## Quick Reference

### Keep a Changelog Standard Categories

| Category | Description |
|---|---|
| **Added** | For new features. |
| **Changed** | For changes in existing functionality. |
| **Deprecated** | For soon-to-be removed features. |
| **Removed** | For now removed features. |
| **Fixed** | For any bug fixes. |
| **Security** | In case of vulnerability fixes. |

---

## Workflow: Draft Release Notes

1. **Detect range of changes** — Run git command to identify the latest version tag and compare it against the preceding tag:
   ```bash
   git describe --tags --abbrev=0
   ```
   Determine the range (e.g. `v1.0.0...v1.1.0` or `v1.0.0...HEAD`).
2. **Retrieve commit logs** — Fetch the commits in that range, including merge commit descriptions:
   ```bash
   git log --oneline --cherry-pick v1.0.0...HEAD
   ```
3. **Parse and categorize changes** — Read each commit/PR:
   - Identify categories (Added, Changed, Fixed, Security) based on conventional commit prefixes (e.g., `feat:`, `fix:`, `security:`).
   - Group identical updates and format them as bullet points.
   - Clean up technical jargon into readable descriptions.
   - Reference PR numbers or commit hashes where relevant.
4. **Draft markdown entry** — Construct the release block using standard markdown:
   ```markdown
   ## [1.1.0] - 2026-06-28
   ### Added
   - Support for new authentication adapter.
   ### Fixed
   - Corrected token expiration timeout bug (#104).
   ```
5. **Update CHANGELOG.md** — Open `CHANGELOG.md` and insert the new release block directly below the main header:
   - Respect existing file spacing.
   - Update internal links/anchors at the bottom of the file mapping tag ranges.
6. **Verify updates** — Run checks to verify format integrity.
7. **Commit atomically** — Commit modifications: `docs(changelog): draft release notes for v1.1.0`.

---

## Decision Rules

- **If no previous tag exists** → Gather git logs from the very first commit to HEAD. Write the block as the initial release `[1.0.0]`.
- **If a commit doesn't follow conventional formats** → Evaluate its content. If it modifies tests/docs, categorize as `Changed` or skip if it's purely internal refactoring.
- **If a security patch is detected** → Categorize strictly under `Security` and place it at the top of the release notes.
- **If no changes are detected** → Do not modify the file. Exit with a status of `COMPLETE` and record `commits_analyzed: 0`.

---

## Example

**Input:**
Commits retrieved between `v1.0.0` and `HEAD`:
```
a1b2c3d feat(auth): add OAuth2 provider configuration (#108)
e5f6g7h fix(api): handle connection timeouts on request retry (#105)
i9j0k1l docs: refine readme instruction details
```

**Steps the agent takes:**
1. Categorizes `feat(auth)` as **Added**: "OAuth2 provider configuration (#108)".
2. Categorizes `fix(api)` as **Fixed**: "Handle connection timeouts on request retry (#105)".
3. Ignores doc improvement `docs:` since it is internal maintenance, or adds it to **Changed** if it represents an API guide update.
4. Formulates markdown output:
   ```markdown
   ## [1.1.0] - 2026-06-28
   ### Added
   - OAuth2 provider configuration (#108).
   ### Fixed
   - Handle connection timeouts on request retry (#105).
   ```
5. Prepends block to `CHANGELOG.md`.

**Output in STATE.md:**
```yaml
last_run: 2026-06-28T11:00:00Z
status: COMPLETE
commits_analyzed: 3
changelog_drafted: true
```

---

## Guardrails

- Never invent or fabricate features. If a commit description is vague, look at the code diff to verify the actual change.
- Do NOT include internal developer notes, developer names, or git hashes in the final changelog text (use clean PR references instead).
- Never modify files outside of `CHANGELOG.md` and release drafts directory.
