---
name: ci-sweeper-skill
description: >
  Reads failing test output, identifies root causes, and makes minimal targeted
  fixes. Trigger on CI failures, broken tests, or "fix my tests". Do NOT use
  for refactoring, dependency updates, or writing new test suites from scratch.
---

# CI Sweeper Skill

An agent skill for diagnosing and fixing failing CI tests with the smallest possible code change. The agent reads test runner output, traces failures to root causes in source or test code, and applies minimal, surgical fixes — one per commit. It never rewrites working code, never skips tests, and never changes assertions to match broken behavior.

---

## When to Use This Skill

Use this skill when:
- CI tests are failing and need automated overnight fixes
- A test suite has regressions introduced by recent code changes
- You need to triage which test failures are fixable vs. require human judgment
- The loop needs to understand test output formats (Jest, Mocha, Vitest, pytest, Go test)

Do NOT use this skill for:
- Writing new test suites from scratch (use `test-coverage-grower` loop instead)
- Refactoring source code beyond what's needed to fix a failure
- Updating test dependencies or frameworks
- Fixing infrastructure/CI pipeline issues (YAML configs, Docker, runners)
- Performance testing or benchmarking

---

## Quick Reference

| Concept | What It Means |
|---|---|
| **Minimal diff** | The smallest code change that makes a failing test pass — no extra refactoring |
| **Root cause** | The actual line/function causing the failure, not just the assertion that reports it |
| **Atomic commit** | One commit per fix — `git revert` undoes exactly one action |
| **Test-only fix** | Changing the test itself (only when the test is wrong, not the code) |
| **Source fix** | Changing the source code that the test exercises |
| **Skip = forbidden** | Never use `.skip`, `.only`, `@pytest.mark.skip`, or any mechanism to avoid running a test |

### Supported Test Runners

| Runner | Stack | Output Format |
|---|---|---|
| Jest | Node.js | FAIL marker + diff + stack trace |
| Vitest | Node.js / Vite | Same as Jest (compatible output) |
| Mocha | Node.js | Failing count + stack trace |
| pytest | Python | FAILED marker + assertion introspection |
| Go test | Go | `--- FAIL:` + file:line |
| RSpec | Ruby | `Failure/Error:` + backtrace |
| JUnit/TestNG | Java | `FAILURES!!!` + stack trace |

---

## Workflow: Fix Failing Tests

1. **Run the test suite** — execute `verifier.command` (e.g., `npm test`) and capture full output
2. **Parse failures** — extract each failing test: name, file, line number, assertion message, and stack trace
3. **Prioritize** — sort failures by likelihood of cascading (a single root cause can fix multiple test failures)
4. **Diagnose root cause** — for each failure:
   - Read the failing test file to understand the assertion
   - Read the source file the test exercises
   - Check recent git changes (`git log -5 --oneline -- <file>`) for the breaking commit
   - Determine: is the test wrong, or is the source code wrong?
5. **Apply the fix** — make the smallest change possible:
   - If source code is wrong → fix the source function/method
   - If test expectation is outdated → update the assertion to match correct behavior
   - If test setup is stale → update fixtures, mocks, or setup data
6. **Commit atomically** — one commit per fix with a descriptive message: `fix(test): correct expected value in auth.test.js — was comparing against stale mock`
7. **Re-run tests** — run the full suite again to verify the fix didn't break other tests
8. **Iterate** — if failures remain, go back to step 2 with the updated output

---

## Workflow: Triage Unfixable Failures

1. **Identify unfixable tests** — a test is unfixable by this loop if:
   - It requires a new dependency or package update
   - It depends on an external service that's down (API, database, network)
   - The failure is in CI infrastructure (runner timeout, OOM, Docker issue)
   - The fix would require architectural changes beyond minimal diff
2. **Document in STATE.md** — add each unfixable test to `tests_remaining` with a reason
3. **Set `waiting_for_human: true`** — if all remaining failures are unfixable
4. **Continue fixing fixable tests** — don't stop the loop because some tests are unfixable

---

## Decision Rules

