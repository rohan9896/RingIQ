---
title: 'Post-Call Qualification Outcome'
type: 'feature'
created: '2026-07-20'
status: 'done'
review_loop_iteration: 0
baseline_commit: '146eee6743c21508a00e99ec4509103d5c3cf38d'
context:
  - '{project-root}/_bmad-output/planning-artifacts/ringiq-product-feature-tracker.md'
  - '{project-root}/_bmad-output/planning-artifacts/prds/prd-RingIQ-2026-07-16/prd.md'
  - '{project-root}/_bmad-output/planning-artifacts/architecture/architecture-RingIQ-2026-07-17/ringiq-low-level-design-and-erd.md'
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** RingIQ persists call attempts, transcripts, and recordings, but tenants cannot see what a completed call learned or why a lead received a particular outcome. This blocks the product's core sales-qualification promise and every downstream follow-up view.

**Approach:** Add an asynchronous, tenant-scoped post-call processor that converts terminal call evidence into one persisted outcome containing classification, rationale, confidence, summary, real-estate facts, callback intent, cited evidence, and terminal reason. Expose the outcome in the existing Calls and Lead Detail experiences.

## Boundaries & Constraints

**Always:** Use only the stored transcript and operational call state as evidence; preserve exact transcript turn references; make scheduling and processing idempotent across duplicate/out-of-order callbacks; assign `unanswered` and `invalid_number` deterministically without an LLM; use `needs_review` for ambiguous, unsupported, or low-confidence connected outcomes; preserve the callback's original phrase and tenant IANA timezone; normalize `callback_at` to UTC only when the time is unambiguous; keep all reads tenant-scoped; retain transcript and recording access when outcome processing fails.

**Ask First:** Changing the eight-label V1 taxonomy; adding a new runtime service; changing the LLM provider; destructive backfills; adding an editable human-override workflow or callback scheduling.

**Never:** Invent facts, evidence quotes, callback times, or summaries unsupported by the transcript; let the LLM override deterministic operational outcomes; trust a client-supplied tenant ID; put model calls in the realtime media path; build the follow-up queue, knowledge-gap workflow, scheduling, or human review in this slice.

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected Output / Behavior | Error Handling |
|----------|--------------|---------------------------|----------------|
| Connected call | Terminal `completed` attempt plus finalized transcript | One outcome with validated V1 label, grounded summary/rationale/evidence, facts, and callback data | Invalid or unsupported output retries, then remains inspectably failed without hiding artifacts |
| Callback order | Result and artifact callbacks arrive in either order or repeat | Exactly one job and one outcome; connected extraction begins only after both prerequisites exist | Duplicate delivery is a no-op; incomplete evidence remains pending |
| Operational outcome | Final `unanswered` or `invalid_number` attempt | Matching deterministic label without invoking the extractor | Busy/final failure/cancellation becomes evidence-backed `needs_review` |
| Ambiguous callback | Transcript requests a callback but gives no safe time | `callback_requested`, original phrase and timezone retained, `callback_at = null` | Never infer a default date or time |
| Extraction unavailable | Missing configuration, timeout, malformed JSON, or exhausted retries | Transcript/recording remain available and outcome shows failed processing | Store safe failure detail; no tenant-private prompt data in logs |

</frozen-after-approval>

## Code Map

- `migrations/versions/20260720_0010_post_call_outcomes.py` -- outcome persistence, terminal reason, and artifact-finalization schema.
- `apps/api/ringiq_api/models/campaigns.py` -- `CallOutcome` model and constrained V1 enums.
- `apps/api/ringiq_api/services/post_call_outcomes.py` -- structured extraction, deterministic mapping, evidence validation, callback normalization, and persistence.
- `apps/api/ringiq_api/services/campaign_operations.py` -- idempotent outcome-job enqueue/claim and terminal transition integration.
- `apps/worker/main.py` -- dispatch outbound-call versus post-call jobs and apply retry/dead-letter behavior.
- `apps/api/ringiq_api/routes/campaigns.py` -- order-safe artifact/result triggers and tenant-scoped outcome responses.
- `apps/api/ringiq_api/schemas/campaigns.py` -- shared outcome, facts, callback, and evidence response contracts.
- `apps/voice_worker/agent.py` -- submit bounded terminal reasons with final call results.
- `apps/web/components/post-call-outcome.tsx` -- shared read-only outcome presentation.
- `apps/web/components/calls-workspace.tsx` and `apps/web/components/lead-detail-workspace.tsx` -- embed the shared outcome surface.

## Tasks & Acceptance

**Execution:**
- [x] `migrations/versions/20260720_0010_post_call_outcomes.py`, `models/campaigns.py`, `models/__init__.py` -- add one outcome per attempt plus processing state, artifact-finalization time, and terminal reason.
- [x] `config.py`, `.env.example`, `pyproject.toml`, `services/post_call_outcomes.py` -- add an injectable Groq-compatible structured extractor with strict schema/evidence validation and deterministic operational mappings.
- [x] `campaign_operations.py`, `routes/campaigns.py`, `apps/worker/main.py`, `apps/voice_worker/agent.py` -- schedule and process outcomes safely across callback order, retries, and duplicate delivery.
- [x] `schemas/campaigns.py`, `routes/campaigns.py`, `apps/web/lib/api-client.ts` -- return the same nullable outcome contract from Calls and lead campaign history.
- [x] `post-call-outcome.tsx`, `calls-workspace.tsx`, `lead-detail-workspace.tsx` -- show processing, failure, needs-review, classification, summary, facts, callback, evidence, and transcript states without editable controls.
- [x] `tests/api/test_post_call_outcomes.py`, `tests/api/test_campaign_routes.py`, `tests/api/test_voice_agent_prompt.py`, `tests/api/test_migrations.py`, `apps/web/lib/post-call-outcome.test.ts` -- cover the matrix, tenant isolation, and display-state helpers.

