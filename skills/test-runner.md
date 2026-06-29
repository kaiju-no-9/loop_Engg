---
name: test-runner
description: >
  Runs test suites, parses test output, and reports results. Trigger on "run tests", "check failures", or when verifying changes. Do NOT use for writing new tests or debugging code.
---

# Test Runner

This skill enables the agent to execute project test suites, correctly parse their output, and provide a structured summary of passes, fails, and error messages. It is essential for the Verifier role.

---

## When to Use This Skill

Use this skill when:
- You need to verify if code changes broke existing functionality.
- You need a structured list of failing tests to pass to a Planner.
- A loop specifies `verifier.type: test_suite`.

Do NOT use this skill for:
- Writing new unit or integration tests.
- Actually fixing the failing tests (that is the Worker's job).

---

## Workflow: Verify Test Suite

1. **Identify the test command**: Check `LOOP.md` for `verifier.command` (e.g., `npm test`). If not present, look at `package.json` or equivalent.
2. **Execute the test suite**: Run the command in the terminal.
3. **Parse the output**: Extract the total number of tests run, passed, and failed.
4. **Extract error details**: For each failing test, extract the test name, file path, and the specific error message or stack trace.
5. **Format the report**: Produce a structured summary of the results.

---

## Decision Rules

- If the test command hangs for more than 5 minutes → kill the process and report a timeout failure.
- If the test output is too large to read fully → extract just the summary section and the first 5 failures.
- If there are no failing tests → report SUCCESS.

---

## Example

**Input:** "Run the tests and tell me what's failing."

**Steps the agent takes:**
1. Runs `npm test`.
2. Observes 2 tests failing out of 50.
3. Extracts the names and error messages for the 2 failing tests.

**Output:**
```markdown
## Test Results
- **Total**: 50
- **Passed**: 48
- **Failed**: 2

### Failures
1. `src/auth.test.js: login fails with bad password`
   - **Error**: `Expected 401 but got 200`
2. `src/utils.test.js: parseDate handles leap years`
   - **Error**: `TypeError: undefined is not a function`
```

---

## Guardrails

- Do NOT attempt to fix the code to make the tests pass.
- Do NOT run tests in watch mode (`--watch`). Always run single-pass execution.
- Always report the exact error message, do not summarize or guess the cause.
