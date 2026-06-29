# Loop Production Readiness Checklist

> What makes a loop production-ready? Ensure you meet these requirements before running any loop autonomously.

## LOOP.md Completeness
- [ ] **Objective is testable**: The objective must be a single, testable sentence. Vague goals lead to infinite loops.
- [ ] **Verifier is defined**: A concrete verifier command (e.g., `npm test`, `eslint .`) is specified to check for completion.
- [ ] **Termination conditions**: At least one success condition and one failure condition beyond `max_iterations` must be set.
- [ ] **Budget cap**: `max_cost_usd` and `max_tokens` are set. Start low (e.g., $1.00) and increase as needed.
- [ ] **Approval gates**: `approval_required_for` is defined for any destructive actions (e.g., `push_to_main`, `delete_files`).
- [ ] **File Scope**: `allow` and `deny` globs are explicitly defined to restrict agent access.
- [ ] **Recovery strategy**: A `recovery` strategy is defined (e.g., `rollback_last_commit`) to handle irrecoverable states.

## SKILL.md Quality
- [ ] **Clear trigger**: Frontmatter `description` contains an active verb, trigger phrases, and explicit exclusions.
- [ ] **Concrete workflows**: Each task is broken down into numbered steps.
- [ ] **Decision rules**: If/then logic handles edge cases and ambiguity.
- [ ] **Worked example**: Includes a full example with realistic input and output.

## STATE.md Template
- [ ] **Structure**: Follows the standard schema (Current Run, Results, Changes, Budget, Human Interaction, Scheduling).
- [ ] **No initial state**: Blank state template, ready to be populated by the verifier.

## Safety & Execution
- [ ] **Dry-run tested**: Run with `--dry-run` to ensure the planner produces sensible steps.
- [ ] **Atomic commits**: The worker makes one atomic commit per logical change.
- [ ] **Separate verifier**: A fresh model instance evaluates "done" so the worker doesn't grade its own work.

## Observability
- [ ] **Logging**: Loop logs its execution path.
- [ ] **state.json**: The `state.json` sidecar tracks cost, commits, and status for the loop dashboard.
