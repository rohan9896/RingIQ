---
title: 'Platform user invitations and Clerk synchronization'
type: 'feature'
created: '2026-07-21'
status: 'done'
review_loop_iteration: 0
baseline_commit: 'e82c489a1fffeaeda400b344839fa7fba57c6e29'
context:
  - '{project-root}/_bmad-output/planning-artifacts/architecture/architecture-RingIQ-2026-07-17/ARCHITECTURE-SPINE.md'
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** Platform operators currently borrow tenant signup, which redirects organization-less accounts to `/workspace/setup`, and platform provisioning depends on a manual local database bootstrap without durable Clerk synchronization.

**Approach:** Add invitation-only platform onboarding with synchronous completion plus idempotent Clerk webhooks. PostgreSQL remains authoritative for realm, role, and status; Clerk private metadata is an operational mirror only.

## Boundaries & Constraints

**Always:** Keep platform and tenant accounts separate; require no active Clerk organization for platform access; authorize from active PostgreSQL identity state; verify webhook signatures against the raw body; deduplicate delivery IDs; correlate onboarding through an opaque backend-created invitation UUID; retain tenant `/workspace/setup`; keep the existing Clerk MFA code UI.

**Ask First:** Expanding synchronization to Clerk organizations/memberships, changing tenant provisioning, allowing an existing tenant account to become platform, or making Clerk metadata/JWT claims authoritative.

**Never:** Trust client-supplied roles or unsafe metadata; provision from an unverified/unknown invitation; expose the role in invitation metadata; hard-delete local users from Clerk deletion; store webhook secrets or payloads in source control.

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected Output / Behavior | Error Handling |
|----------|---------------|----------------------------|----------------|
| Invite platform user | Super admin submits new email, display name, valid role | Create 30-day Clerk application invitation and pending local record | Existing/pending/tenant email returns 409; Clerk failure marks invite failed |
| Accept invitation | Valid ticket, matching verified email, personal session | Idempotently provision active platform user, mirror private metadata, open `/platform` | Missing/expired/revoked/mismatched ticket stays in platform-specific error UI |
| Delayed/replayed webhook | Valid signed user event, duplicate or out of order | Same provisioning/sync service converges once | Invalid signature is 400; processing failure is 5xx for retry |
| Clerk user updated/deleted | Existing local identity | Sync profile only; deletion marks inactive | Metadata changes never alter realm, role, or status |
| Platform user enters tenant auth/setup | Active platform DB identity without org | Redirect to `/platform` | Unprovisioned personal session continues to `/workspace/setup` |

</frozen-after-approval>

## Code Map

- `apps/api/ringiq_api/models/identity.py` and Alembic migration -- invitation/receipt persistence and constraints.
- `apps/api/ringiq_api/services/clerk_directory.py` -- Clerk invitation, user lookup, and metadata operations.
- `apps/api/ringiq_api/routes/platform.py` plus new webhook route -- management, completion, and signed event interfaces.
- `apps/web/components/auth/*` and platform routes -- ticket acceptance, destination resolution, and user management UI.
- `scripts/bootstrap_platform_user.py` -- first-admin invitation plus direct-ID recovery.

## Tasks & Acceptance

**Execution:**
- [x] Add identity models, migration, config, `standardwebhooks`, schemas, and migration/model tests.
- [x] Implement a shared idempotent invitation/provisioning service and injectable Clerk directory operations.
- [x] Add platform user/invitation CRUD reads, create/revoke, onboarding completion, and signature-verified Clerk webhook routes with focused API tests.
- [x] Add `/platform/users`, ticket acceptance, API client types, shared post-auth destination resolution, and frontend/unit/E2E coverage.
- [x] Extend the bootstrap CLI, environment documentation, and one-time private-metadata reconciliation behavior.

**Acceptance Criteria:**
- Given a valid invited user, when the invitation is accepted while Clerk webhooks are delayed, then synchronous completion grants the assigned database role and navigation reaches `/platform` without `/workspace/setup`.
- Given any later webhook replay or metadata edit, when authorization runs, then the database role/status remains the sole authority and duplicate mutations do not occur.
- Given an ordinary tenant signup, when verification completes, then organization setup behavior remains unchanged.
- Given an existing platform account, when it visits tenant auth or setup routes, then it is redirected to `/platform`.

## Spec Change Log

## Design Notes

Application invitations carry only `ringiq_platform_invitation_id`; the pending database row owns email and role. Both the webhook and synchronous completion call one transaction-safe provisioning service. The accepted user receives a private metadata mirror under `ringiq`, but inbound metadata is never promoted into authorization state.

## Verification

**Commands:**
- `uv run pytest tests/api` -- backend, migration, invitation, webhook, and compatibility tests pass.
- `npm test --workspace apps/web`, `npm run web:typecheck`, and `npm run web:lint` -- frontend tests, types, and lint pass.
- `npm run web:build` -- Next.js routes build successfully.

## Suggested Review Order

**Identity authority and provisioning**

- Shared transaction boundary owns invitation validation, role assignment, and idempotency.
  [`platform_identity.py:193`](../../apps/api/ringiq_api/services/platform_identity.py#L193)

- Invitation creation persists backend-owned intent before Clerk receives the opaque correlation ID.
  [`platform_identity.py:83`](../../apps/api/ringiq_api/services/platform_identity.py#L83)

- Clerk integration isolates invitations, current-user reads, and private-metadata mirroring.
  [`clerk_directory.py:100`](../../apps/api/ringiq_api/services/clerk_directory.py#L100)

**Webhook consistency and authorization**

- Raw-body verification, receipt leasing, current-state fetches, and mirror guards converge safely.
  [`webhooks.py:104`](../../apps/api/ringiq_api/routes/webhooks.py#L104)

- Database realm, role, and active status remain the sole runtime authority.
  [`context.py:100`](../../apps/api/ringiq_api/auth/context.py#L100)

- Super-admin management, locked revocation, and synchronous completion expose the backend workflow.
  [`platform.py:286`](../../apps/api/ringiq_api/routes/platform.py#L286)

**Invitation UX and routing**

- Ticket signup verifies email, supports provisioning retry, and never requests a verification code.
  [`platform-invitation-form.tsx:46`](../../apps/web/components/auth/platform-invitation-form.tsx#L46)

- Shared post-auth resolution separates platform, tenant, inactive, and unprovisioned destinations.
  [`post-auth-destination.ts:13`](../../apps/web/lib/post-auth-destination.ts#L13)

- Super admins manage platform users and invitation lifecycle from one directory page.
  [`platform-users.tsx:45`](../../apps/web/components/platform/platform-users.tsx#L45)

**Persistence and operations**

- Migration enforces normalized open invitations and idempotent provider delivery receipts.
  [`20260721_0011_platform_user_invitations.py:19`](../../migrations/versions/20260721_0011_platform_user_invitations.py#L19)

- Bootstrap serializes first-admin invites, validates recovery identities, and reconciles metadata.
  [`bootstrap_platform_user.py:131`](../../scripts/bootstrap_platform_user.py#L131)

**Verification**

- API coverage exercises synchronous completion, webhook replay, tampering, leases, and failures.
  [`test_platform_user_routes.py:251`](../../tests/api/test_platform_user_routes.py#L251)

- Inactive platform identities are explicitly kept out of tenant onboarding.
  [`test_platform_context.py:74`](../../tests/api/test_platform_context.py#L74)
