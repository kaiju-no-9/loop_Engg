---
name: api-consumer-notifier-skill
description: >
  Detects breaking API changes by diffing OpenAPI specs and notifies dependent
  consumer services with migration guidance. Trigger on "notify consumers",
  "breaking API change", or "API deprecation alert". Do NOT use for fixing code
  or updating API specs.
---

# API Consumer Notifier Skill

An agent skill for detecting breaking changes in an API's surface area, identifying which downstream consumer services are affected, and sending targeted notifications with actionable migration guidance. The agent reads OpenAPI spec diffs, cross-references a consumer registry, and delivers notifications through GitHub Issues, Slack, or email. It never modifies source code — it is a read-and-notify loop only.

---

## When to Use This Skill

Use this skill when:
- Code is merged to main that changes API endpoints, request/response schemas, or authentication
- The `api-contract-sync` loop has updated the OpenAPI spec and triggered this loop as a downstream chain
- A team wants proactive notification of API changes before consumer services break
- An API deprecation needs to be communicated to all dependents

Do NOT use this skill for:
- Fixing or updating the API spec itself (use `api-contract-sync` instead)
- Modifying consumer service code to adapt to API changes
- Writing or running API tests
- Managing API versioning strategy or gateway configuration
- Sending general team announcements unrelated to API changes

---

## Quick Reference

| Concept | What It Means |
|---|---|
| **Breaking change** | A change that will cause existing consumer code to fail — removed endpoint, changed response shape, renamed required field |
| **Non-breaking change** | A change consumers can ignore safely — added optional field, new endpoint, expanded enum values |
| **Consumer registry** | A YAML/JSON file mapping API endpoints to the services that consume them |
| **Migration guidance** | Specific instructions telling a consumer team what to change in their code to adapt |
| **OpenAPI diff** | A structured comparison of two versions of an OpenAPI spec, highlighting additions, removals, and modifications |

### Breaking vs Non-Breaking Changes

| Change Type | Breaking? | Action |
|---|---|---|
| Endpoint removed | **Yes** | Notify all consumers of that endpoint |
| Required field added to request body | **Yes** | Notify — consumers must send the new field |
| Response field removed | **Yes** | Notify — consumers may be reading that field |
| Response field renamed | **Yes** | Notify — consumers referencing old name will break |
| Response field type changed | **Yes** | Notify — consumers parsing the old type will break |
| Authentication scheme changed | **Yes** | Notify all consumers |
| New optional query parameter added | No | No notification needed |
| New endpoint added | No | No notification needed (unless it replaces a deprecated one) |
| New optional response field added | No | No notification needed |
| Description or example updated | No | No notification needed |

---

## Workflow: Detect Breaking Changes

1. **Get the spec versions** — retrieve the previous (pre-merge) and current (post-merge) OpenAPI specs:
   ```bash
   # Get the previous version from the merge base
   git show HEAD~1:openapi.yaml > /tmp/openapi-old.yaml
   cp openapi.yaml /tmp/openapi-new.yaml
   ```
2. **Diff the specs** — use a structured diff tool to identify changes:
   ```bash
   # Using oasdiff (recommended) or openapi-diff
   npx oasdiff diff /tmp/openapi-old.yaml /tmp/openapi-new.yaml --format json
   ```
