# Failure Notes

Track mistakes you make and learn from them.

## Quick test with Docker (after cloning)

From the repo root:

```bash
docker-compose up
```

Then:

- **API:** http://localhost:8000  
- **Interactive API docs:** http://localhost:8000/docs  

No `.env` or config is required for this; the Compose file uses local-dev defaults.

To run in the background: `docker-compose up -d`. To stop: `docker-compose down`.

**If `curl` says "Couldn't connect to server" on port 8000:**

1. **Start the stack** (from repo root):
   ```bash
   docker-compose up -d
   ```
2. **Wait for the backend** – Postgres starts first, then the API. Give it 15–30 seconds, then:
   ```bash
   docker-compose ps
   ```
   Both `failure_notes_db` and `failure_notes_api` should be **Up** (and the API may show "healthy" after a bit).

3. **If the API container is not up or keeps restarting**, check logs:
   ```bash
   docker-compose logs backend
   ```
   Fix any errors (e.g. missing dependency, DB connection). Common fix: ensure Postgres is healthy first – `docker-compose down -v && docker-compose up -d` and wait ~30s.

4. **If port 8000 is already in use** on your machine, either stop the other process using 8000 or change the host port in `docker-compose.yml` (e.g. `"8001:8000"`), then use `http://localhost:8001` in the browser and curl.

### How to test (with Docker running)

**1. In the browser**

- Root: http://localhost:8000  
- Health: http://localhost:8000/health  
- **Interactive API docs (try all endpoints):** http://localhost:8000/docs  

**2. From the terminal (curl)**

```bash
# Health check
curl http://localhost:8000/health

# Register a user (password must be 8+ chars)
curl -s -X POST http://localhost:8000/users/register \
  -H "Content-Type: application/json" \
  -d '{"username":"testuser","email":"test@example.com","password":"password123"}'

# Login and get token (use the same email/password)
curl -s -X POST http://localhost:8000/users/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"password123"}'
# Copy the "token" from the JSON response, then:

# Call a protected endpoint (replace YOUR_TOKEN with the token from login)
curl -s http://localhost:8000/users/me -H "Authorization: Bearer YOUR_TOKEN"
```

**3. Verify authorization (protected endpoints)**

Authorization is working if:

- **Without token** → 401 Unauthorized:
  ```bash
  curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/users/me
  # Expect: 401
  ```
- **With valid token** → 200 and your user JSON:
  ```bash
  # 1) Login and save token
  TOKEN=$(curl -s -X POST http://localhost:8000/users/login \
    -H "Content-Type: application/json" \
    -d '{"email":"test@example.com","password":"password123"}' | python3 -c "import sys,json; print(json.load(sys.stdin).get('token',''))")
  # 2) Call protected endpoint
  curl -s http://localhost:8000/users/me -H "Authorization: Bearer $TOKEN"
  # Expect: 200 and JSON with id, username, email
  ```

**4. One-shot auth check**

From the repo root (with API running):

```bash
chmod +x scripts/verify_auth.sh && ./scripts/verify_auth.sh
```

This checks: no token → 401, valid token → 200, invalid token → 401.

**5. Using Swagger UI (http://localhost:8000/docs)**

1. Open http://localhost:8000/docs  
2. Call **POST /users/login** with `{"email":"test@example.com","password":"password123"}` (register first if needed).  
3. Copy the `token` from the response.  
4. Click **Authorize**, paste the token (with or without "Bearer "), then **Authorize**.  
5. Call **GET /users/me** – it should return 200 and your user. Call it without authorizing first to see 401.

## What this does

1. **Record mistakes** – Save mistakes with context (conversation, code, etc.)
2. **Classify mistakes** – Determine what type of mistake it is
3. **Get recommendations** – Suggestions to avoid repeating the same mistake
4. **Get alerts** – Notifications (e.g. Slack/Gmail) when you exceed a limit
5. **Compare with others** – See how your mistake count compares

## Project layout

- **`notes/`** – Python (FastAPI) backend; API and DB access
- **`db/`** – PostgreSQL schema and init script; see [db/README.md](db/README.md)
- **`config/`** – Example configs; copy and edit for local/production (see `.example` files)
- **`docs/`** – [Best practices review](docs/BEST_PRACTICES_REVIEW.md) (what’s in place and what’s optional)

## Setup (non-Docker)

1. Configure database in `config/database.yml` (use `config/database.yml.example` as template)
2. Set alert limits in `config/thresholds.yml`
3. Add Slack/Gmail in `config/integrations.yml`
4. For the API: `cd notes`, copy `notes/.env.example` to `notes/.env`, then run the app (e.g. `uvicorn app.main:app --reload`)

## Security & secrets

- Do **not** commit `.env` or real `config/database.yml` / `config/integrations.yml` / `config/thresholds.yml` (they are in `.gitignore`).
- Use `notes/.env.example` as a template; copy to `notes/.env` and fill in values locally only.
- In production, set `SECRET_KEY`, `JWT_SECRET_KEY`, and `DATABASE_URL` via environment variables or your host’s secrets.
