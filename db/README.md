# Database Setup

This directory contains database initialization and migration scripts.

## Structure

```
db/
├── init.sql          # Initial database schema
├── migrations/       # Database migration scripts
└── seeds/           # Seed data (optional)
```

## Quick Start

From the **repo root**, start the full stack (PostgreSQL + API):

```bash
docker-compose up
```

- The database schema is created automatically from `init.sql` on first startup.
- The API runs at http://localhost:8000 (docs at http://localhost:8000/docs).

No `.env` file is needed when using Docker Compose; it uses built-in dev defaults.

## Files

- **init.sql** - Creates all tables, indexes, and triggers
- **migrations/** - Future database migrations go here
- **seeds/** - Optional seed data for development

## Manual Execution

If you need to run the init script manually:

```bash
docker exec -it failure_notes_db psql -U postgres -d failure_notes -f /docker-entrypoint-initdb.d/init.sql
```

## Connection Details

- **Host:** localhost
- **Port:** 5432
- **Database:** failure_notes
- **Username:** postgres
- **Password:** postgres
