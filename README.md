# RingIQ
RingIQ is a B2B AI voice platform that automatically calls, qualifies, and prioritizes leads using each business’s private knowledge base.

## UV Setup

This repository is now ready for `uv`-based development.

Common commands:

```bash
uv sync
uv run python -m ringiq
```

`uv sync` will create `.venv` if needed and keep the environment aligned with `pyproject.toml`.

## Monorepo Layout

RingIQ is organized as a monorepo so the product services can evolve together while keeping clear ownership boundaries.

```text
apps/
  api/            Core SaaS Backend API
  worker/         Background jobs and async processing
  voice-worker/   Real-time Voice AI call runtime
  web/            Tenant-facing frontend app
packages/         Shared internal packages, added only when needed
infra/            Local and deployment infrastructure
docs/             Implementation-facing documentation
```

Planning artifacts are stored in `_bmad-output/planning-artifacts`.
