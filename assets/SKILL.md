---
name: skill-writer
description: >
  Writes and refines SKILL.md files for AI agents. Trigger on "make a skill",
  "write agent instructions", "package this as a skill". Do NOT use for READMEs,
  docs, or non-agent writing.
dependencies: none
---

# Skill Writer

A meta-skill for writing, structuring, and refining `skill.md` files — the core artifact that gives AI agents specialized knowledge and repeatable workflows. In the Loop Engineering ecosystem, skills define *what the agent knows how to do*, while `LOOP.md` defines *what the agent should do* and when. Use this skill to produce skill files that are well-scoped, reliably triggered, and immediately actionable.

---

## When to Use This Skill

Use this skill when the user wants to:
- Create a new skill file from scratch
- Improve or audit an existing skill file
- Package a workflow or conversation pattern into a reusable skill
- Understand how to structure capabilities for Claude agents
- Test whether a skill's description will trigger correctly

Do NOT use this skill for:
- General markdown documentation (README, wikis, help centers)
- System prompts not packaged as skills
- MCP server configuration or tool definitions
- Non-agent instruction writing (style guides, SOPs for humans)

---

## Quick Reference: Core Skill Objects

Before writing any skill, understand these building blocks:

| Object | What it is |
|---|---|
| `SKILL.md` | Required entry point. YAML frontmatter + markdown instructions. |
| `description` | The trigger field. Claude reads this to decide whether to invoke the skill. |
| `references/` | Optional subfolder for deep-dive docs loaded on demand. |
| `scripts/` | Optional executable code for deterministic sub-tasks. |
| `assets/` | Optional templates, fonts, or files used in output. |
| `name` | Human-friendly identifier, ≤ 64 characters. |

**Folder structure:**

```
my-skill/
├── SKILL.md              ← Required
├── references/           ← Optional: deep-dive docs
│   └── advanced.md
├── scripts/              ← Optional: executable helpers
│   └── process.py
└── assets/               ← Optional: templates and files
    └── template.docx
```

**Distribution:** zip the folder (not loose files):

```
my-skill.zip
└── my-skill/
    ├── SKILL.md
    └── ...
```

Skills use **progressive disclosure**: Claude reads metadata first (name + description), then the `SKILL.md` body, then bundled resources — loading only what the task needs.

---

## Workflow: Write a New Skill from Scratch

1. **Capture intent** — answer (or ask the user) these questions before writing:
   - What specific, repeatable task should this skill handle?
   - What phrases or contexts should trigger it?
   - What does a good output look like? (format, length, structure)
   - What should the skill explicitly *not* do?
   - Are there scripts, templates, or reference files to bundle?
   - If the user has an existing workflow or conversation showing the desired behavior, extract the pattern from it first.

2. **Write the description first** — draft the `description` field before the body. See "Decision Rules" below for what makes a strong description.

3. **Write a structural overview** — before workflows, orient the model with a quick-reference table of core objects, key files, or entry points in the skill's domain.

4. **Document workflows, not features** — write *how to complete a task*, not *what the skill contains*. Each major workflow gets its own numbered section.

5. **Add if/then decision rules** — explicit branching logic reduces ambiguity. Cover common forks the agent will face.

6. **Write a concrete example** — minimum one worked example with realistic input, numbered steps, and actual output (not just a description of output).

7. **Add guardrails** — define what the skill should not do and known failure modes.

8. **Manage length** — keep `SKILL.md` under 500 lines. Offload deep content to `references/` with pointers explaining when to read each file.

9. **Run the quality checklist** before finalizing.

---

## Workflow: Audit and Improve an Existing Skill

1. Read the existing `SKILL.md` in full.
2. Check each item in the Quality Checklist below and note any failures.
3. Test the description against the trigger test table in "Description Optimization."
4. Rewrite weak sections; do not just append. The goal is a coherent, minimal file — not a longer one.
5. Verify all referenced files (`references/`, `scripts/`, `assets/`) actually exist.

