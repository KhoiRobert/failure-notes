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
