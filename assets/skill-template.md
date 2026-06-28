---
name: [Skill Name]
description: >
  [Active verb + what it does] + [trigger phrases] + [explicit exclusions].
  Do NOT use for [out-of-scope cases].
---

# [Skill Name]

[One paragraph: what this skill enables the agent to do and why it matters.]

---

## When to Use This Skill

Use this skill when:
- [Trigger condition 1]
- [Trigger condition 2]

Do NOT use this skill for:
- [Out-of-scope case 1]
- [Out-of-scope case 2]

---

## Quick Reference

[Table or list of core objects, key files, or entry points in this domain.]

| Term | What it is |
|---|---|
| [Object] | [Definition] |
| [Object] | [Definition] |

---

## Workflow: [Main Task Name]

1. [Step 1]
2. [Step 2]
3. [Step 3]

---

## Workflow: [Secondary Task Name]

1. [Step 1]
2. [Step 2]

---

## Decision Rules

- If [condition] → [action]
- If [condition] → [action]
- If no [X] is specified → default to [Y]
- If a step fails → [error handling instruction]

---

## Example

**Input:** "[Realistic user request]"

**Steps the agent takes:**
1. [Concrete step]
2. [Concrete step]
3. [Concrete step]

**Output:**
[Actual output snippet — not just a description of it]

---

## Guardrails

- Do NOT [prohibited action]
- Do NOT [prohibited action]
- Always [required behavior]
- If uncertain about [X] → ask before proceeding

---

## Security and Best Practices

- Never hardcode API keys, passwords, or tokens in any skill file
- Use MCP connections for external service access rather than embedding credentials
- Review any downloaded skill before enabling it
- Keep scripts deterministic and side-effect-free where possible
- Test after each significant change rather than building the full skill at once

---

## Reference Files

*(Only include this section if you have a `references/` subfolder)*

- `references/[filename].md` — [What it contains]. Read when [specific condition].
