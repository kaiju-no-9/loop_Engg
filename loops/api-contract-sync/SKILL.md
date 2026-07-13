---
name: api-contract-sync-skill
description: >
  Parses API route handlers, detects drift from the OpenAPI spec, and updates
  the spec to match. Trigger on "sync API spec", "update OpenAPI", or "spec is
  outdated". Do NOT use for writing route handlers or modifying business logic.
---

# API Contract Sync Skill

An agent skill for keeping OpenAPI (or Swagger) specification files perfectly synchronized with the actual API route handlers in the codebase. The agent parses route files across popular frameworks (Express, FastAPI, Go net/http, Rails, Spring Boot), extracts endpoint signatures (method, path, parameters, request/response schemas), diffs them against the current spec, and applies targeted updates. It never modifies route handler code — only the spec file.

---

## When to Use This Skill

Use this skill when:
- Route handler files have been modified and the OpenAPI spec may be out of date
- New API endpoints have been added without corresponding spec entries
- API parameters, request bodies, or response schemas have changed
- The team wants automated spec-route consistency on every push

Do NOT use this skill for:
- Writing or modifying API route handlers or controller logic
- Generating API client SDKs from the spec (that's a separate build step)
- Managing API versioning strategy (v1, v2 paths)
- Fixing business logic bugs in endpoint handlers
- Writing API tests or integration tests

---

## Quick Reference

| Concept | What It Means |
|---|---|
| **OpenAPI spec** | The YAML/JSON file describing all API endpoints, parameters, request/response schemas |
| **Route handler** | The source code that defines an API endpoint (e.g., `app.get('/users', handler)`) |
| **Drift** | When the spec doesn't match the actual route handlers — endpoints missing, schemas outdated |
| **Endpoint signature** | The combination of HTTP method + path + parameters + request body + response schema |
| **Spec linting** | Validating the OpenAPI spec against the standard using tools like Redocly or Spectral |

### Framework-Specific Route Patterns

| Framework | Language | Route Pattern |
|---|---|---|
| Express | Node.js | `app.get('/path', handler)` or `router.post('/path', ...)` |
| FastAPI | Python | `@app.get("/path")` or `@router.post("/path")` |
| Go net/http | Go | `http.HandleFunc("/path", handler)` or `mux.Handle(...)` |
| Gin | Go | `r.GET("/path", handler)` |
| Rails | Ruby | `get '/path', to: 'controller#action'` in `routes.rb` |
| Spring Boot | Java | `@GetMapping("/path")` or `@RequestMapping(...)` |
| Django REST | Python | `path('path/', ViewSet.as_view())` in `urls.py` |

---

## Workflow: Detect Route Changes

1. **Identify route files** — scan the allowed file scope for route definition files:
   ```bash
   # Find route files based on common patterns
   find api/ routes/ src/routes/ src/api/ src/controllers/ \
     -name "*.js" -o -name "*.ts" -o -name "*.py" -o -name "*.go" \
     -o -name "*.rb" -o -name "*.java" 2>/dev/null
   ```
2. **Parse endpoint signatures** — extract HTTP method, path, parameters, and types from each route:
   - For Express/Koa: look for `app.<method>()` or `router.<method>()` calls
   - For FastAPI: look for `@app.<method>()` or `@router.<method>()` decorators
   - For Go: look for `HandleFunc()`, `Handle()`, or framework-specific route registrations
3. **Load current spec** — parse `openapi.yaml` (or `.json`) to get the currently documented endpoints
4. **Diff routes vs spec** — compare extracted routes against documented endpoints:
   - **New endpoints:** routes in code but not in spec
   - **Removed endpoints:** spec entries with no corresponding route handler
   - **Modified endpoints:** routes whose parameters, body, or response schema differ from spec
   - **Unchanged endpoints:** routes that match the spec exactly (no action needed)
5. **Generate sync plan** — produce an ordered list of spec updates needed

---

## Workflow: Update OpenAPI Spec

1. **Add new endpoints** — for each route found in code but missing from the spec:
   - Create a new `paths:` entry with the correct HTTP method
   - Add path parameters (e.g., `{id}`) with types inferred from the handler
   - Add query parameters if detected in the handler
   - Add request body schema if the handler reads a body (POST, PUT, PATCH)
   - Add response schema based on what the handler returns
   - Add appropriate `operationId`, `summary`, and `tags`
2. **Update modified endpoints** — for each endpoint where the spec doesn't match the handler:
   - Update parameter lists (added/removed/renamed parameters)
   - Update request body schema (new required fields, type changes)
   - Update response schema (changed fields, new status codes)
   - Preserve any existing descriptions, examples, or custom extensions
3. **Handle removed endpoints** — for endpoints in the spec but not in code:
   - Do NOT auto-remove — flag in STATE.md as `potentially_removed` for human review
   - The endpoint may have moved to a different file or be intentionally deprecated
4. **Validate the updated spec:**
   ```bash
   npx @redocly/cli lint openapi.yaml
   ```
5. **Commit the spec update:**
   ```
   docs(api): sync openapi.yaml with route handlers — added GET /api/orders, updated POST /api/users schema
   ```

---

## Workflow: Validate Spec Against Routes

1. **Run the linter** — ensure the spec is valid OpenAPI:
   ```bash
   npx @redocly/cli lint openapi.yaml --format stylish
   ```
2. **Cross-validate routes** — confirm every route handler has a spec entry and vice versa
3. **Check for common issues:**
   - Missing `operationId` fields
   - Duplicate path entries
   - Unreferenced schema definitions
   - Invalid `$ref` pointers
4. **Report results** — update STATE.md with sync status

---

## Decision Rules

- If the framework can't be auto-detected → check `package.json` (Node), `requirements.txt` (Python), `go.mod` (Go), `Gemfile` (Ruby), or `pom.xml` (Java) for framework dependencies
- If a route uses dynamic route registration (metaprogramming) → log it as `unparseable` in STATE.md and skip
- If a response type can't be inferred from the handler → add a `TODO` comment in the spec entry and use a generic `object` schema
- If an endpoint appears in the spec but not in code → do NOT remove it; flag as `potentially_removed` for human review (it might be in an unscanned file)
- If the spec uses `$ref` references to shared schemas → preserve the reference structure; don't inline schemas
- If multiple routes share the same path but different methods → each gets its own entry under the same `paths:` key
- If the spec file doesn't exist → create a new one with the OpenAPI 3.0.3 boilerplate and populate it from scratch
- If a route handler has JSDoc/docstring annotations → use them to populate `summary` and `description` fields

---

## Example

**Input:** A new Express route was added to `src/routes/orders.js`:

```javascript
// GET /api/orders — list all orders with optional status filter
router.get('/api/orders', async (req, res) => {
  const { status, page = 1, limit = 20 } = req.query;
  const orders = await OrderService.list({ status, page, limit });
  res.json({ data: orders, total: orders.length });
});

// GET /api/orders/:id — get a single order by ID
router.get('/api/orders/:id', async (req, res) => {
  const order = await OrderService.findById(req.params.id);
  if (!order) return res.status(404).json({ error: 'Order not found' });
  res.json(order);
});
```

**Current `openapi.yaml` has no entries for `/api/orders`.**

**Steps the agent takes:**

1. Scans `src/routes/orders.js` → extracts 2 endpoints:
   - `GET /api/orders` with query params: `status` (string, optional), `page` (integer, optional, default 1), `limit` (integer, optional, default 20)
   - `GET /api/orders/{id}` with path param: `id` (string, required)

2. Diffs against current spec → both endpoints are new (not in spec)

3. Adds to `openapi.yaml`:
   ```yaml
   paths:
     /api/orders:
       get:
         operationId: listOrders
         summary: List all orders with optional status filter
         tags: [Orders]
         parameters:
           - name: status
             in: query
             required: false
             schema:
               type: string
           - name: page
             in: query
             required: false
             schema:
               type: integer
               default: 1
           - name: limit
             in: query
             required: false
             schema:
               type: integer
               default: 20
         responses:
           '200':
             description: Successful response
             content:
               application/json:
                 schema:
                   type: object
                   properties:
                     data:
                       type: array
                       items:
                         type: object
                     total:
                       type: integer

     /api/orders/{id}:
       get:
         operationId: getOrderById
         summary: Get a single order by ID
         tags: [Orders]
         parameters:
           - name: id
             in: path
             required: true
             schema:
               type: string
         responses:
           '200':
             description: Successful response
             content:
               application/json:
                 schema:
                   type: object
           '404':
             description: Order not found
             content:
               application/json:
                 schema:
                   type: object
                   properties:
                     error:
                       type: string
   ```

4. Runs `npx @redocly/cli lint openapi.yaml` → passes with 0 errors

5. Commits: `docs(api): add GET /api/orders and GET /api/orders/{id} to OpenAPI spec`

6. Triggers `api-consumer-notifier` downstream (new endpoints are non-breaking, so no notifications needed)

**Output in STATE.md:**
```yaml
last_run: 2026-07-10T09:15:00Z
status: COMPLETE
endpoints_added: 2
endpoints_modified: 0
endpoints_potentially_removed: 0
spec_lint_errors: 0
files_changed: [openapi.yaml]
commits_made: 1
cost_usd: 0.55
```

---

## Guardrails

- Do NOT modify route handler code — only update the OpenAPI spec file
- Do NOT remove endpoints from the spec unless explicitly confirmed by a human
- Do NOT alter business logic, middleware, or authentication in route handlers
- Do NOT inline `$ref` schema references — preserve the existing reference structure
- Do NOT add example values that contain real user data or credentials
- Do NOT change the OpenAPI version or spec structure (e.g., don't convert from 3.0 to 3.1 without approval)
- Keep spec changes minimal — don't restructure the entire file when adding one endpoint
- Preserve existing descriptions, examples, and custom extensions (`x-*` fields) when updating endpoints
- If the spec becomes invalid after an update → rollback immediately, do not push a broken spec

---

## Security and Best Practices

- Never include real API keys, tokens, or secrets in spec examples
- Use generic placeholder values in examples (e.g., `"Bearer <token>"`, `"user@example.com"`)
- Ensure security schemes (`securityDefinitions`, `components/securitySchemes`) are accurate but don't expose internal auth details
- Validate that sensitive endpoints have proper security requirements defined in the spec
- All commits should be signed if the project requires it
