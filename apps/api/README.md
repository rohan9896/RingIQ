# Core SaaS Backend API

FastAPI service for RingIQ's core product backend.

This service owns tenant-scoped product workflows such as:

- Tenant and organization mapping.
- Lead upload and lifecycle state.
- Campaign setup and readiness.
- Knowledge base Q&A records.
- Call records and dashboard APIs.
- Provider webhooks where required.

It should remain the product source of truth. Real-time call execution belongs in `apps/voice-worker`.

