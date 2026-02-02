# Database Setup

This directory contains the database schema and initialization.

## Structure

```
db/
├── init.sql    # Initial schema (users, sessions, root_causes, scenarios, user_root_causes)
└── README.md
```

## Quick Start

From the **repo root**:

```bash
docker-compose up
```

- Schema is created from `init.sql` on first startup.
- API: http://localhost:8000 | Docs: http://localhost:8000/docs

## init.sql

Creates tables: `users`, `sessions`, `root_causes`, `scenarios`, `user_root_causes`. Mounted by Docker as `01-init.sql`; runs only when the database is initialized (empty volume).

## Connection (Docker default)

| Setting    | Value        |
|-----------|--------------|
| Host      | localhost    |
| Port      | 5432         |
| Database  | failure_notes|
| Username  | postgres     |
| Password  | postgres     |

## Inspect schema

```bash
docker exec -it failure_notes_db psql -U postgres -d failure_notes -c "\dt"
```
