# RingIQ
RingIQ is a B2B AI voice platform that automatically calls, qualifies, and prioritizes leads using each business’s private knowledge base.

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

The voice worker posts demo pipeline milestones back to the FastAPI server at `RINGIQ_API_BASE_URL`, so the API terminal shows LiveKit, Deepgram, Groq, and Sarvam progress logs during a test call.

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
