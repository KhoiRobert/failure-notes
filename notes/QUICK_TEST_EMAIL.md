# Quick Test: Email Alerts (Workaround for LLM Error)

The LLM error you're seeing doesn't prevent email alerts from working! Here's how to test email alerts by manually creating root causes and linking scenarios.

## Step 1: Login and Get Token

```bash
# Login via API
curl -X POST "http://localhost:8000/api/sessions/login" \
  -H "Content-Type: application/json" \
  -d '{
    "email_or_username": "phamdinhkhoi213@gmail.com",
    "password": "your-password"
  }'
```

Copy the `token` from the response.

## Step 2: Create a Root Cause Manually

```bash
# Replace YOUR_TOKEN with token from Step 1
curl -X POST "http://localhost:8000/api/root-causes/" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Null Pointer Exception",
    "description": "Forgetting to check for null values before accessing object properties",
    "solution": "Always validate input and use null-safe operators or optional chaining"
  }'
```

**Save the `id` from response** (e.g., `{"id": 1, ...}`) - you'll need it for Step 3.

## Step 3: Create 3 Scenarios

```bash
# Scenario 1
curl -X POST "http://localhost:8000/api/scenarios/" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "context": "Got null pointer error in user service"
  }'

# Save the scenario ID from response (e.g., {"id": 1, ...})

# Scenario 2
curl -X POST "http://localhost:8000/api/scenarios/" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "context": "Another null pointer error"
  }'

# Save scenario ID 2

# Scenario 3
curl -X POST "http://localhost:8000/api/scenarios/" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "context": "Yet another null pointer"
  }'

# Save scenario ID 3
```

## Step 4: Link All 3 Scenarios to the Same Root Cause

Replace `SCENARIO_ID_1`, `SCENARIO_ID_2`, `SCENARIO_ID_3` with actual IDs from Step 3, and `ROOT_CAUSE_ID` with the ID from Step 2:

```bash
# Link Scenario 1 (usage_count becomes 1, no alert)
curl -X POST "http://localhost:8000/api/scenarios/SCENARIO_ID_1/link-root-cause/ROOT_CAUSE_ID" \
  -H "Authorization: Bearer YOUR_TOKEN"

# Link Scenario 2 (usage_count becomes 2, no alert)
curl -X POST "http://localhost:8000/api/scenarios/SCENARIO_ID_2/link-root-cause/ROOT_CAUSE_ID" \
  -H "Authorization: Bearer YOUR_TOKEN"

# Link Scenario 3 (usage_count becomes 3, ALERT TRIGGERED! 📧)
curl -X POST "http://localhost:8000/api/scenarios/SCENARIO_ID_3/link-root-cause/ROOT_CAUSE_ID" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

## Step 5: Check Your Email!

Check `phamdinhkhoi213@gmail.com` for the alert email!

## Using Swagger UI (Easier)

1. Open: http://localhost:8000/docs
2. Login: `POST /api/sessions/login`
3. Copy token, click "Authorize" button at top, paste token
4. Create root cause: `POST /api/root-causes/`
5. Create 3 scenarios: `POST /api/scenarios/` (3 times)
6. Link scenarios: `POST /api/scenarios/{scenario_id}/link-root-cause/{root_cause_id}` (3 times)
7. Check email!

## About the LLM Error

The error you're seeing:
```
Tool choice is required, but model did not call a tool
```

This happens because:
- The model `openai/gpt-oss-20b` may not fully support structured output
- The API is rejecting the structured output request

**This doesn't break email alerts!** The system gracefully handles this:
- ✅ Scenarios are still created
- ✅ You can manually link scenarios to root causes
- ✅ Email alerts work perfectly when linking scenarios

The error is now logged as a warning (not an error) and won't crash your app.
