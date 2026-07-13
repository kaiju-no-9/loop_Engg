---
name: accessibility-audit-skill
description: >
  Scans frontend components for WCAG 2.1 AA violations using axe-core and applies
  minimal HTML/ARIA fixes. Trigger on "accessibility audit", "a11y scan", or "fix
  WCAG violations". Do NOT use for visual redesigns or backend changes.
---

# Accessibility Audit Skill

An agent skill for running automated accessibility scans with axe-core, interpreting WCAG 2.1 violation reports, and applying the smallest possible HTML, ARIA, or CSS changes to resolve critical and serious issues. The agent prioritizes fixes by impact severity, prefers semantic HTML over ARIA attributes, and never alters visual design intent without human approval.

---

## When to Use This Skill

Use this skill when:
- Frontend components need weekly accessibility compliance checks
- axe-core or similar tools report WCAG 2.1 AA violations that need automated remediation
- New UI components have been added without accessibility review
- A pull request introduces HTML changes that may affect screen reader compatibility

Do NOT use this skill for:
- Visual design changes (colors, layouts, typography beyond contrast fixes)
- Backend or API code modifications
- Writing new components or pages from scratch
- Manual accessibility testing or user testing coordination
- Fixing violations that require architectural changes (e.g., completely restructuring page navigation)

---

## Quick Reference

| Concept | What It Means |
|---|---|
| **WCAG 2.1 AA** | Web Content Accessibility Guidelines level AA — the standard compliance target for most organizations |
| **axe-core** | Open-source accessibility testing engine by Deque — the primary scanning tool |
| **Violation** | A specific accessibility rule failure (e.g., missing `alt` text, insufficient color contrast) |
| **Impact levels** | `critical` > `serious` > `moderate` > `minor` — always fix in this priority order |
| **ARIA** | Accessible Rich Internet Applications — attributes that supplement semantic HTML for assistive tech |
| **Semantic HTML** | Using correct HTML elements (`<button>`, `<nav>`, `<main>`) instead of generic `<div>` with ARIA roles |

### Common Violation Categories

