# LOOP.md — accessibility-audit

> Run axe-core accessibility scans weekly, detect WCAG violations, and apply minimal HTML/ARIA fixes — keeping your frontend inclusive by default.

---

## Loop Definition

```yaml
name: accessibility-audit
version: "1.0"

objective: "Scan frontend components for WCAG 2.1 AA violations using axe-core, apply automated fixes, and verify the fixes resolve the violations"
# The loop succeeds when axe-core reports zero critical/serious violations on scanned pages.

cadence: "0 5 * * 0"        # Every Sunday at 5am UTC

tools:
  - bash                    # Run axe-core scans, build commands, and test suites
  - file_edit               # Modify HTML, JSX, TSX, and CSS files to fix violations
  - git                     # Commit atomic fixes and push PR branch

file_scope:
  allow:
    - "src/**"              # Source components (JSX, TSX, Vue, Svelte)
    - "components/**"       # Shared UI components
    - "pages/**"            # Page-level components (Next.js, Nuxt)
    - "app/**"              # App directory (Next.js 13+)
    - "views/**"            # View templates
    - "templates/**"        # HTML templates
    - "public/**"           # Static HTML files
    - "styles/**"           # CSS/SCSS for color contrast fixes
    - "*.css"               # Root-level stylesheets
    - "*.html"              # Root-level HTML files
    - ".loops/accessibility-audit/**"  # Local state and logs
  deny:
    - ".env*"               # Never touch environment files
    - "*.secret"            # Never touch secrets
    - "*.key"               # Never touch keys
    - "infrastructure/**"   # Never touch infra
    - "node_modules/**"     # Never touch dependencies
    - "dist/**"             # Never touch build output
    - ".github/**"          # Never touch CI config
    - "server/**"           # Never touch backend code
    - "api/**"              # Never touch API routes
    - "test/**"             # Never touch test files directly
    - "tests/**"

verifier:
  type: test_suite
  command: "npx axe-core-cli --exit"   # Exits non-zero if violations remain
  timeout_seconds: 300

termination:
  success:
    - all_violations_resolved    # axe-core reports zero critical/serious violations
  failure:
    - max_iterations: 12         # Hard stop after 12 fix-verify cycles
    - no_progress_detected       # Stops if two consecutive runs fix zero new violations
    - budget_exhausted           # Stops when token or dollar limit is hit

budget:
  max_tokens: 50000              # Per-run token cap
  max_cost_usd: 2.00             # Hard stop — never exceed this per run

approval_required_for:
  - push_to_main                 # Always ask before merging to main
  - delete_files                 # Always ask before deleting any file
  - modify_styles                # Ask before changing global stylesheets (may affect visual design)

triggers:
  on_success: []
  on_failure:
    - notify-slack               # Alert the team if the loop fails

recovery:
  strategy: rollback_last_commit # git revert HEAD — undo the last atomic commit
  max_retries: 2                 # Retry twice before escalating
  escalation: human              # Final fallback is always human review

merge_strategy: pr
branch_prefix: loop/accessibility-audit

state_file: .loops/accessibility-audit/STATE.md
skill_file: .loops/accessibility-audit/SKILL.md
```

---

## How This Loop Works

### The Cycle

```
1. Loop runs on schedule (every Sunday at 5am) or manually
2. Planner reads STATE.md + SKILL.md, runs axe-core scan on target pages/components
3. Planner parses violation report, categorizes by severity (critical → serious → moderate → minor)
4. Planner produces a prioritized fix plan (dry-run stops here)
5. Worker applies fixes — one fix per atomic commit (ARIA attributes, semantic HTML, color contrast)
6. Verifier re-runs axe-core scan in a fresh context
7. If zero critical/serious violations → update STATE.md, mark COMPLETE
8. If violations remain → iterate (up to max_iterations)
9. If stuck → recovery protocol (rollback, retry, escalate)
```

### Dry Run

```bash
claude /loop accessibility-audit --dry-run
```

Scans the frontend, identifies all WCAG violations, and produces a prioritized fix plan without modifying any files.

### One-Shot Run

```bash
claude /loop accessibility-audit
```

Executes the full scan-fix-verify cycle once. Review the PR it opens.

### Scheduled Run

Push `.github/workflows/accessibility-audit.yml` to enable weekly runs at 5am UTC on Sundays.

---

## What "Done" Means

The loop is **COMPLETE** when:
- axe-core reports zero critical and serious WCAG 2.1 AA violations
- All fixes are committed atomically (one commit per violation category)
- A PR is opened summarizing the violations found and fixes applied
- STATE.md is updated with scan results

The loop is **BLOCKED** when:
- `max_iterations` (12) reached without resolving all critical/serious violations
- Budget exhausted ($2.00 or 50,000 tokens)
- Two consecutive iterations fix zero new violations
- A violation requires visual design changes that need human approval
- `waiting_for_human: true` is set in STATE.md

---

## Scoping Rules

- **Write access:** Frontend components (`src/**`, `components/**`, `pages/**`), styles (`styles/**`, `*.css`), and HTML templates
- **Read access:** All allowed files — to understand component structure and styling
- **Never touch:** Backend code, API routes, test files, environment variables, CI config, node_modules, build output
- **One loop = one scope:** accessibility-audit only fixes WCAG violations. It does not refactor components, update dependencies, or modify test suites.