3. **Classify changes** — parse the diff output and categorize each change as breaking or non-breaking using the table above
4. **Filter to breaking changes only** — discard non-breaking changes (they don't require notification)
5. **If no breaking changes → exit** — set status to COMPLETE with `breaking_changes_found: 0`

---

## Workflow: Identify Affected Consumers

1. **Read the consumer registry** — load `consumers.yaml` (or `consumers.json`):
   ```yaml
   # consumers.yaml example
   consumers:
     - service: billing-service
       repo: org/billing-service
       endpoints:
         - GET /api/invoices
         - POST /api/payments
       contact:
         slack: "#billing-team"
         github: "@billing-team"

     - service: mobile-app
       repo: org/mobile-app
       endpoints:
         - GET /api/users/{id}
         - GET /api/products
       contact:
         slack: "#mobile-team"
         github: "@mobile-devs"
   ```
2. **Match breaking changes to consumers** — for each breaking change, find all consumers whose `endpoints` list includes the affected endpoint
3. **Group by consumer** — aggregate all breaking changes per consumer service (one notification per consumer, not per change)
4. **Generate migration guidance** — for each consumer, write specific instructions on what they need to change

---

## Workflow: Send Notifications

1. **Compose notification messages** — for each affected consumer, create a notification that includes:
   - Which endpoints changed and how
   - What the consumer needs to do (specific code changes)
   - A timeline if a deprecation period applies
   - A link to the API changelog or PR that introduced the change
2. **Send via configured channels:**
   - **GitHub Issues** (preferred for tracking):
     ```bash
     gh issue create --repo org/billing-service \
       --title "⚠️ Breaking API change: POST /api/payments response schema updated" \
       --body "Migration guidance..."
     ```
   - **Slack** (for immediate awareness):
     ```bash
     curl -X POST "$SLACK_WEBHOOK_URL" -H 'Content-type: application/json' \
       --data '{"channel": "#billing-team", "text": "..."}'
     ```
   - **PR comment** (on the triggering PR):
     ```bash
     gh pr comment $PR_NUMBER --body "Breaking change detected. Affected consumers: ..."
     ```
3. **Confirm delivery** — verify that GitHub issues were created (check HTTP 201) and Slack messages were sent
4. **Log results** — record each notification (consumer, channel, status) in STATE.md

---

## Decision Rules

- If no consumer registry file exists → set `waiting_for_human: true` with a message to create `consumers.yaml` and skip notification
- If a breaking change affects an endpoint not listed in the consumer registry → log a warning ("untracked endpoint changed") but do not block the loop
- If the same consumer is affected by 3+ breaking changes → send a single consolidated notification, not separate ones
- If a breaking change is a field rename → include both old and new field names in the migration guidance with a code snippet
- If a breaking change is an endpoint removal → check if a replacement endpoint exists and include it in the migration guidance
- If Slack webhook is not configured → fall back to GitHub Issues only
- If GitHub issue creation fails (rate limit, auth) → retry up to `max_retries`, then escalate to human
- If the OpenAPI spec file doesn't exist → log error, set `waiting_for_human: true`, and suggest running `api-contract-sync` first
- If the diff tool reports no changes at all → exit cleanly with `COMPLETE` status

---

## Example

**Input:** Merge to main changes `openapi.yaml` — the `/api/users/{id}` endpoint response removes the `email` field and renames `name` to `full_name`.

**Consumer registry shows:**
```yaml
consumers:
  - service: mobile-app
    repo: org/mobile-app
    endpoints: [GET /api/users/{id}]
    contact: { slack: "#mobile-team", github: "@mobile-devs" }
  - service: admin-dashboard
    repo: org/admin-dashboard
    endpoints: [GET /api/users/{id}, GET /api/users]
    contact: { slack: "#admin-team", github: "@admin-devs" }
```

**Steps the agent takes:**

1. Diffs `openapi.yaml` at `HEAD~1` vs `HEAD` → finds 2 breaking changes:
   - `GET /api/users/{id}` response: field `email` removed
   - `GET /api/users/{id}` response: field `name` renamed to `full_name`

2. Cross-references consumer registry → 2 consumers affected: `mobile-app` and `admin-dashboard`

3. Composes notification for `mobile-app`:
   ```
   ⚠️ Breaking API Change: GET /api/users/{id}

   Two breaking changes affect your service:

   1. Field `email` has been removed from the response.
      → If you use `response.email`, remove or replace it.

   2. Field `name` has been renamed to `full_name`.
      → Update: `response.name` → `response.full_name`

   PR: https://github.com/org/api-service/pull/142
   ```

4. Creates GitHub issue on `org/mobile-app` → confirmed (issue #87)
5. Posts to `#mobile-team` Slack channel → confirmed

6. Composes and sends identical notification to `admin-dashboard` → confirmed (issue #203, Slack delivered)

**Output in STATE.md:**
```yaml
last_run: 2026-07-10T14:30:00Z
status: COMPLETE
breaking_changes_found: 2
consumers_affected: 2
notifications_sent:
  - consumer: mobile-app
    channel: github-issue
    status: delivered
    issue_url: https://github.com/org/mobile-app/issues/87
  - consumer: mobile-app
    channel: slack
    status: delivered
  - consumer: admin-dashboard
    channel: github-issue
    status: delivered
    issue_url: https://github.com/org/admin-dashboard/issues/203
  - consumer: admin-dashboard
    channel: slack
    status: delivered
cost_usd: 0.35
```

---

## Guardrails

- Do NOT modify any source code — this loop is read-and-notify only
- Do NOT modify the OpenAPI spec — that is the `api-contract-sync` loop's responsibility
- Do NOT send notifications for non-breaking changes — only breaking changes warrant notification
- Do NOT create duplicate issues — check for existing open issues with the same title before creating new ones
- Do NOT include sensitive data (API keys, tokens, user data) in notifications
- Do NOT send notifications to channels not listed in the consumer registry
- Keep notification messages concise and actionable — include what changed, what to do, and a link to the PR
- If uncertain whether a change is breaking → err on the side of notifying (false positives are better than missed breakages)

---

## Security and Best Practices

- Never include API keys, tokens, or credentials in notification messages
- Use Slack webhooks or GitHub tokens stored as environment variables, never hardcoded
- Validate the consumer registry format before processing — malformed YAML should not crash the loop
- Rate-limit notifications to avoid spamming channels (max one consolidated notification per consumer per run)
- Log all notification attempts (including failures) for audit trail
