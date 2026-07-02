# Contributing a New Loop

Thank you for adding a new loop to the catalog! Follow these steps to ensure your loop is production-ready.

## How to Add a Loop

1. **Fork and Clone**: Fork this repository and clone it locally.
2. **Scaffold**: Create your loop directory under `loops/<loop-name>/`.
3. **Required Files**: Your loop must contain:
   - `LOOP.md`: The definition of what the loop does.
   - `SKILL.md`: The capabilities needed for the loop.
   - `STATE.md`: The template for state tracking.

## LOOP.md Requirements
Your `LOOP.md` must have:
- [ ] A single, testable `objective`.
- [ ] At least one `verifier` with a runnable command.
- [ ] At least one `termination` condition beyond `max_iterations`.
- [ ] `budget` caps set (`max_tokens`, `max_cost_usd`).
- [ ] `approval_required_for` any destructive action.
- [ ] `file_scope` explicitly defined.
- [ ] Documented `--dry-run` behavior.

## Local Testing
Always test your loop locally before submitting a PR:
```bash
# See the plan without making changes (using the agent command)
claude /loop <loop-name> --dry-run
```

## Readiness Score
Run `loop-wizard audit` on your new loop. It must score at least 80/100.
```bash
loop-wizard audit . --suggest
```

## Naming Conventions
- Loop names should be kebab-case, typically `<noun>-<verb>er` (e.g., `ci-sweeper`, `changelog-drafter`).

## Pull Request Process
1. Open a PR with the title: `feat(loop): add <loop-name>`.
2. Include the `loop-wizard cost` estimate in your PR description.
3. A maintainer will review your loop against the [DESIGN_CHECKLIST](DESIGN_CHECKLIST.md).
