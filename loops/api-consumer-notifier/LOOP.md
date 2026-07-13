# LOOP.md — api-consumer-notifier

> Detect breaking API changes on merge to main and automatically notify all dependent services — preventing downstream outages before they happen.

---

## Loop Definition

```yaml
name: api-consumer-notifier
version: "1.0"

objective: "Detect breaking changes in the API surface on merge to main, identify all affected consumer services, and send targeted notifications with migration guidance"
# The loop succeeds when all affected consumers have been notified and notifications are confirmed delivered.

cadence: "event-driven"      # Triggered on merge to main branch

tools:
  - bash                    # Run diff commands, OpenAPI validators, and notification scripts
  - gh                      # Create GitHub issues on consumer repos, post PR comments

file_scope:
  allow:
    - "openapi.yaml"        # OpenAPI specification file
    - "openapi.json"        # OpenAPI specification file (JSON format)
    - "swagger.yaml"        # Swagger specification file
    - "swagger.json"        # Swagger specification file (JSON format)
    - "api/**"              # API route definitions (read-only — to detect changes)
    - "routes/**"           # Route handler files (read-only)
    - "src/routes/**"       # Nested route handlers (read-only)
    - "src/api/**"          # Nested API handlers (read-only)
    - "src/controllers/**"  # Controller files (read-only)
    - "consumers.yaml"      # Consumer registry — maps endpoints to dependent services
    - "consumers.json"      # Consumer registry (JSON format)
    - ".loops/api-consumer-notifier/**"  # Local state, configuration, and logs
  deny:
    - ".env*"               # Never touch environment files
    - "*.secret"            # Never touch secrets
    - "*.key"               # Never touch keys
    - "infrastructure/**"   # Never touch infra
    - "node_modules/**"     # Never touch dependencies
    - "dist/**"             # Never touch build output
    - "src/**"              # Never modify source code (read API routes only via api/**/routes/**)
    - "test/**"             # Never touch tests
    - "tests/**"

verifier:
  type: script
  command: "bash .loops/api-consumer-notifier/verify-notifications.sh"
  timeout_seconds: 120       # Notifications should complete quickly

termination:
  success:
    - all_consumers_notified # All affected consumers have received notifications
  failure:
    - max_iterations: 5      # Max 5 attempts per run (notification retries)
    - budget_exhausted       # Stops if API limits or safety cost limits hit
    - no_progress_detected

budget:
  max_tokens: 30000          # Lower token budget — this loop reads, not writes
  max_cost_usd: 1.00         # Spend cap per run

approval_required_for:
  - create_issues            # Ask before creating issues on external consumer repos
  - send_notifications       # Ask before sending Slack/email notifications in production

triggers:
  on_success: []
  on_failure:
    - notify-slack           # Alert the team if notification delivery fails

recovery:
  strategy: retry            # Retry notification delivery on failure
  max_retries: 3
  escalation: human          # Escalate to human if notifications can't be delivered

merge_strategy: none         # This loop does not create PRs — it only notifies
branch_prefix: n/a

state_file: .loops/api-consumer-notifier/STATE.md
skill_file: .loops/api-consumer-notifier/SKILL.md
```

---

## How This Loop Works

### The Cycle

```
1. Loop triggers on merge to main (or manual invocation)
2. Planner fetches the previous and current OpenAPI spec versions
3. Planner diffs the specs to detect breaking changes (removed endpoints, changed schemas, renamed fields)
4. If no breaking changes → exit with COMPLETE status (nothing to notify)
5. If breaking changes detected → Planner cross-references with consumer registry
6. Worker generates targeted notification messages per consumer with migration guidance
7. Worker sends notifications via configured channels (GitHub Issues, Slack, email)
8. Verifier confirms all notifications were delivered successfully
9. Update STATE.md with change report and notification log
```

### Dry Run

```bash
claude /loop api-consumer-notifier --dry-run
```

Diffs the API spec, identifies breaking changes and affected consumers, and produces a notification preview without sending anything.

### One-Shot Run

```bash
claude /loop api-consumer-notifier
```

Executes the full detect-notify-verify cycle once.

### Event-Driven Trigger

Configure a GitHub Action to trigger this loop on merge to main:

```yaml
on:
  push:
    branches: [main]
    paths: ['openapi.yaml', 'openapi.json', 'api/**', 'routes/**']
```

---

## What "Done" Means

The loop is **COMPLETE** when:
- The API spec diff has been analyzed for breaking changes
- All affected consumer services have been identified via the consumer registry
- Notifications with migration guidance have been sent to every affected consumer
- Delivery of all notifications is confirmed (GitHub issue created, Slack message delivered)
- STATE.md is updated with the change report

The loop is **BLOCKED** when:
- Consumer registry is missing or incomplete (can't identify affected services)
- Notification channels are unreachable (Slack API down, GitHub rate limited)
- Budget cap ($1.00) is reached
- `waiting_for_human: true` is set in STATE.md

---

## Scoping Rules

- **Read access:** OpenAPI specs, route handlers, and consumer registry — to detect changes and identify consumers
- **Write access:** State and log files only — this loop does NOT modify any source code
- **Creates:** GitHub issues and Slack messages on consumer repos/channels
- **Never touch:** Source code, test files, environment variables, infrastructure, dependencies
- **One loop = one scope:** api-consumer-notifier only detects and notifies. It does not fix breaking changes (that's the developer's job) or update consumer code.
