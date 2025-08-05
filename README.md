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

```mermaid
classDiagram
    %% Wat zijn de nuances van een aanvraag voor meerdere
    %% klanten tegelijkertijd?
    %% Zijn er subsidies bij meerdere aanbieders tegelijkertijd?
    %% BV: een subsidie die door zowel SNN als RVO wordt gegeven?
    %% Wordt er wel eens een aanvraag geschreven voor meerdere
    %% subsidies? Of altijd voor één?

    CLIENT }|--o{ APPLICATION : has
    LISTING ||--o{ APPLICATION: has
    USER }|--o{ CLIENT : has
    USER }|--o{ LISTING : has
    PROVIDER ||--o{ LISTING: has

    USER_CONTEXT |o--|| USER : has
    CLIENT_CONTEXT }o--o{ CLIENT : has
    LISTING_CONTEXT }o--o{ LISTING : has
    APPLICATION_CONTEXT }o--o{ APPLICATION : has
    PROVIDER_CONTEXT }o--o{ PROVIDER : has
    DOCUMENT_SECTION }o--|| APPLICATION: has
    DOCUMENT_COMMENT }o--|| DOCUMENT_SECTION: has
```