| axe-core Rule ID | Category | Typical Fix |
|---|---|---|
| `image-alt` | Images | Add descriptive `alt` attribute |
| `button-name` | Interactive | Add accessible label (`aria-label` or visible text) |
| `color-contrast` | Visual | Adjust foreground/background color to meet 4.5:1 ratio |
| `label` | Forms | Associate `<label>` with form input via `for`/`id` |
| `link-name` | Navigation | Add text content or `aria-label` to `<a>` elements |
| `heading-order` | Structure | Fix heading hierarchy (don't skip levels) |
| `landmark-*` | Structure | Add appropriate landmark roles (`<main>`, `<nav>`, `<aside>`) |
| `aria-*` | ARIA | Fix invalid, misused, or missing ARIA attributes |

---

## Workflow: Run Accessibility Scan

1. **Determine scan target** — identify the pages or components to scan based on `file_scope` in LOOP.md:
   ```bash
   # For static HTML
   npx axe-core-cli ./public/index.html --reporter json

   # For running dev server
   npx axe-core-cli http://localhost:3000 --reporter json

   # For component-level scanning (if configured)
   npm run test:a11y -- --reporter json
   ```
2. **Parse the report** — extract each violation with its rule ID, impact level, affected elements (CSS selectors), and help URL
3. **Categorize by impact** — group violations into `critical`, `serious`, `moderate`, `minor`
4. **Deduplicate** — multiple elements may trigger the same rule; group them for batch fixes
5. **Produce fix plan** — ordered list of fixes, critical first, with the specific elements and proposed changes

---

## Workflow: Fix WCAG Violations

1. **Start with critical violations** — these prevent users from accessing content at all
2. **For each violation, determine the fix type:**
   - **Missing attribute** → add the attribute (e.g., `alt`, `aria-label`, `for`)
   - **Wrong element** → replace with semantic HTML (e.g., `<div onclick>` → `<button>`)
   - **Missing structure** → add landmarks or headings (e.g., wrap content in `<main>`)
   - **Color contrast** → adjust the CSS color values to meet WCAG AA ratio (4.5:1 for normal text, 3:1 for large text)
   - **Missing focus management** → add `tabindex`, focus styles, or keyboard handlers
3. **Apply the fix** — make the smallest possible change to the component file
4. **Commit atomically** — one commit per violation rule (may fix multiple elements):
   ```
   fix(a11y): add alt text to product images — resolves axe image-alt violation
   ```
5. **Re-scan** — run axe-core again to confirm the violation is resolved
6. **Iterate** — move to the next violation in priority order

---

## Workflow: Triage Unfixable Violations

1. **Identify unfixable violations** — a violation is unfixable by this loop if:
   - Fixing it requires a visual design change that alters the intended look (beyond contrast adjustments)
   - The violation is in a third-party component the project doesn't control
   - The fix requires JavaScript behavior changes that go beyond minimal ARIA additions
   - The violation is a false positive from axe-core (rare but possible)
2. **Document in STATE.md** — add each unfixable violation to `violations_remaining` with a reason
3. **Set `waiting_for_human: true`** — if only unfixable violations remain
4. **Continue fixing fixable violations** — don't stop the loop because some violations are unfixable

---

## Decision Rules

- If the violation is `critical` or `serious` → always attempt a fix before moving to lower-impact issues
- If a `<div>` or `<span>` has an `onClick` handler → replace with `<button>` (semantic HTML preferred over `role="button"`)
- If an image is decorative (no meaningful content) → use `alt=""` (empty alt), not `aria-hidden`
- If an image conveys information → write a concise, descriptive `alt` text based on surrounding context
- If color contrast fails → adjust the *foreground* color first; only adjust background if foreground changes would conflict with the design system
- If a form input lacks a visible label and one can't be added → use `aria-label` as a fallback
- If heading levels are skipped (e.g., `<h1>` → `<h3>`) → insert the missing level or adjust the hierarchy
- If a component uses ARIA `role` but the semantic HTML equivalent exists → prefer the semantic element
- If a fix requires changing more than 15 lines in a single file → flag in STATE.md as `needs_human_review`
- If a violation is on a third-party component → log it as unfixable, do not attempt to patch `node_modules`
- If no violations are found when the loop starts → set status to `COMPLETE` with `violations_fixed: 0` and exit cleanly

---

## Example

**Input:** axe-core JSON report showing 4 violations

```json
{
  "violations": [
    {
      "id": "image-alt",
      "impact": "critical",
      "nodes": [
        { "target": ["img.hero-banner"] },
        { "target": ["img.product-thumb:nth-child(3)"] }
      ]
    },
    {
      "id": "color-contrast",
      "impact": "serious",
      "nodes": [
        { "target": [".subtitle-text"] }
      ]
    },
    {
      "id": "button-name",
      "impact": "serious",
      "nodes": [
        { "target": ["button.icon-btn-close"] }
      ]
    },
    {
      "id": "heading-order",
      "impact": "moderate",
      "nodes": [
        { "target": ["h3.section-title"] }
      ]
    }
  ]
}
```

**Steps the agent takes:**

1. Prioritizes by impact: `image-alt` (critical) → `color-contrast` (serious) → `button-name` (serious) → `heading-order` (moderate)

2. Fixes `image-alt` on `img.hero-banner`:
   - Reads surrounding context in the component → the image is a promotional banner for "Summer Sale"
   - Adds `alt="Summer Sale — 30% off all items this weekend"`
   - Fixes `img.product-thumb:nth-child(3)` similarly
   - Commit: `fix(a11y): add descriptive alt text to hero banner and product thumbnails`

3. Fixes `color-contrast` on `.subtitle-text`:
   - Current: `color: #999` on `background: #fff` → ratio 2.85:1 (fails AA)
   - Changes to: `color: #595959` → ratio 7.0:1 (passes AA)
   - Commit: `fix(a11y): improve subtitle text contrast from 2.85:1 to 7.0:1`

4. Fixes `button-name` on `button.icon-btn-close`:
   - Button contains only an SVG icon, no text
   - Adds `aria-label="Close"` to the button element
   - Commit: `fix(a11y): add aria-label to icon-only close button`

5. Fixes `heading-order` on `h3.section-title`:
   - Previous heading in the page is `<h1>` — `<h3>` skips level 2
   - Changes `<h3>` to `<h2>` to maintain hierarchy
   - Commit: `fix(a11y): correct heading hierarchy — h3 to h2 after h1`

6. Re-runs axe-core → 0 violations → status: COMPLETE

**Output in STATE.md:**
```yaml
last_run: 2026-07-06T05:12:00Z
status: COMPLETE
violations_found: 4
violations_fixed: 4
violations_remaining: 0
files_changed:
  - src/components/HeroBanner.jsx
  - src/components/ProductGrid.jsx
  - styles/typography.css
  - src/components/Modal.jsx
  - src/components/SectionTitle.jsx
commits_made: 4
cost_usd: 1.20
```

---

## Guardrails

- Do NOT remove semantic HTML elements to suppress violations — fix them properly
- Do NOT hide content with `display: none` or `aria-hidden="true"` to avoid violations
- Do NOT add `role` attributes when a native HTML element exists (e.g., use `<button>` not `<div role="button">`)
- Do NOT change visual design intent beyond what's required for color contrast compliance
- Do NOT modify test files or test assertions
- Do NOT touch backend code, API routes, or server-side templates unless they render frontend HTML
- Do NOT install, update, or remove dependencies
- Do NOT use `tabindex` values greater than 0 — this disrupts natural tab order
- Always prefer semantic HTML over ARIA — ARIA is a supplement, not a replacement
- If uncertain whether a fix changes visual design → flag for human review, do not guess

---

## Security and Best Practices

- Never hardcode credentials, tokens, or user data in alt text or ARIA labels
- If an accessibility fix involves form labels, ensure labels do not expose sensitive field purposes in ways that create phishing vectors
- Use deterministic, context-appropriate alt text — avoid generic text like "image" or "photo"
- Verify that ARIA attributes reference valid IDs (`aria-labelledby`, `aria-describedby`) — dangling references are worse than missing attributes
- All commits should be signed if the project requires it
