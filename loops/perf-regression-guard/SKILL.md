---
name: perf-regression-guard-skill
description: >
  Runs performance audits (Lighthouse/k6) and flags regressions on PRs. Trigger on
  'run performance tests' or 'check performance'. Do NOT use for general refactoring
  or backend logic.
---

# Performance Regression Guard Skill

An agent skill for executing performance audits, extracting core metrics, comparing them against established baselines, and flagging regressions in pull requests using the GitHub CLI.

---

## When to Use This Skill

Use this skill when:
- Pull requests need performance validation during CI or pre-merge checks
- You need to run Lighthouse or k6 performance audits on frontend pages/endpoints
- You want to detect performance regression metrics (e.g. FCP, LCP, TBT, response latency)
- You need to post performance scorecard reports onto pull requests

Do NOT use this skill for:
- Writing new component/page features
- Automating major frontend/backend code refactoring
- Fixing general test suite errors unrelated to performance
- Changing application build pipelines or CI workflow definitions

---

## Quick Reference

| Metric | Target / Best Practice | Description |
|---|---|---|
| **LCP** | ≤ 2.5s | Largest Contentful Paint — measures loading performance |
| **FCP** | ≤ 1.8s | First Contentful Paint — measures perceived load speed |
| **TBT** | ≤ 200ms | Total Blocking Time — measures page responsiveness |
| **CLS** | ≤ 0.1 | Cumulative Layout Shift — measures visual stability |
| **p95 Latency** | ≤ 200ms | 95th percentile response latency in load testing (k6) |

---

## Workflow: Run Performance Audits

1. **Identify routes/endpoints** — read configuration or command args to determine which URLs or API paths to test.
2. **Execute audit commands**:
   ```bash
   # Run Lighthouse audit
   npx lighthouse http://localhost:3000/home --output=json --output-path=.loops/perf-regression-guard/report.json
   
   # Run k6 load tests
   k6 run --out json=.loops/perf-regression-guard/k6_report.json tests/perf/load-test.js
   ```
3. **Parse audit output** — read generated JSON reports to extract key metrics (LCP, TBT, error rates, latencies).

---

## Workflow: Analyze & Compare Metrics

1. **Retrieve baseline** — load the latest baseline metrics from `.loops/perf-regression-guard/baseline.json`. If none exists, treat the current run as the baseline.
2. **Calculate variance** — compare current metrics against the baseline:
   - Lighthouse Score drop: `Baseline Score - Current Score`
   - Latency increase: `((Current Latency - Baseline Latency) / Baseline Latency) * 100%`
3. **Identify regressions** — flag a regression if:
   - Any Core Web Vital score drops by > 5 points
   - p95 latency increases by > 10%
   - Error rate increases by > 1%

---

## Workflow: Flag Regressions on PR

1. **Generate Markdown report** — compile comparison table and details of regressions.
2. **Post to GitHub PR** — use `gh` CLI to comment on the active PR:
   ```bash
   gh pr comment <pr_number> --body-file=.loops/perf-regression-guard/comment.md
   ```
3. **Update state** — update `STATE.md` with metrics and status.

---

## Decision Rules

- If no baseline file exists → save current results as the baseline and exit with success.
- If a regression is detected → generate report, post to PR, and set exit code to non-zero (or status: BLOCKED).
- If performance matches or exceeds the baseline → post a success report to the PR and exit with success.
- If the dev server is not running → attempt to start it using `npm run start` or `npm run dev` before running audits.

---

## Example

**Input:** Performance audit run on PR #12

**Steps the agent takes:**
1. Runs Lighthouse audit on `http://localhost:3000/` and gets an LCP of 3.2s, TBT of 350ms, Overall: 78.
2. Reads baseline: LCP of 2.1s, TBT of 120ms, Overall: 91.
3. Compares metrics and flags significant regressions in LCP (+52%) and TBT (+191%).
4. Generates a markdown report summarizing the findings.
5. Posts the report to the PR using `gh pr comment 12 --body-file=report.md`.

**Output:**
```markdown
### ⚠️ Performance Regression Detected

A performance audit was executed on this PR. The following regressions were identified:

| Metric | Baseline | Current | Change | Status |
|---|---|---|---|---|
| Lighthouse Score | 91 | 78 | -13 | ❌ Regression |
| Largest Contentful Paint (LCP) | 2.1s | 3.2s | +52% | ❌ Regression |
| Total Blocking Time (TBT) | 120ms | 350ms | +191% | ❌ Regression |
```

---

## Guardrails

- Do NOT comment repeatedly on the same PR commit hash; check if a comment for the current commit already exists.
- Do NOT modify production build assets directly.
- Always check that the URL/dev server is healthy before launching k6/Lighthouse.
