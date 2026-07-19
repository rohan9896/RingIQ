# RingIQ Staging Deployment

Status: backend Heroku deployment complete; self-hosted LiveKit voice worker deployment in progress; frontend deferred.

## Target topology

- `ringiq-staging-api`: FastAPI `web`, PostgreSQL-backed `worker`, and LiveKit
  `voice` processes on Heroku EU.
- `ringiq-staging-web`: Next.js on Heroku EU (deferred).
- Heroku Postgres Essential-0 attached to the API app.
- LiveKit Cloud media project in `ap-south` / Mumbai, with the voice agent
  self-hosted as a Heroku dyno because managed Agent Deployments are not enabled
  for this LiveKit project.
- Generated Heroku domains for staging; no custom DNS in this phase.

## Backend process contract

The root `Procfile` declares:

- `release`: apply Alembic migrations before a release becomes active.
- `web`: bind FastAPI to Heroku's assigned `$PORT`.
- `worker`: poll PostgreSQL for campaign and click-to-call jobs.
- `voice`: connect the Python voice agent to LiveKit Cloud.

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

The Heroku app also contains the Deepgram, Groq, and Sarvam provider keys needed
by its isolated `voice` process. Recording remains disabled until replacement
storage credentials are configured.

## Deployment order

1. Create the API app in Heroku EU on Cedar/Heroku-24.
2. Set `heroku/python` as its buildpack and provision Essential-0 Postgres.
3. Configure backend variables, initially allowing the future staging web URL.
4. Deploy the committed repository root and require a successful release phase.
5. Scale `web=1` and `worker=1` as Basic dynos.
6. Verify `/health`, migrations, process status, logs, and database connectivity.
7. In the next pass, deploy the frontend and update CORS/Clerk URLs.
8. Deploy the self-hosted voice process on Heroku and connect it to the LiveKit
   Cloud Mumbai project with a dedicated staging agent name.
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
- LiveKit CLI: authenticated to project `ringiq` with a fresh project credential.
- Local voice-agent container: Python image built and startup command verified
  for both native and `linux/amd64` targets.
- LiveKit managed deployment: unavailable because Agent Deployments are not
  enabled for this project; pending deployment `CA_YHg7RnuTdMBG` was not built.
- Self-hosted LiveKit voice dyno: deployment in progress on Heroku, connected to
  the LiveKit `ap-south` / Mumbai project as `ringiq-staging-agent`.
- Recording: disabled and the previously exposed storage values removed.
