---
name: code-repair-skill
description: >
  Diagnoses source code bugs from test failures and applies minimal production-code
  fixes. Trigger on "fix the code", "source bug", or "tests failing due to code
  issue". Do NOT use for writing new tests or updating dependencies.
---

# Code Repair Skill

An agent skill for tracing test failures back to bugs in production source code, diagnosing root causes, and applying the smallest possible code fix that makes the test suite pass. Unlike `ci-sweeper` (which prioritizes fixing tests), this skill prioritizes fixing the *source code* — operating on the assumption that the test is correct and the code is wrong. It commits atomic, minimal fixes and never introduces new behavior beyond what's needed to resolve the failure.

---

## When to Use This Skill

Use this skill when:
- Tests are failing because of bugs in source code (not stale test expectations)
- A code change introduced a regression that broke previously passing tests
- Runtime errors (TypeError, NullPointerException, panic) are traced to source code logic
- The test assertions are correct and the implementation needs to be fixed

Do NOT use this skill for:
- Fixing stale test expectations or outdated mocks (use `ci-sweeper` instead)
- Writing new test suites from scratch (use `test-coverage-grower` instead)
- Refactoring source code beyond what's needed to fix the failing test
- Updating or installing dependencies (use `dependency-updater` instead)
- Fixing CI/CD pipeline issues or infrastructure problems
- Performance optimization (unless a test explicitly asserts on performance)

---

## Quick Reference

| Concept | What It Means |
|---|---|
| **Root cause** | The specific line or function in source code that causes the test failure |
| **Minimal diff** | The smallest change to source code that makes the failing test pass without breaking others |
| **Regression** | A previously passing test now fails due to a recent code change |
| **Source fix** | Modifying production code (`src/**`, `lib/**`) to correct its behavior |
| **Test fix** | Modifying a test — only allowed when the test itself is provably wrong |
| **Cascading failure** | A single source bug causing multiple test failures — fix the root cause, all tests pass |
| **Side-effect-free fix** | A change that doesn't alter behavior for passing tests — only fixes the broken path |

### Diagnosis Priority Order

| Check | Purpose |
|---|---|
| 1. Read the test assertion | Understand what the test expects |
| 2. Read the source function | Understand what the code actually does |
| 3. Check git log | Identify the commit that introduced the regression |
| 4. Trace the call stack | Follow the error from assertion through source layers |
| 5. Check types and contracts | Verify function signatures, return types, and interfaces |
| 6. Check edge cases | Look for null checks, boundary conditions, and error handling |

---

## Workflow: Diagnose Source Code Bug

1. **Run the test suite** — execute `verifier.command` (e.g., `npm test`) and capture full output
2. **Parse failures** — extract each failing test: name, file, line, assertion message, stack trace, and error type
3. **Classify each failure:**
   - **Runtime error** (TypeError, NullPointerException, panic) → source code bug, high confidence
   - **Assertion mismatch** (expected vs received differ) → could be source or test; investigate further
   - **Timeout** → may be an infinite loop or missing async handling in source
   - **Import/Module error** → missing export, wrong path, circular dependency
4. **Identify cascading failures** — if multiple tests fail in the same module, they likely share a root cause. Fix the root cause first.
5. **Trace to source code** — for each failure:
   - Read the test file to understand what it asserts
   - Read the source file the test exercises
   - Check recent git changes on the source file:
     ```bash
     git log -5 --oneline -- src/services/order.js
     ```
   - Walk the call stack from the assertion to the source function that produces the wrong result
6. **Determine fix location** — decide whether to fix source or test:
   - **Default: fix the source** — the test is assumed correct unless evidence shows otherwise
   - **Exception: fix the test** — only if the test is provably wrong (testing deprecated behavior, wrong expected value confirmed by specification)

---

## Workflow: Apply Minimal Fix

1. **Write the fix** — make the smallest change that corrects the behavior:
   - Fix the specific logic error (wrong operator, missing null check, incorrect condition)
   - Do NOT refactor surrounding code
   - Do NOT add features unrelated to the failing test
   - Do NOT change function signatures unless absolutely necessary
2. **Verify scope** — ensure the fix doesn't change behavior for any currently passing test:
   ```bash
   # Run the full suite, not just the failing test
   npm test
   ```
3. **Commit atomically** — one commit per bug fix with a descriptive message:
   ```
   fix(orders): handle null customer in calculateTotal — was causing TypeError on guest checkout
   ```
4. **If the fix requires changing >30 lines** → flag in STATE.md as `needs_human_review` and document why the fix is large
5. **If the fix requires changing >3 files** → request human approval before committing

---

## Workflow: Handle Complex Failures

1. **Multi-file bugs** — when the bug spans multiple source files:
   - Identify the primary source of the bug (usually the file where the wrong value originates)
   - Fix from the inside out — fix the root function first, then propagate changes if needed
   - Commit as a single atomic change (multi-file fix = one commit, not separate commits per file)
2. **Flaky tests** — when a test sometimes passes and sometimes fails:
   - Check for non-deterministic behavior: `Date.now()`, `Math.random()`, race conditions, unordered collections
   - Fix the source code to be deterministic, or fix the test to handle non-determinism
   - Log flaky tests in STATE.md even if they pass on the current run
3. **Type errors and interface mismatches** — when types don't align:
   - Check if a function's return type changed but callers weren't updated
   - Fix the source function to return the expected type, or update all callers consistently
   - Verify the TypeScript compiler passes (if applicable): `npx tsc --noEmit`

---

