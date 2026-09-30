# MarketPilot Auth Testing Playbook

Admin: `sayuswaru28@gmail.com` / `MarketPilot@2026`
Demo:  `demo@marketpilot.in` / `Demo1234!`

## Step 1 — MongoDB
```
mongosh
use test_database
db.users.find({role:"admin"}).pretty()
```
Verify bcrypt hash starts with `$2b$`. Indexes: users.email (unique),
login_attempts.identifier/email, password_reset_tokens.expires_at (TTL) & token_hash (unique),
password_reset_requests.email & created_at (TTL).

## Step 2 — API
```
curl -c cookies.txt -X POST http://localhost:8001/api/auth/login \
  -H "Content-Type: application/json" -d '{"email":"demo@marketpilot.in","password":"Demo1234!"}'
curl -b cookies.txt http://localhost:8001/api/auth/me
```

## Step 3 — Password reset (local)
Set `FRONTEND_URL="http://localhost:3000"` in `/app/backend/.env`, restart backend. The
reset link is written to the backend log (loopback fallback). Restore the https origin after.

1. Register a test account.
2. forgot-password for a registered vs unregistered email → identical generic 200 bodies.
3. Reset via the logged link; old password fails, new works, link cannot be reused.
4. Throttle: 6 requests for a fresh email → only first 5 create token docs.
5. Lockout clearance: 5 failed logins → reset → immediate login succeeds.

## Notes
- MarketPilot places NO orders. Kotak Neo adapter is read-only; `order_execution: disabled`.
- All market/fundamental/news data in V1 is deterministic mock data.
