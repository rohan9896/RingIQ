# Data Integrity And Tenant Security Review

Verdict: Pass after security-boundary fixes.

## Findings

1. Critical: Resolving a tenant from Clerk organization ID before setting RLS context needs a narrowly scoped security-definer function or equivalent control-plane mapping. A general `BYPASSRLS` application role is unacceptable.
2. High: `jobs` and `outbox_events` require cross-tenant operational access. Restrict that access to dedicated queue roles/functions and keep user/API roles unable to query them.
3. High: Pin `knowledge_base_version_id` in the same transaction that creates `call_attempts`; do not resolve it after telephony connects.
4. Medium: Composite tenant foreign keys and a non-owner runtime role correctly prevent most cross-tenant association errors.