**Acceptance Criteria:**
- Given a completed connected call with a finalized transcript, when the post-call job succeeds, then Calls and Lead Detail show the same grounded outcome and evidence.
- Given terminal and artifact callbacks in either order or repeated, when processing runs, then one outcome is produced and no duplicate model work or state regression occurs.
- Given an unanswered or invalid-number terminal attempt, when processing runs, then the matching outcome is stored without calling the LLM.
- Given a callback request without an unambiguous time, when extraction completes, then the original phrase and timezone are shown and no callback timestamp is invented.
- Given extractor failure or low-confidence/unsupported evidence, when retries finish, then artifacts remain accessible and the UI shows failed processing or `needs_review` rather than a fabricated result.

## Design Notes

Use the existing durable `jobs` table with a distinct post-call job type and attempt-ID idempotency key. The internal result and artifact routes may both request scheduling; uniqueness makes this safe. Connected calls require terminal state plus an explicit `artifacts_finalized_at`, including when the final transcript is empty. Operational outcomes can process immediately.

Keep the model provider behind an injectable adapter. Request JSON output, validate it with Pydantic, bound text/list sizes, and accept evidence only when the cited turn index, speaker, and exact quote match the stored transcript. Completed outcomes are immutable unless a future extractor-version migration is explicitly approved.

## Verification

**Commands:**
- `.venv/bin/pytest -q` -- expected: all API, worker, voice, model, and migration tests pass against PostgreSQL.
- `npm run typecheck --workspace apps/web` -- expected: no TypeScript errors.
- `npm run lint --workspace apps/web` -- expected: no lint errors.
- `npm run test --workspace apps/web` -- expected: all web helper tests pass.
- `npm run build --workspace apps/web` -- expected: production build succeeds.
- `git diff --check` -- expected: no whitespace errors.

## Suggested Review Order

**Outcome policy and grounding**

- Start with the processing decision tree, deterministic labels, and conservative review fallback.
  [`post_call_outcomes.py:375`](../../apps/api/ringiq_api/services/post_call_outcomes.py#L375)

- Validate callback instants against the spoken phrase, call date, and tenant timezone.
  [`post_call_outcomes.py:265`](../../apps/api/ringiq_api/services/post_call_outcomes.py#L265)

- Reject unsupported structured facts before they reach tenant-facing views.
  [`post_call_outcomes.py:321`](../../apps/api/ringiq_api/services/post_call_outcomes.py#L321)

**Lifecycle, concurrency, and failure handling**

- Converge terminal and artifact callbacks on one idempotent post-call job.
  [`campaign_operations.py:127`](../../apps/api/ringiq_api/services/campaign_operations.py#L127)

- Recover expired leases and make exhausted post-call processing inspectably failed.
  [`campaign_operations.py:355`](../../apps/api/ringiq_api/services/campaign_operations.py#L355)

- Serialize callback mutations and keep finalized transcripts immutable.
  [`campaigns.py:106`](../../apps/api/ringiq_api/routes/campaigns.py#L106)

- Dispatch extraction outside the realtime path with bounded leases and retries.
  [`main.py:49`](../../apps/worker/main.py#L49)

- Preserve precise terminal causes without duplicate finalization races.
  [`agent.py:1149`](../../apps/voice_worker/agent.py#L1149)

**Persistence and tenant boundaries**

- Review the one-to-one outcome model and composite tenant-attempt constraint.
  [`campaigns.py:230`](../../apps/api/ringiq_api/models/campaigns.py#L230)

- Apply outcome storage, terminal metadata, indexes, and downgrade symmetry.
  [`20260720_0010_post_call_outcomes.py:19`](../../migrations/versions/20260720_0010_post_call_outcomes.py#L19)

**Tenant-facing presentation**

- Reuse one read-only outcome surface for state, facts, callbacks, and evidence.
  [`post-call-outcome.tsx:11`](../../apps/web/components/post-call-outcome.tsx#L11)

- Render normalized callback time in the stored tenant timezone.
  [`post-call-outcome.ts:46`](../../apps/web/lib/post-call-outcome.ts#L46)

- Embed identical outcome behavior in Calls and Lead Detail.
  [`calls-workspace.tsx:80`](../../apps/web/components/calls-workspace.tsx#L80)

**Verification and project status**

- Exercise the real concurrent callback race with two database transactions.
  [`test_post_call_outcomes.py:387`](../../tests/api/test_post_call_outcomes.py#L387)

- Verify exhausted leases transition outcomes from analyzing to failed.
  [`test_post_call_outcomes.py:464`](../../tests/api/test_post_call_outcomes.py#L464)

- Confirm API parity, idempotency, artifact immutability, and tenant isolation.
  [`test_campaign_routes.py:286`](../../tests/api/test_campaign_routes.py#L286)

- Review the canonical tracker reconciliation and next recommended feature.
  [`ringiq-product-feature-tracker.md:27`](../planning-artifacts/ringiq-product-feature-tracker.md#L27)

- Keep the pre-existing artifact-upload retry weakness visible for later work.
  [`deferred-work.md:1`](deferred-work.md#L1)