- If the test runner is not specified in LOOP.md → detect from `package.json` scripts, `pytest.ini`, `go.mod`, or `Gemfile`
- If a single source change fixes multiple tests → make one commit, reference all fixed tests in the message
- If the fix requires changing more than 20 lines → flag it in STATE.md as `needs_human_review` and move on
- If the test was marked as `.skip` before this loop ran → leave it skipped, do not fix it
- If an assertion expects a specific date/time → check if the failure is time-dependent and fix with relative dates or frozen time
- If a mock is returning stale data → update the mock, don't remove it
- If the same test has failed in the last 3 consecutive runs → escalate to `waiting_for_human`
- If all tests pass after the first iteration → complete immediately, don't iterate unnecessarily
- If no tests are failing when the loop starts → set status to `COMPLETE` with `tests_fixed: 0` and exit cleanly

---

## Example

**Input:** `npm test` output showing 3 failures

```
FAIL  src/auth.test.js
  ● login() › should return a token for valid credentials
    expect(received).toBe(expected)
    Expected: "Bearer eyJ..."
    Received: undefined

FAIL  src/utils.test.js
  ● formatDate() › should format ISO strings
    expect(received).toBe(expected)
    Expected: "June 27, 2026"
    Received: "Jun 27, 2026"

FAIL  src/api.test.js
  ● fetchUser() › should handle 404
    TypeError: Cannot read properties of undefined (reading 'status')
```

**Steps the agent takes:**

1. Parses 3 failures: `auth.test.js:login`, `utils.test.js:formatDate`, `api.test.js:fetchUser`

2. Diagnoses `auth.test.js`:
   - Reads `src/auth.js` → `login()` was refactored and now returns `{ token }` object instead of raw string
   - Fix: update test to access `result.token` instead of `result`
   - Commit: `fix(test): access token property after auth.login() return type change`

3. Diagnoses `utils.test.js`:
   - Reads `src/utils.js` → `formatDate()` uses `toLocaleDateString` which abbreviates month names
   - Fix: update test expectation from `"June 27, 2026"` to `"Jun 27, 2026"`
   - Commit: `fix(test): correct formatDate expected output to match abbreviated month`

4. Diagnoses `api.test.js`:
   - Reads `src/api.js` → `fetchUser()` was changed to throw on 404 instead of returning a response object
   - Fix: update test to use `expect(() => fetchUser(999)).toThrow()` instead of checking `.status`
   - Commit: `fix(test): update fetchUser 404 test to expect thrown error`

5. Re-runs `npm test` → all 3 tests pass → status: COMPLETE

**Output in STATE.md:**
```
last_run: 2026-06-28T02:14:00Z
status: COMPLETE
tests_found: 3
tests_fixed: 3
tests_remaining: 0
files_changed: src/auth.test.js, src/utils.test.js, src/api.test.js
commits_made: 3
cost_usd: 0.43
iterations_used: 1
waiting_for_human: false
```

---

## Guardrails

- Do NOT rewrite working tests — only fix tests that are currently failing
- Do NOT refactor source code beyond what's needed to fix the test failure
- Do NOT skip tests or mark them as `.skip` / `.only` / `@pytest.mark.skip`
- Do NOT change assertions to match broken behavior — fix the code or fix the expectation, never paper over the bug
- Do NOT touch files outside the `file_scope` defined in LOOP.md
- Do NOT install, update, or remove dependencies
- Do NOT modify CI pipeline configuration (`.github/workflows/`, `.gitlab-ci.yml`, etc.)
- Do NOT make changes that increase the diff beyond what's necessary
- Always prefer updating test expectations over changing source code, unless the source code is clearly wrong
- If uncertain whether the test or the source is wrong → flag for human review, do not guess

---

## Security and Best Practices

- Never hardcode API keys, passwords, or tokens in test fixtures
- If a test failure exposes credentials in its output → flag immediately, do not log the credentials in STATE.md
- Use deterministic test data — avoid `Date.now()`, `Math.random()`, or network calls in fixes
- Verify that fixes don't introduce new security vulnerabilities (e.g., don't disable authentication checks to make a test pass)
- All commits should be signed if the project requires it