## Decision Rules

- If the test was written before the source change that broke it → the source is wrong; fix the source
- If the test was written after the source change → investigate further; the test may be testing the wrong behavior
- If the source change was a deliberate refactor (e.g., function renamed, return type changed) → fix the test, not the source
- If the error is a null/undefined reference → add a null check or provide a default value; do NOT change the function's public API
- If the error is an off-by-one → fix the boundary condition in the source; verify with edge case inputs
- If a fix requires changing an exported function signature → flag for `approval_required_for: modify_public_api`
- If multiple tests fail and they share a common source function → fix the source function first, then re-run all tests
- If the same file has failed in the last 3 consecutive runs → escalate to `waiting_for_human`
- If all tests pass when the loop starts → set status to `COMPLETE` with `bugs_fixed: 0` and exit cleanly
- If a fix introduces new lint warnings → fix the lint issues as part of the same commit
- If the failing test is in a `skip` or `todo` state → leave it as-is; do not attempt to fix skipped tests

---

## Example

**Input:** `npm test` output showing 2 failures

```
FAIL  tests/services/order.test.js
  ● OrderService.calculateTotal() › should include tax for domestic orders
    TypeError: Cannot read properties of null (reading 'taxRate')
      at calculateTotal (src/services/order.js:45)
      at Object.<anonymous> (tests/services/order.test.js:23)

FAIL  tests/services/order.test.js
  ● OrderService.calculateTotal() › should apply discount for orders over $100
    expect(received).toBe(expected)
    Expected: 94.50
    Received: 105.00
```

**Steps the agent takes:**

1. Parses 2 failures in `order.test.js`, both in `calculateTotal()` — likely a shared root cause

2. Reads the test file `tests/services/order.test.js`:
   ```javascript
   test('should include tax for domestic orders', () => {
     const order = { items: [...], customer: { country: 'US' } };
     expect(calculateTotal(order)).toBe(107.10); // $100 + 7.1% tax
   });
   test('should apply discount for orders over $100', () => {
     const order = { items: [...], customer: { country: 'US' }, coupon: 'SAVE10' };
     expect(calculateTotal(order)).toBe(94.50); // $105 - 10% discount
   });
   ```

3. Reads the source file `src/services/order.js:45`:
   ```javascript
   function calculateTotal(order) {
     const subtotal = sumItems(order.items);
     const region = getRegion(order.customer.country); // line 45
     const tax = subtotal * region.taxRate;
     return subtotal + tax;
   }
   ```

4. Checks `git log -3 --oneline -- src/services/order.js`:
   ```
   a1b2c3d refactor(orders): extract region lookup into getRegion()
   ```

5. Reads `getRegion()`:
   ```javascript
   function getRegion(country) {
     const regions = { US: { taxRate: 0.071 }, CA: { taxRate: 0.13 } };
     return regions[country]; // Returns undefined for unknown countries — no null check!
   }
   ```
   Wait — `US` is in the map, so it should work. Re-reads the test... the customer object is correct. Re-reads the error — it says `null` not `undefined`. Checks the actual refactor commit:
   ```javascript
   // The refactor changed the return: returns null for unknown AND wraps in a try-catch that returns null
   function getRegion(country) {
     try {
       return regionConfig.lookup(country); // regionConfig is undefined — was never imported!
     } catch {
       return null;
     }
   }
   ```

6. Root cause: `regionConfig` was never imported after the refactor. The `getRegion` function silently returns `null` for every country.

7. Fix: adds the missing import and restores correct behavior:
   ```javascript
   // Add at top of file
   const regionConfig = require('./config/regions');
   ```
   This also fixes the discount test because `calculateTotal` now correctly computes the subtotal with tax before applying discounts.

8. Commit: `fix(orders): import regionConfig in order service — getRegion was returning null for all countries after refactor`

9. Re-runs `npm test` → both tests pass → status: COMPLETE

**Output in STATE.md:**
```yaml
last_run: 2026-07-10T16:45:00Z
status: COMPLETE
tests_found: 2
bugs_fixed: 1
tests_fixed: 2
bugs_remaining: 0
root_cause: "Missing import of regionConfig after refactor — getRegion returned null for all inputs"
files_changed:
  - src/services/order.js
commits_made: 1
cost_usd: 0.85
iterations_used: 1
waiting_for_human: false
```

---

## Guardrails

- Do NOT change test assertions to match broken source code — fix the source, not the test (unless the test is provably wrong)
- Do NOT refactor source code beyond what's needed to fix the failing test
- Do NOT add new features or behavior not exercised by existing tests
- Do NOT change exported function signatures without human approval
- Do NOT skip, disable, or mark tests as `.todo` to avoid failures
- Do NOT install, update, or remove dependencies
- Do NOT modify database migrations, infrastructure config, or CI pipelines
- Do NOT make changes that increase the diff beyond what's necessary for the fix
- Do NOT change code formatting or style in files you're not fixing (no drive-by cleanup)
- If uncertain whether the source or the test is wrong → flag for human review with evidence for both interpretations

---

## Security and Best Practices

- Never hardcode API keys, passwords, or tokens in source code fixes
- If a test failure exposes credentials in its output → flag immediately, do not log the credentials in STATE.md
- Verify that fixes don't introduce new security vulnerabilities (e.g., removing input validation to make a test pass)
- If a fix involves error handling → ensure errors are caught and logged, not silently swallowed
- Use deterministic test data — avoid `Date.now()`, `Math.random()`, or network calls in fixes
- All commits should be signed if the project requires it
