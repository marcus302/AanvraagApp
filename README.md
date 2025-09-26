# AanvraagApp
Write proposals for whatever blazingly fast

# DEV

## Environment

Activate dev shell.
```bash
nix develop
```

Run locally.
```
poetry run python -m debugpy --listen 0.0.0.0:5678 -m uvicorn aanvraagapp:app --host 0.0.0.0 --port 8000 --reload
```

## Database Management

### Setting up the database

To create all database tables:

```bash
poetry run python -m tests.db_utils setup
```

### Cleaning up the database

To drop all database tables:

```bash
poetry run python -m tests.db_utils teardown
```

### Database backup and restore

To create a backup of the "mark" database in plain SQL format:

```bash
docker exec -i $(docker-compose ps -q db) pg_dump -U mark -d mark \
    --no-owner \
    --no-privileges \
    --data-only \
    --inserts \
    --disable-triggers \
    > backup_mark.sql
```

This can be used for a test environment. See conftest.py.

## Linting and formatting

Check for issues:
```bash
poetry run ruff check
```

Format all python code:
```bash
poetry run ruff format
```