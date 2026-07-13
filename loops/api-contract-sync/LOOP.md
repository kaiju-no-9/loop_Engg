# LOOP.md — api-contract-sync

> Keep the OpenAPI spec perfectly in sync with route handlers on every file change — so the spec is always the single source of truth.

---

## Loop Definition

```yaml
name: api-contract-sync
version: "1.0"

objective: "Detect changes in API route handler files, update the OpenAPI specification to match, and validate the spec against the live routes"
# The loop succeeds when the OpenAPI spec accurately reflects all route handlers and passes validation.

cadence: "event-driven"      # Triggered when route handler files change

tools:
  - bash                    # Run spec validators, route parsers, and diff tools
  - file_edit               # Modify OpenAPI spec files (YAML/JSON)
  - git                     # Commit spec updates and push PR branch

file_scope:
  allow:
    - "openapi.yaml"        # OpenAPI specification file (primary write target)
    - "openapi.json"        # OpenAPI specification file (JSON format)
    - "swagger.yaml"        # Swagger specification file
    - "swagger.json"        # Swagger specification file (JSON format)
    - "api/**"              # API route definitions (read to extract signatures)
    - "routes/**"           # Route handler files
    - "src/routes/**"       # Nested route handlers
    - "src/api/**"          # Nested API handlers
    - "src/controllers/**"  # Controller files
    - "src/handlers/**"     # Handler files (Go, Rust)
    - "docs/api/**"         # API documentation directory
    - ".loops/api-contract-sync/**"  # Local state, configuration, and logs
  deny:
    - ".env*"               # Never touch environment files
    - "*.secret"            # Never touch secrets
    - "*.key"               # Never touch keys
    - "infrastructure/**"   # Never touch infra
    - "node_modules/**"     # Never touch dependencies
    - "dist/**"             # Never touch build output
    - ".github/**"          # Never touch CI config
    - "test/**"             # Never touch test files
    - "tests/**"
    - "src/models/**"       # Never touch data models directly
    - "src/services/**"     # Never touch business logic

verifier:
  type: script
  command: "npx @redocly/cli lint openapi.yaml && bash .loops/api-contract-sync/verify-routes.sh"
  timeout_seconds: 180       # Spec validation + route comparison

termination:
  success:
    - spec_in_sync           # OpenAPI spec matches all route handlers and passes linting
  failure:
    - max_iterations: 8      # Max 8 sync-validate cycles per run
    - no_progress_detected   # Stops if two consecutive runs produce the same diff
    - budget_exhausted       # Stops when token or dollar limit is hit

budget:
  max_tokens: 40000          # Per-run token cap
  max_cost_usd: 1.00         # Hard stop — never exceed this per run

approval_required_for:
  - push_to_main             # Always ask before merging to main
  - delete_endpoints         # Ask before removing an endpoint from the spec (may be intentional deprecation)
  - breaking_schema_change   # Ask before changing response schemas that consumers depend on

triggers:
  on_success:
    - api-consumer-notifier  # Notify downstream consumers of any spec changes
  on_failure:
    - notify-slack           # Alert the team if sync fails

recovery:
  strategy: rollback_last_commit # git revert HEAD — undo the spec change
  max_retries: 2                 # Retry twice before escalating
  escalation: human              # Final fallback is always human review

merge_strategy: pr
branch_prefix: loop/api-contract-sync

state_file: .loops/api-contract-sync/STATE.md
skill_file: .loops/api-contract-sync/SKILL.md
```

---

## How This Loop Works

### The Cycle

```
1. Loop triggers when route handler files change (or manual invocation)
2. Planner reads STATE.md + SKILL.md, scans route handler files for endpoint definitions
3. Planner compares extracted endpoints against the current OpenAPI spec
4. Planner identifies drift: new endpoints, modified parameters, removed routes, changed response schemas
5. Planner produces a sync plan (dry-run stops here)
6. Worker updates the OpenAPI spec to match the actual route handlers
7. Verifier lints the spec with Redocly and validates routes match
8. If spec is valid and in sync → update STATE.md, trigger api-consumer-notifier
9. If spec has errors → iterate (up to max_iterations)
10. If stuck → recovery protocol (rollback, retry, escalate)
```

### Dry Run

```bash
claude /loop api-contract-sync --dry-run
```

Scans route handlers, identifies drift from the OpenAPI spec, and produces a sync report without modifying the spec file.

### One-Shot Run

```bash
claude /loop api-contract-sync
```

Executes the full detect-sync-validate cycle once. Review the PR it opens.

### Event-Driven Trigger

Configure a GitHub Action to trigger on route file changes:

```yaml
on:
  push:
    branches: [main, develop]
    paths: ['api/**', 'routes/**', 'src/routes/**', 'src/api/**', 'src/controllers/**']
```

---

## What "Done" Means

The loop is **COMPLETE** when:
- All route handlers have been parsed and their endpoint signatures extracted
- The OpenAPI spec has been updated to match the actual routes
- The spec passes Redocly linting with zero errors
- A route-vs-spec validation confirms no drift remains
- All changes are committed atomically and a PR is opened
- STATE.md is updated with sync results

The loop is **BLOCKED** when:
- `max_iterations` (8) reached without achieving full sync
- Budget exhausted ($1.00 or 40,000 tokens)
- Route handler uses a pattern the parser can't interpret (dynamic routes, metaprogramming)
- The spec has structural issues that can't be resolved automatically
- `waiting_for_human: true` is set in STATE.md

---

## Scoping Rules

- **Write access:** OpenAPI spec files (`openapi.yaml`, `openapi.json`, `swagger.*`) and state logs
- **Read access:** Route handler files (`api/**`, `routes/**`, `src/controllers/**`) — to extract endpoint definitions
- **Never touch:** Source code logic, data models, business logic, test files, environment variables, CI config
- **One loop = one scope:** api-contract-sync only updates the API spec. It does not fix route handlers, modify controllers, or write tests. It chains to `api-consumer-notifier` for downstream notification.
