# RingIQ Staging Deployment

Status: backend Heroku deployment complete; frontend and LiveKit Cloud deferred to the next pass.

## Target topology

- `ringiq-staging-api`: FastAPI `web` process and PostgreSQL-backed `worker` process on Heroku EU.
- `ringiq-staging-web`: Next.js on Heroku EU (deferred).
- Heroku Postgres Essential-0 attached to the API app.
- LiveKit Cloud voice agent in `ap-south` / Mumbai (deferred).
- Generated Heroku domains for staging; no custom DNS in this phase.

## Backend process contract

The root `Procfile` declares:

- `release`: apply Alembic migrations before a release becomes active.
- `web`: bind FastAPI to Heroku's assigned `$PORT`.
- `worker`: poll PostgreSQL for campaign and click-to-call jobs.

The API normalizes Heroku's managed PostgreSQL URL to SQLAlchemy's asyncpg
dialect and requires SSL whenever `ENVIRONMENT` is not `local` or `test`.

## Backend configuration

Set these groups on `ringiq-staging-api`; never commit their values:

- Runtime: `ENVIRONMENT`, `CORS_ALLOWED_ORIGINS`, `RINGIQ_INTERNAL_API_KEY`.
- Identity: `CLERK_SECRET_KEY`, `CLERK_JWT_KEY`, `CLERK_AUTHORIZED_PARTIES`.
- LiveKit dispatch: `LIVEKIT_URL`, `LIVEKIT_API_KEY`, `LIVEKIT_API_SECRET`,
  `LIVEKIT_AGENT_NAME`, SIP trunk and timeout settings.
- Recording access: bucket, region, access key, secret, endpoint, public base URL,
  and signed URL expiry settings.
- Database: Heroku manages `DATABASE_URL` through the Postgres attachment.

Provider keys used only by the voice runtime (Deepgram, Groq, and Sarvam) do
not belong on the Heroku API app.

## Deployment order

1. Create the API app in Heroku EU on Cedar/Heroku-24.
2. Set `heroku/python` as its buildpack and provision Essential-0 Postgres.
3. Configure backend variables, initially allowing the future staging web URL.
4. Deploy the committed repository root and require a successful release phase.
5. Scale `web=1` and `worker=1` as Basic dynos.
6. Verify `/health`, migrations, process status, logs, and database connectivity.
7. In the next pass, deploy the frontend and update CORS/Clerk URLs.
8. Deploy the voice agent to LiveKit Cloud Mumbai and point it at the API URL.
9. Create the Clerk organization `Ashiana Housing`, complete onboarding, and
   run the safe demo seed. Seeded phone numbers use the reserved fictional
   `+1 202-555-01xx` range and the campaign remains a non-runnable draft.

## Verification record

- Pre-deployment API baseline: 95 tests passing.
- Pre-deployment Next.js production build: passing.
- Backend app: `ringiq-staging-api` in Heroku EU on Heroku-24.
- Backend URL: `https://ringiq-staging-api-3695f29fe3f8.herokuapp.com`.
- Deployed code: `0e65ee9` with successful release migration.
- Database: Essential-0, Alembic head `20260719_0009`, 20 public tables.
- Formation: `web=1:Basic`, `worker=1:Basic`.
- Health check: `GET /health` returned `200 {"status":"ok"}`.
- Staging database password and internal API key were rotated after verification.
- Rotate the reused Clerk test secret, LiveKit API secret, and recording-storage
  access key before the frontend/voice pass because a Heroku status command
  unexpectedly displayed config values in its output.
- Frontend deployment: deferred.
- LiveKit agent deployment: deferred.
