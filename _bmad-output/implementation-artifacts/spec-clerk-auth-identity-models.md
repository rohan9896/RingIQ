---
title: 'Clerk Auth And Identity Models'
type: 'feature'
created: '2026-07-17'
status: 'done'
review_loop_iteration: 0
baseline_commit: '67e305ce41202ec37946324ea0f0c2a2fe627739'
context:
  - '{project-root}/_bmad-output/planning-artifacts/architecture/architecture-RingIQ-2026-07-17/ARCHITECTURE-SPINE.md'
  - '{project-root}/_bmad-output/planning-artifacts/architecture/architecture-RingIQ-2026-07-17/ringiq-low-level-design-and-erd.md'
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** RingIQ has no persistence foundation or authenticated tenant context, so API routes cannot safely associate a Clerk user and active Organization with internal product data.

**Approach:** Add asynchronous SQLAlchemy/Alembic foundations, implement `Tenant`, `User`, and `TenantMembership` models, verify Clerk session tokens through the official Python SDK, resolve an active local membership, and expose a protected `/v1/me` route.

## Boundaries & Constraints

**Always:** Use Clerk's official `clerk-backend-api`; accept session tokens only; validate authorized parties; require an active Clerk Organization; keep Clerk IDs as unique external identifiers rather than primary keys; return consistent 401/403 responses; use async database access; keep dependencies injectable for tests; preserve the existing public health and demo endpoints.

**Ask First:** Any change that requires creating production database roles, changing Clerk Dashboard configuration, or replacing Clerk/SQLAlchemy with another provider or persistence stack.

**Never:** Store passwords or session tokens; trust client-supplied tenant IDs; authorize from Clerk Organization claims without resolving an active internal membership; implement RBAC, Clerk webhooks, frontend sign-in UI, remaining ERD models, or production RLS role provisioning in this slice.

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected Output / Behavior | Error Handling |
|----------|--------------|---------------------------|----------------|
| Authenticated member | Valid session token with active org and active local mapping | `/v1/me` returns internal user, tenant, membership, and Clerk identity IDs | N/A |
| Missing/invalid token | No token, expired token, wrong signature, wrong authorized party, or non-session token | Request is rejected | 401 with `WWW-Authenticate: Bearer`; never expose token |
| No active organization | Valid user session without Clerk Organization ID | Request is rejected | 403 `active_organization_required` |
| Mapping missing | Valid Clerk identity but tenant/user/membership is absent or inactive | Request is rejected without auto-provisioning | 403 `tenant_membership_not_provisioned` |
| Database unavailable | Token valid but identity lookup fails | Request fails without treating user as unauthorized | 503 and server-side diagnostic log |

</frozen-after-approval>

## Code Map

- `pyproject.toml` -- Add SQLAlchemy, asyncpg, Alembic, Clerk SDK, and test dependencies.
- `.env.example` -- Document database and Clerk backend variables without secrets.
- `apps/api/ringiq_api/config.py` -- Parse database URL, Clerk keys, and authorized-party list.
- `apps/api/ringiq_api/db/` -- Declarative base, timestamp mixin, async engine, and session dependency.
- `apps/api/ringiq_api/models/identity.py` -- Tenant, user, and membership ORM models with UUID keys and uniqueness constraints.
- `alembic.ini` and `migrations/` -- Initial identity schema migration and async migration environment.
- `apps/api/ringiq_api/auth/` -- Clerk verification service, principal type, and tenant-context dependency.
- `apps/api/ringiq_api/routes/me.py` -- Protected identity-context endpoint.
- `apps/api/ringiq_api/main.py` -- Register the protected router and database lifecycle.
- `tests/api/` -- Model, configuration, authentication, membership, and route tests.

## Tasks & Acceptance

**Execution:**
- [x] Add dependency and environment configuration for async PostgreSQL and Clerk.
- [x] Add database base/session modules and the three identity ORM models.
- [x] Add and validate the initial Alembic migration.
- [x] Implement injectable Clerk session verification and typed principal extraction.
- [x] Implement active internal membership resolution and `/v1/me`.
- [x] Add focused tests for every I/O matrix case and model constraint.

**Acceptance Criteria:**
- Given a clean database, when migrations run, then identity tables and required unique/index constraints are created successfully.
- Given an existing active tenant/user/membership mapping, when a valid Clerk session for that active Organization calls `/v1/me`, then the matching internal context is returned.
- Given an existing public endpoint, when called without Clerk credentials, then its existing behavior is unchanged.
- Given test execution without external Clerk or PostgreSQL access, when dependencies are overridden, then auth and route behavior can be tested deterministically.

## Spec Change Log

## Design Notes

Use `clerk_backend_api.authenticate_request()` with `AuthenticateRequestOptions(jwt_key=..., secret_key=..., authorized_parties=..., accepts_token=["session_token"])`. Clerk v2 Organization claims are read from the SDK-normalized payload. Local membership lookup remains authoritative for RingIQ tenant access; synchronization will be added through a later webhook story.

## Verification

**Commands:**
- `uv sync --group dev` -- passed; runtime and test dependencies resolved into `uv.lock`.
- `.venv/bin/pytest -q` -- passed; 26 tests, with one upstream Starlette deprecation warning.
- `.venv/bin/python -m compileall -q apps migrations tests` -- passed.
- `git diff --check` -- passed.
- Alembic upgrade/downgrade is covered against temporary SQLite; configured PostgreSQL was not mutated.

## Suggested Review Order

**Request Boundary**

- Start with the protected endpoint and its resolved tenant-context contract.
  [`me.py:9`](../../apps/api/ringiq_api/routes/me.py#L9)

- Active local membership remains authoritative after Clerk authenticates the request.
  [`context.py:30`](../../apps/api/ringiq_api/auth/context.py#L30)

- Clerk verification accepts session tokens only and requires an active Organization.
  [`clerk.py:36`](../../apps/api/ringiq_api/auth/clerk.py#L36)

**Persistence**

- Shared-schema identity models preserve external Clerk IDs behind internal UUID keys.
  [`identity.py:16`](../../apps/api/ringiq_api/models/identity.py#L16)

- Membership constraints enforce tenant-user uniqueness and cascading ownership.
  [`identity.py:74`](../../apps/api/ringiq_api/models/identity.py#L74)

- Initial migration creates identity constraints, indexes, and reversible table order.
  [`20260717_0001_identity_models.py:19`](../../migrations/versions/20260717_0001_identity_models.py#L19)

**Operational Boundaries**

- Voice and identity settings load independently to preserve the existing demo pipeline.
  [`config.py:21`](../../apps/api/ringiq_api/config.py#L21)

- Async sessions are cached, injectable, and map store failures to service unavailability.
  [`session.py:19`](../../apps/api/ringiq_api/db/session.py#L19)

- Application lifespan disposes database resources without changing existing public routes.
  [`main.py:10`](../../apps/api/ringiq_api/main.py#L10)

**Verification**

- Route tests prove tenant output and demo independence from identity configuration.
  [`test_me_route.py:27`](../../tests/api/test_me_route.py#L27)

- Database-backed model tests exercise external-ID uniqueness and status checks.
  [`test_models.py:27`](../../tests/api/test_models.py#L27)

- Migration tests execute upgrade and downgrade without external infrastructure.
  [`test_migrations.py:7`](../../tests/api/test_migrations.py#L7)
