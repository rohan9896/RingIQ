# Background Worker

Async worker service for non-real-time jobs backed by PostgreSQL leases.

## Run

```bash
uv run python -m apps.worker.main
```

Process at most one currently due job:

```bash
uv run python -m apps.worker.main --once
```

Planned responsibilities:

- CSV import processing.
- Lead validation jobs.
- Knowledge chunking.
- Embedding generation.
- Campaign outbound-call initiation.
- Unanswered-call retry scheduling.
- Post-call summarization.
- Knowledge gap extraction.

This service should execute product workflows defined by the Core SaaS Backend, not own product policy independently.
