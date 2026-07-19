# RingIQ
RingIQ is a B2B AI voice platform that automatically calls, qualifies, and prioritizes leads using each business’s private knowledge base.

# Slides Deck link
https://ringiq-product-deck.vercel.app

# Live URL
https://ringiq-staging-web.vercel.app/

# Demo Creds
rohang9896@gmail.com
SYvXiXpxmj7ZwDg

## UV Setup

This repository is now ready for `uv`-based development.

Common commands:

```bash
uv sync
uv run python -m ringiq
```

`uv sync` will create `.venv` if needed and keep the environment aligned with `pyproject.toml`. The backend voice pipeline requires Python 3.11 or newer.

## Voice Pipeline Demo

The first implementation spike wires the outbound voice pipeline without a database:

```text
FastAPI demo endpoint
  -> LiveKit explicit agent dispatch
  -> LiveKit SIP outbound participant
  -> Voice AI Worker
  -> Deepgram Flux STT
  -> Groq llama-3.3-70b-versatile
  -> Sarvam Bulbul v3 TTS
```

Set up local environment variables:

```bash
cp .env.example .env
```

Install dependencies:

```bash
uv sync
```

Run the voice worker in one terminal:

```bash
uv run python -m apps.voice_worker.agent dev
```

Run the API in another terminal:

```bash
uv run uvicorn apps.api.ringiq_api.main:app --reload
```

Run the PostgreSQL job worker in a third terminal when using campaign or
click-to-call features:

```bash
uv run python -m apps.worker.main
```

Product call APIs enqueue work in PostgreSQL; this worker claims those jobs and
dispatches the LiveKit agent and outbound SIP participant. The `/demo/calls`
endpoint dispatches directly and does not require the job worker.

The voice worker posts demo pipeline milestones back to the FastAPI server at `RINGIQ_API_BASE_URL`, so the API terminal shows LiveKit, Deepgram, Groq, and Sarvam progress logs during a test call.

Keep one voice-worker process running per local environment. Failed call startup now removes its
LiveKit room, and the voice job shuts itself down if its SIP participant does not arrive within
`LIVEKIT_SIP_PARTICIPANT_WAIT_TIMEOUT_SECONDS`.

Trigger a demo call:

```bash
curl -X POST http://127.0.0.1:8000/demo/calls \
  -H "Content-Type: application/json" \
  -d '{"phone_number":"+919876543210"}'
```

The phone number must be in E.164 format. A valid LiveKit SIP outbound trunk is required before the call can be placed.

## Monorepo Layout

RingIQ is organized as a monorepo so the product services can evolve together while keeping clear ownership boundaries.

```text
apps/
  api/            Core SaaS Backend API
  worker/         Background jobs and async processing
  voice_worker/   Real-time Voice AI call runtime
  web/            Tenant-facing frontend app
packages/         Shared internal packages, added only when needed
infra/            Local and deployment infrastructure
docs/             Implementation-facing documentation
```

Planning artifacts are stored in `_bmad-output/planning-artifacts`.

## Platform Console

RingIQ internal users sign in through the separate platform entrance:

```text
http://localhost:3000/platform/sign-in
```

Platform identities do not belong to a Clerk organization. Enable **Allow Personal Accounts** in the Clerk dashboard so these accounts can complete sign-in. Tenant routes still require an active organization, and the API enforces that one Clerk user cannot be both a tenant user and a platform user.

Apply the identity migrations:

```bash
uv run alembic upgrade head
```

Create the first platform super administrator after creating its dedicated user in Clerk:

```bash
uv run python -m scripts.bootstrap_platform_user \
  --clerk-user-id user_xxxxxxxxx \
  --email admin@ringiq.in \
  --display-name "RingIQ Admin"
```

The bootstrap command refuses to convert an existing tenant identity. Subsequent platform-user invitations will be managed through the platform console in a later implementation slice.
