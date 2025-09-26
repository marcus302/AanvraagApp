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
docker exec -i $(docker-compose ps -q db) pg_dump -U mark -d mark --no-owner --no-privileges > backup_mark.sql
```

To restore a backup to a database with an arbitrary name:

```bash
# First, create the target database (replace 'new_database_name' with your desired name)
docker exec -i $(docker-compose ps -q db) psql -U mark -c "CREATE DATABASE new_database_name;"

# Then restore the backup to the new database
docker exec -i $(docker-compose ps -q db) psql -U mark -d new_database_name < backup_mark.sql
```

## Linting and formatting

Check for issues:
```bash
poetry run ruff check
```

Format all python code:
```bash
poetry run ruff format
```