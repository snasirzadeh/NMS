# Future Maintenance Workflow

The original ten implementation phases are complete. Future work is normal
maintenance or a clearly scoped feature request, not another soft phase.

## Before Editing

Read `docs/project-guide/instructions.md`, `docs/PLAN.md`, and
`docs/architecture.md`. Inspect `git status`, relevant modules, tests, and
current runtime behavior. Preserve unrelated user changes.

## During Editing

Keep network logic in services, routes thin, schema changes in Alembic, and
security-sensitive behavior covered by tests. Update `README.md`, `docs/`, or
`local/` when operator behavior changes. Do not add monitoring infrastructure.

## Verification

```bash
backend/.venv/bin/pytest -q
(cd frontend && npm run build)
git diff --check
```

For Compose or Docker changes, also run `docker compose config --quiet` with
the required `.env` values, then check both health endpoints and
`docker compose ps`.

## Closeout

Report files changed, verification results, warnings, and blocked work. Do
not create or continue a phase prompt. Commit/push only when asked.
