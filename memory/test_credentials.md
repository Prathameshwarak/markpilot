# MarketPilot — Test Credentials

## Admin / Owner
- Email: `sayuswaru28@gmail.com`
- Password: `MarketPilot@2026`
- Role: admin

## Demo user
- Email: `demo@marketpilot.in`
- Password: `Demo1234!`
- Role: user

## Auth endpoints
- POST `/api/auth/register`
- POST `/api/auth/login`
- POST `/api/auth/logout`
- GET  `/api/auth/me`
- POST `/api/auth/refresh`
- POST `/api/auth/forgot-password`
- POST `/api/auth/reset-password`

Notes:
- JWT cookies are httpOnly + Secure + SameSite=None. Over plain http (e.g. FastAPI
  TestClient) the browser/jar will not resend Secure cookies — pass the `access_token`
  cookie value as `Authorization: Bearer <token>` in that case.
