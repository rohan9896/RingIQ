# Core SaaS Backend API

FastAPI service for RingIQ's core product backend.

This service owns tenant-scoped product workflows such as:

- Tenant and organization mapping.
- Lead upload and lifecycle state.
- Campaign setup and readiness.
- Knowledge base Q&A records.
- Call records and dashboard APIs.
- Provider webhooks where required.

It should remain the product source of truth. Real-time call execution belongs in `apps/voice_worker`.

## Demo endpoint

```bash
uv run uvicorn apps.api.ringiq_api.main:app --reload
```

```bash
curl -X POST http://127.0.0.1:8000/demo/calls \
  -H "Content-Type: application/json" \
  -d '{"phone_number":"+919876543210"}'
```
