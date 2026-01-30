#!/usr/bin/env bash
# Verify API authorization: no token → 401, valid token → 200.
# Usage: ./scripts/verify_auth.sh   (API must be running at http://localhost:8000)

set -e
BASE="${BASE_URL:-http://localhost:8000}"

echo "1. Without token: GET /users/me should return 401"
CODE=$(curl -s -o /dev/null -w "%{http_code}" "$BASE/users/me")
if [ "$CODE" = "401" ]; then
  echo "   OK: got 401"
else
  echo "   FAIL: expected 401, got $CODE"
  exit 1
fi

echo "2. Register + login and GET /users/me with token should return 200"
curl -s -X POST "$BASE/users/register" \
  -H "Content-Type: application/json" \
  -d '{"username":"authuser","email":"auth@example.com","password":"password123"}' > /dev/null || true
LOGIN=$(curl -s -X POST "$BASE/users/login" \
  -H "Content-Type: application/json" \
  -d '{"email":"auth@example.com","password":"password123"}')
TOKEN=$(echo "$LOGIN" | python3 -c "import sys,json; print(json.load(sys.stdin).get('token',''))")
if [ -z "$TOKEN" ]; then
  echo "   FAIL: no token from login"
  exit 1
fi
CODE=$(curl -s -o /dev/null -w "%{http_code}" "$BASE/users/me" -H "Authorization: Bearer $TOKEN")
if [ "$CODE" = "200" ]; then
  echo "   OK: got 200 with token"
else
  echo "   FAIL: expected 200, got $CODE"
  exit 1
fi

echo "3. Invalid token should return 401"
CODE=$(curl -s -o /dev/null -w "%{http_code}" "$BASE/users/me" -H "Authorization: Bearer invalid-token-12345")
if [ "$CODE" = "401" ]; then
  echo "   OK: got 401 for invalid token"
else
  echo "   FAIL: expected 401 for invalid token, got $CODE"
  exit 1
fi

echo ""
echo "Authorization is working correctly."
