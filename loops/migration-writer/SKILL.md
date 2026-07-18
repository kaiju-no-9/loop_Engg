---
name: migration-writer-skill
description: >
  Detects database schema changes and generates migration SQL or framework code.
  Trigger on 'write migration' or 'generate schema changes'. Do NOT use for general
  query writing.
---

# Migration Writer Skill

An agent skill for scanning database models or schema definitions, detecting drift against migration history, generating schema migrations, and validating them before committing.

---

## When to Use This Skill

Use this skill when:
- Model files (Prisma schemas, SQLAlchemy models, TypeORM entities) are modified
- Database migrations need to be created automatically based on code changes
- You need to validate that existing migration files match the current model schemas
- Database migrations must be generated without manual drafting

Do NOT use this skill for:
- Writing general application CRUD queries or database seed scripts
- Running migrations directly on production databases without safety gates
- Performing major data seeding or migrations containing raw sensitive data
- Modifying frontend views or unrelated API routes

---

## Quick Reference

| Framework | CLI Command (Generate) | Migration Path |
|---|---|---|
| **Prisma** | `prisma migrate dev --create-only` | `prisma/migrations/` |
| **Alembic** | `alembic revision --autogenerate -m "msg"` | `alembic/versions/` |
| **Sequelize** | `sequelize migration:generate --name msg` | `migrations/` |
| **TypeORM** | `typeorm migration:generate src/migrations/msg` | `src/migrations/` |
| **Django** | `python manage.py makemigrations` | `*/migrations/` |

---

## Workflow: Detect Schema Drift

1. **Verify database models** — read model/schema definitions (e.g. `schema.prisma` or Python/TS entity files).
2. **Check sync status** — execute the framework's schema status or dry-run command:
   ```bash
   # Example for Prisma
   npx prisma migrate status
   
   # Example for Django
   python manage.py makemigrations --check --dry-run
   ```
3. **Parse differences** — if the check command reports drift, identify the specific model additions, modifications, or deletions.

---

## Workflow: Generate Migration Files

1. **Invoke generator CLI** — run the appropriate framework CLI command to scaffold migration files:
   ```bash
   # Prisma
   npx prisma migrate dev --create-only --name add_user_roles
   
   # Alembic
   alembic revision --autogenerate -m "add_user_roles"
   ```
2. **Review generated files** — open the new migration file to ensure the SQL or framework code correctly reflects the schema updates.
3. **Handle custom logic** — if the CLI fails to capture specific requirements (e.g. default values, index constraints), manually adjust the migration file contents.

---

## Workflow: Validate & Commit Migrations

1. **Run dry-run migration** — apply the generated migration to a local or temporary test database to ensure there are no syntax or constraint errors.
2. **Verify status** — run the schema verification script defined in `verifier.command` to verify models match migrations.
3. **Commit atomically**:
   ```bash
   git add prisma/schema.prisma prisma/migrations/
   git commit -m "db(migration): generate migration for user roles schema addition"
   ```

---

## Decision Rules

- If the schema change contains destructive operations (e.g. `DROP TABLE`, `DROP COLUMN`, altering types that cause data loss) → stop, set `waiting_for_human: true` in `STATE.md`, and log the warning. Do NOT apply or commit.
- If the framework CLI supports auto-generation → always use the CLI command instead of writing raw SQL from scratch.
- If multiple models are changed at once → generate a single consolidated migration file, listing all changes in the commit message.
- If local database connection credentials are missing → do NOT guess or prompt for production credentials; use the local dev environment connection.

---

## Example

**Input:** User adds a `phone` field to the `User` model in `schema.prisma`.

**Steps the agent takes:**
1. Runs `prisma migrate status` and detects schema drift (models have `phone` but database migrations do not).
2. Runs `npx prisma migrate dev --create-only --name add_phone_to_user`.
3. Inspects the generated SQL migration file:
   ```sql
   -- AlterTable
   ALTER TABLE "User" ADD COLUMN "phone" TEXT;
   ```
4. Verifies the SQL is non-destructive (adding a nullable column).
5. Runs verification checks.
6. Commits the `schema.prisma` and generated migration directory.

**Output:**
```
[INFO] Schema drift detected.
[INFO] Generated migration: prisma/migrations/20260718143000_add_phone_to_user/migration.sql
[INFO] Validation successful. Committing migration...
```

---

## Guardrails

- Never modify historic migration files that have already been applied/committed.
- Never hardcode environment secrets or API tokens inside migrations.
- Never ignore destructive migration warnings from the framework CLI.