---

## Decision Rules

**For the description field:**
- If the domain has common synonyms → include them ("skill", "agent instructions", "workflow package")
- If the skill is narrow → add explicit exclusions to prevent overtriggering ("Do NOT use for...")
- If trigger phrases are predictable → list them verbatim ("help me make a skill", "write instructions for my agent")
- If the description exceeds 200 characters → trim by cutting adjectives, not nouns or trigger contexts
- Always start with an active verb: "Writes...", "Converts...", "Generates...", "Applies..."

**For the skill body:**
- If the user hasn't named their trigger phrases → ask before writing the description
- If the skill body is approaching 500 lines → split into `references/` subfolder now, not later
- If the user provides a conversation showing the desired behavior → extract the pattern first, then formalize
- If a workflow has more than 7 steps → break it into sub-workflows with their own headings
- If a step can fail silently → add an explicit error-handling rule in Decision Rules or Guardrails
- If no output format is specified in the skill → default to Markdown
- If the task requires sequential steps → number them; if it presents alternatives → use if/then rules

**For reference files:**
- If a reference file exceeds 300 lines → add a table of contents at the top
- Always explain *when* to read each reference file, not just what it contains

**For loop-integrated skills:**
- If the skill is for a loop with `file_scope` → document which files the skill's knowledge covers and ensure alignment with the loop's allowlist
- If the skill references tools → cross-reference with the loop's `tools:` allowlist in LOOP.md
- If the skill has a verifier role → separate "what to know" from "how to verify" — the Verifier agent gets a fresh context
- If the skill will be used by the Planner agent → focus on planning heuristics and decision criteria
- If the skill will be used by the Worker agent → focus on execution steps and tool usage patterns
- If no LOOP.md exists alongside the skill → treat it as a standalone reusable skill in `skills/`

---

## Example: Writing a Skill from Scratch

**User request:** "I want a skill that helps Claude write SQL queries from plain English descriptions of what I need."

**Steps Claude takes:**

1. Captures intent: task = SQL generation; triggers = "write a query", "SQL for...", "query that..."; output = runnable SQL + brief explanation; not in scope = schema design, migrations, ORM code.

2. Writes description:
   ```
   Generates SQL queries from plain-English descriptions. Trigger on "write a query",
   "SQL for...", "query that does X", or any request to retrieve/transform database data.
   Do NOT use for schema design, migrations, or ORM code.
   ```

3. Writes quick-reference overview: lists supported SQL dialects, key objects (tables, views, CTEs), and the expected input format (table names + desired output).

4. Documents two workflows: "Generate a new query" and "Explain or fix an existing query."

5. Adds decision rules: if no dialect specified → default to PostgreSQL; if table names are ambiguous → ask before generating; if query would be destructive (DELETE, DROP) → confirm first.

6. Writes a concrete example with actual input ("Get all orders placed in the last 30 days with total > $100") and actual output (a working SQL snippet).

7. Adds guardrails: do not assume column names not provided; always include a `LIMIT` clause unless the user explicitly removes it; note when a query may be slow.

**Output:** A complete `SKILL.md` ready to drop into a `sql-writer/` folder.

---

## SKILL.md Structure Reference

### YAML Frontmatter

```yaml
---
name: My Skill Name           # Human-friendly, ≤ 64 characters
description: >                # ≤ 200 characters. THE trigger field.
  Active verb + what it does + trigger phrases + explicit exclusions.
dependencies: python>=3.8     # Optional. Required packages.
---
```

### Markdown Body Sections

