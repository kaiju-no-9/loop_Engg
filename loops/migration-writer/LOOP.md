# LOOP.md — migration-writer

> Detect database schema changes and automatically generate the corresponding database migration files.

---

## Loop Definition

```yaml
name: migration-writer
version: "1.0"

objective: "Detect database schema or model changes and automatically generate and validate migration files"
# The loop succeeds when no schema drift is detected and all generated migrations pass validation.

cadence: "event-driven"      # Triggered on schema changes

tools:
  - bash                    # Run migrations, schema generation CLI
  - file_edit               # Create/modify migrations or schema files
  - git                     # Commit generated migrations

file_scope:
  allow:
    - "prisma/**"           # Prisma schema and migrations
    - "db/**"               # DB schemas, models, and migrations
    - "src/db/**"           # Nested database files
    - "src/models/**"       # Database models
    - "package.json"        # Project configurations
    - ".loops/migration-writer/**" # Local state, config, and logs
  deny:
    - ".env*"               # Never touch environment files
    - "*.secret"            # Never touch secrets
    - "*.key"               # Never touch keys
    - "infrastructure/**"   # Never touch infra
    - "node_modules/**"     # Never touch dependencies
    - "dist/**"             # Never touch build output
    - ".github/**"          # Never touch CI config

verifier:
  type: script
  command: "bash .loops/migration-writer/verify-schema.sh" # Command that verifies migrations match model files
  timeout_seconds: 180

termination:
  success:
    - schema_in_sync          # verifier.command exits 0 (no pending/untracked changes)
  failure:
    - max_iterations: 8      # Stops after 8 generate-verify runs
    - budget_exhausted       # Stops when token or dollar limit is hit

budget:
  max_tokens: 80000          # Per-run token cap
  max_cost_usd: 3.00         # Hard stop — never exceed this per run

approval_required_for:
  - push_to_main             # Always ask before merging to main
  - delete_files             # Always ask before deleting files
  - apply_migration_to_prod  # Ask before applying migrations to production

triggers:
  on_success: []
  on_failure:
    - notify-slack           # Alert team if migration generation or validation fails

recovery:
  strategy: rollback_last_commit
  max_retries: 2
  escalation: human

merge_strategy: pr
branch_prefix: loop/migration-writer

state_file: .loops/migration-writer/STATE.md
skill_file: .loops/migration-writer/SKILL.md
```

---

## How This Loop Works

### The Cycle

```
1. Loop triggers when database model or schema files change
2. Planner reads STATE.md + SKILL.md, runs validation script to check schema alignment
3. Planner compares model files (e.g. schema.prisma, SQLAlchemy models) with existing migration history
4. If schema drift is detected:
   a. Planner executes DB migration generator (e.g. prisma migrate dev --create-only, alembic revision)
   b. Planner generates custom migration SQL if necessary
   c. Worker writes or refines the migration script files
5. Verifier runs schema checks to confirm schema matches migrations and has zero validation errors
6. If validation passes -> commit changes atomically and open a PR
7. If validation fails -> iterate or rollback and escalate
```

### Dry Run

```bash
antigravity /loop migration-writer --dry-run
```

Checks database models for schema drift and outputs the migration plan/SQL without writing migration files to disk.

### One-Shot Run

```bash
antigravity /loop migration-writer
```

Executes the full schema audit, migration writing, and validation cycle once.

---

## What "Done" Means

The loop is **COMPLETE** when:
- All schema drift is resolved by generating corresponding migration files
- The generated migrations successfully compile/validate without errors
- All modifications are committed atomically to a feature branch
- STATE.md is updated with generated migrations and schema status

The loop is **BLOCKED** when:
- `max_iterations` (8) is reached
- Budget is exhausted ($3.00 or 80,000 tokens)
- The generator detects destructive changes (e.g. drop table/column) and requires human approval
- `waiting_for_human: true` is set in STATE.md

---

## Scoping Rules

- **Write access:** Migration directories (`db/migrations/**`, `prisma/migrations/**`), schema files, and state logs.
- **Read access:** Database models (`src/models/**`), package configs, and existing migration history.
- **Never touch:** Environment configurations, frontend files, application business logic.
- **One loop = one scope:** migration-writer only writes and checks database migration scripts. It does not alter application routes, test suites, or deployment pipelines.
