# Failure Notes

Track mistakes you make and learn from them.

## What This Does

1. **Record mistakes** - Save mistakes with context (conversation, code, etc.)
2. **Classify mistakes** - Automatically determine what type of mistake it is
3. **Get recommendations** - Suggestions on how to avoid making the same mistake again
4. **Get alerts** - If you make the same mistake more than N times, get notified via Slack or Gmail
5. **Compare with others** - See how many mistakes you make compared to other people

## How It Works

- All mistakes are stored in a database
- Each person has their own mistake records
- The system tracks how many times you make each type of mistake
- When you exceed a limit, you get an alert

## Setup

1. Configure database connection in `config/database.yml`
2. Set alert limits in `config/thresholds.yml` (how many mistakes before alert)
3. Add Slack/Gmail settings in `config/integrations.yml`

## Security & secrets (before pushing to GitHub)

- **Never commit** `.env` or real `config/database.yml` / `config/integrations.yml` / `config/thresholds.yml` — they are in `.gitignore`.
- Use **`notes/.env.example`** as a template: copy to `notes/.env` and fill in real values locally only.
- **Production**: set `SECRET_KEY`, `JWT_SECRET_KEY`, and `DATABASE_URL` via environment variables or your host’s secrets; do not use the defaults from code.
- **Docker Compose** in this repo uses local-dev defaults (`postgres`/`postgres`); for production, use env vars or a managed database.