| Section | Purpose | Required? |
|---|---|---|
| Overview | One paragraph: what the skill does and why | Recommended |
| When to Use / Scope | Explicit trigger conditions + out-of-scope cases | Recommended |
| Quick Reference | Core objects, key files, mental model table | If domain is complex |
| Workflow(s) | Step-by-step task guides, one per major task | Central — always include |
| Decision Rules | If/then guidance for forks and edge cases | Highly recommended |
| Example | Full worked input → steps → output | Highly recommended |
| Guardrails | What NOT to do; known failure modes | Recommended |
| Reference Pointers | What's in `references/` and when to read it | If using references/ |
| Security | Credential handling, side effects, review notes | Recommended |

---

## Description Optimization

Test the description against these prompt types before finalizing:

| Prompt type | Should trigger? |
|---|---|
| Exact use-case from the skill | Yes |
| Related task using different words | Yes |
| Completely unrelated task | No |
| Ambiguous edge case | Depends — refine if unclear |

If undertriggering → add synonyms, user phrases, and domain keywords.
If overtriggering → add explicit "Do NOT use for..." exclusions.

**Weak description:**
> Apply brand guidelines to documents.

**Strong description:**
> Applies Acme Corp brand guidelines (colors, fonts, logo rules) to any presentation, doc, or marketing asset. Trigger on "make this on-brand", "apply brand", or any external-facing content creation. Do NOT use for internal memos.

---

## Quality Checklist

Before finalizing any skill, verify:

- [ ] `name` is ≤ 64 characters and human-friendly
- [ ] `description` is ≤ 200 characters, starts with an active verb, includes trigger phrases, and has explicit exclusions
- [ ] Body opens with a one-paragraph overview
- [ ] Quick-reference section orients the model before any workflow
- [ ] Every major workflow is documented step-by-step
- [ ] At least one if/then decision rules section exists
- [ ] At least one concrete, fully worked example (realistic input → actual output) is included
- [ ] Out-of-scope cases are listed explicitly ("Do NOT use for...")
- [ ] Guardrails cover what NOT to do and known failure modes
- [ ] All files referenced in `SKILL.md` actually exist in the folder
- [ ] `SKILL.md` is under 500 lines (or has reference pointers to offload depth)
- [ ] The folder name matches the `name` field
- [ ] Packaging: the ZIP contains the folder, not loose files

---

## Full Template

See `assets/skill-template.md` for the complete starter template. Copy it, fill in the bracketed fields, and remove any sections marked "Only include if...".

The template includes these sections in order:

| Section | Required? |
|---|---|
| YAML Frontmatter (`name`, `description`, `dependencies`) | Yes |
| Overview paragraph | Recommended |
| When to Use / Scope | Recommended |
| Quick Reference | If domain is complex |
| Workflow(s) | Always |
| Decision Rules | Highly recommended |
| Example | Highly recommended |
| Guardrails | Recommended |
| Security and Best Practices | Recommended |
| Reference Files | If using `references/` |

---

## Where Skills Live

### In This Repo

| Location | Purpose |
|---|---|
| `loops/<loop-name>/SKILL.md` | Loop-specific skill — bundled with its loop definition |
| `skills/` | Reusable shared skills — referenced by multiple loops |

### In Other Environments

| Environment | Path |
|---|---|
| Claude Code | `~/.claude/skills/` or project-local `skills/` |
| Claude.ai | Upload via Customize → Skills |
| API | Pass as context or inject via system prompt |

---

## Reference Files

Use existing skills in this repo as templates when writing new ones:

- `skills/test-runner.md` — Verification-focused skill. Read when writing skills for loops with `verifier.type: test_suite`.
- `skills/pr-reviewer.md` — Review-oriented skill. Read when the skill involves code quality judgment.
- `skills/git-committer.md` — Tool-gated skill. Read when the skill needs approval gates on destructive actions.
- `skills/issue-triager.md` — Classification skill. Read when the skill involves labeling or categorizing inputs.
- `skills/doc-writer.md` — Content-generation skill. Read when the skill produces documentation artifacts.
- `skills/cost-reporter.md` — Read-only observability skill. Read when the skill queries data without modifying files.
