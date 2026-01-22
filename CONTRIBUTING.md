# How to Use This

## Record a Mistake

When you make a mistake, record it with:
- Your name/ID
- What happened (the mistake)
- The context (conversation, code, situation)
- What type of mistake it is (or let the system figure it out)

## What Happens

1. The mistake is saved in the database
2. The system figures out what type of mistake it is
3. You get recommendations on how to avoid it
4. If you make the same mistake too many times, you get an alert (Slack or Gmail)
5. You can see how your mistakes compare to others

## Configuration Files

- `config/database.yml` - Where to connect to the database
- `config/thresholds.yml` - How many mistakes before sending an alert
- `config/integrations.yml` - Slack and Gmail settings for alerts
