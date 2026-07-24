# RingIQ

RingIQ is a B2B AI voice platform that automatically calls, qualifies, and prioritizes leads using each business's private knowledge base.

[Live staging app](https://ringiq-staging-web.vercel.app/) · [Product deck](https://ringiq-product-deck.vercel.app) · [Watch the demo](https://youtu.be/T8kWorPbZrU)

[![Watch the RingIQ product demo](https://img.youtube.com/vi/T8kWorPbZrU/maxresdefault.jpg)](https://youtu.be/T8kWorPbZrU)

> These credentials are for the staging demo only.

## Voice pipeline

The current implementation connects the outbound calling pipeline without requiring a database for the `/demo/calls` flow:

```text
FastAPI demo endpoint
  -> LiveKit explicit agent dispatch
  -> LiveKit SIP outbound participant
  -> Voice AI Worker
  -> Deepgram Flux STT
  -> Groq openai/gpt-oss-20b
  -> Sarvam Bulbul v3 TTS
```

## Quick start

### Prerequisites

- Python 3.11 or newer
- [`uv`](https://docs.astral.sh/uv/)
- Configured LiveKit, SIP, Deepgram, Groq, and Sarvam credentials

### Install

Copy the environment template and install the workspace dependencies:

```bash
cp .env.example .env
uv sync
```

`uv sync` creates `.venv` when needed and keeps the environment aligned with `pyproject.toml`.

Verify the base package installation:

```bash
uv run python -m ringiq
```

### Run the services

Start each service in a separate terminal.

Voice worker:

```bash
uv run python -m apps.voice_worker.agent dev
```

API server:

```bash
uv run uvicorn apps.api.ringiq_api.main:app --reload
```

PostgreSQL job worker, required for campaign and click-to-call features:

```bash
uv run python -m apps.worker.main
```

Product call APIs enqueue work in PostgreSQL. The job worker claims those jobs and dispatches the LiveKit agent and outbound SIP participant. The `/demo/calls` endpoint dispatches directly and does not require the job worker.

### Trigger a demo call

```bash
curl -X POST http://127.0.0.1:8000/demo/calls \
  -H "Content-Type: application/json" \
  -d '{"phone_number":"+919876543210"}'
```

The phone number must use E.164 format, and a valid LiveKit SIP outbound trunk must be configured before a call can be placed.

### Runtime notes

- The voice worker reports pipeline milestones to the FastAPI server at `RINGIQ_API_BASE_URL`, so the API terminal shows LiveKit, Deepgram, Groq, and Sarvam progress.
- Keep one voice-worker process running per local environment.
- Failed call startup removes its LiveKit room.
- A voice job shuts down when its SIP participant does not arrive within `LIVEKIT_SIP_PARTICIPANT_WAIT_TIMEOUT_SECONDS`.

## Monorepo layout

```text
apps/
  api/            Core SaaS backend API
  worker/         Background jobs and asynchronous processing
  voice_worker/   Real-time Voice AI call runtime
  web/            Tenant-facing frontend app
packages/         Shared internal packages, added when needed
infra/            Local and deployment infrastructure
docs/             Implementation-facing documentation
```

Planning artifacts live in `_bmad-output/planning-artifacts`.

## Platform console

RingIQ internal users sign in through the separate platform entrance:

```text
http://localhost:3000/platform/sign-in
```

Platform identities do not belong to a Clerk organization. Enable **Allow Personal Accounts** in the Clerk dashboard so these accounts can complete sign-in. Tenant routes still require an active organization, and the API prevents a Clerk user from being both a tenant user and a platform user.

Apply the identity migrations:

```bash
uv run alembic upgrade head
```

Configure a Clerk webhook endpoint at `/webhooks/clerk`, subscribe it to
`user.created`, `user.updated`, and `user.deleted`, and set its signing secret in
`CLERK_WEBHOOK_SIGNING_SECRET`. Set `PLATFORM_INVITATION_REDIRECT_URL` to the
web application's `/platform/accept-invitation` URL.

Invite the first platform super administrator directly from RingIQ. The
bootstrap command refuses to create another invitation after a super
administrator exists or while another first-admin invitation is open:

```bash
uv run python -m scripts.bootstrap_platform_user \
  --email admin@ringiq.in \
  --display-name "RingIQ Admin"
```

The recipient follows the Clerk invitation link, creates a password, and lands
in the platform console without tenant workspace setup. Super administrators can
invite additional platform users from `/platform/users`.

For break-glass recovery, an existing dedicated Clerk identity can still be
provisioned directly. The command refuses to convert a tenant identity:

```bash
uv run python -m scripts.bootstrap_platform_user \
  --clerk-user-id user_xxxxxxxxx \
  --email admin@ringiq.in \
  --display-name "RingIQ Admin"
```

After upgrading an existing deployment, mirror all database-owned platform
identity fields into Clerk private metadata once:

```bash
uv run python -m scripts.bootstrap_platform_user --reconcile-metadata
```

RingIQ continues to authorize platform requests from PostgreSQL. Clerk private
metadata is an operational mirror and is never used as the source of roles or
account status.
