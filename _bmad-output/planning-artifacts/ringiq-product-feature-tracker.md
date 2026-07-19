# RingIQ Product Feature Tracker

**Last updated:** 2026-07-19  
**Product scope:** Real-estate-first Voice AI lead qualification SaaS  
**Delivery state:** Local implementation and verification; not a deployment checklist

## How To Use This Tracker

- `[x]` **Done**: implemented as a usable product/API capability and locally verified.
- `[-]` **In progress**: a meaningful slice exists, but the complete product capability is not ready.
- `[ ]` **Planned**: required or intended, with no meaningful implementation yet.
- `Deferred`: intentionally outside the current MVP.

This is the canonical implementation tracker. The PRD remains the source of truth for product requirements; this document records the actual delivery state.

## Current Delivery Snapshot

| Area | Status | What exists now | What completes the area |
|---|---|---|---|
| Platform foundation | `[-]` | Monorepo, FastAPI backend, Next.js web app, PostgreSQL migrations, and Postgres-backed API tests | Deployment, monitoring, production operations |
| Identity and access | `[-]` | Clerk custom sign-in/sign-up UI, tenant and platform identity realms, role-aware backend contexts | Tenant user and organization lifecycle administration |
| Category templates | `[x]` | Platform category and starter KB template CRUD, questions, draft editing, publication, and real-estate draft seed action | Seeded initial templates for production deployment |
| Tenant knowledge base | `[x]` | Tenant can select a published starter template, create a draft, answer/edit questions, and publish it | Retrieval indexing and use during production calls |
| Lead imports | `[x]` | Tenant CSV import, validation, lead management, campaign selection, and lead campaign/call history | AI qualification outcomes |
| Voice AI demo | `[x]` | Outbound SIP demo call with LiveKit, Deepgram, Groq, Sarvam, and pipeline/latency logs | Tenant-grounded production calling workflow |
| Campaigns and call operations | `[x]` | Campaign lifecycle, readiness, durable jobs, outbound call initiation, retries, controls, and monitoring | Tenant-grounded AI conversation behavior is tracked separately |
| Qualification outcomes | `[ ]` | Designed in PRD/LLD | Classification, callback capture, follow-up queue |
| Conversation audit | `[ ]` | Designed in PRD/LLD | Persisted call attempts, recordings, transcripts, summaries |
| Tenant dashboard | `[-]` | Live readiness, lead/call metrics, and recent operational call activity | Qualification metrics, filters, and richer call detail views |
| Knowledge improvement loop | `[ ]` | Designed in PRD/LLD | Gap detection, review, and improvement workflow |

## 1. Product Foundation And Access

- [x] Monorepo structure for web app, core API, voice worker, and future background worker.
- [x] FastAPI core backend bootstrap with health endpoint, configuration, logging, and CORS support.
- [x] Next.js TypeScript web app bootstrap with the established RingIQ visual theme.
- [x] PostgreSQL as the only application and test database; Alembic migrations and PostgreSQL test coverage are in place.
- [x] Clerk custom authentication UI for sign-in and sign-up.
- [x] Platform sign-in flow gates organizationless RingIQ users into the platform console.
- [x] Tenant workspace gating: authenticated users must have an organization before entering the tenant workspace.
- [x] Separate tenant and RingIQ platform identity realms.
- [x] Platform roles: super admin, operations, and template manager.
- [x] Backend tenant-scoping for implemented tenant knowledge-base and lead endpoints.
- [x] Backend platform role checks for category and template administration.
- [ ] Tenant user invitation and removal management.
- [ ] Tenant organization creation, editing, suspension, and lifecycle management from the platform console.
- [ ] Platform-user lifecycle management.
- [ ] Production-ready authorization audit trail.

## 2. Category And Starter Knowledge-Base Templates

- [x] Platform users can create, list, view, and update categories.
- [x] Platform template managers can create versioned starter KB templates for a category.
- [x] Templates support configurable lead fields and structured Q&A questions.
- [x] Template questions support required/optional flags, ordering, help text, answer types, validation metadata, and options.
- [x] Draft templates can be edited and published.
- [x] Published templates are protected from edits.
- [x] Platform template console UI is available.
- [x] Platform dashboard shows live aggregate organization, user, category, and template counts.
- [x] Platform users can seed the first real-estate category and starter KB draft from the dashboard.
- [ ] Seed the first production real-estate category and starter template as part of deployment.
- [ ] Archive/deactivate workflow for categories and template versions, including tenant-facing behavior.

## 3. Tenant Knowledge-Base Setup

- [x] Tenant users can browse published starter templates.
- [x] Tenant users can create a KB draft from a starter template.
- [x] Tenant users can edit the KB title, business profile, additional notes, and structured answers.
- [x] Tenant users can publish a KB version.
- [x] Required KB questions block publication until answered.
- [x] A published KB becomes the tenant's active version for later calls.
- [x] Tenant knowledge-base UI is available.
- [ ] Call-readiness rules that combine business-profile and active-KB requirements.
- [ ] Compile published KB content into tenant-scoped retrieval chunks and embeddings.
- [ ] Retrieve relevant active-KB knowledge during production calls.
- [ ] Knowledge-base history, archival, and rollback UX.

## 4. Lead Import And Lead Workspace

- [x] Tenant users can submit lead CSV content for import.
- [x] Mandatory lead fields are name, email, and phone number.
- [x] Optional category-specific columns are preserved as lead attributes.
- [x] Import validates required fields, email format, and Indian/E.164 phone numbers.
- [x] Imports detect duplicate phone numbers within the tenant.
- [x] Import results preserve imported, invalid, and duplicate row outcomes with reasons.
- [x] Tenant users can list and search their leads.
- [x] Leads workspace UI is available.
- [x] Browser file upload, column-mapping review, and downloadable error report.
- [x] Lead edit, archive/restore, and manual sales-work status management.
- [x] Lead enrollment selection for campaigns.
- [x] Lead detail page with contact details, optional attributes, archive state, and manual follow-up status.
- [x] Manual single-lead creation without requiring CSV import.
- [x] Add campaign enrollment and call-attempt history to lead detail.
- [ ] Add AI outcome context to lead detail when classification is implemented.

## 5. Campaign Creation And Call Operations

- [x] Create a campaign from selected imported leads.
- [x] Show campaign readiness based on active KB and required business profile data.
- [x] Configure the V1 unanswered-call rule: one initial attempt plus up to three retries.
- [x] Persist campaign, enrollment, and attempt states.
- [x] Use PostgreSQL-backed jobs/outbox to schedule and safely claim outbound call work.
- [x] Start a production call through the voice worker for one eligible lead at a time.
- [x] Stop retries after a connected call or terminal outcome.
- [x] Campaign launch, pause, resume, cancellation, and automatic completion controls.
- [x] Campaign progress and operational-error visibility.
- [x] Immediate single-lead **Call now** path with retries disabled.

## 6. Voice AI Qualification

- [x] Demo endpoint can initiate an outbound call to an entered phone number.
- [x] LiveKit SIP connects RingIQ to Vobiz for the demo outbound call.
- [x] Demo voice worker uses Deepgram Flux for speech-to-text, Groq for LLM orchestration, and Sarvam for text-to-speech.
- [x] Demo agent supports English, Hindi, and mixed Hindi-English conversation behavior.
- [x] Demo agent uses short lead-qualification conversation rules and safe-answer constraints.
- [x] Pipeline stage and turn-latency logs are emitted to the FastAPI service.
- [x] Generate tenant-specific voice instructions from the published business profile and active KB.
- [x] Load the pinned tenant-scoped KB context for each production call.
- [x] Pass lead name and optional lead attributes into the call context.
- [ ] Capture structured qualification facts: area, budget, property type, intent, and timeline.
- [ ] Capture a requested callback date/time.
- [ ] Enforce a production call-end policy and terminal outcomes.
- [x] Preserve tenant, campaign, lead, and call-attempt identifiers through LiveKit dispatch and result callbacks.

## 7. Lead Classification And Sales Follow-Up

- [ ] Derive and store one V1 outcome: hot, warm, cold, callback requested, not interested, unanswered, invalid number, or needs review.
- [ ] Store a human-readable reason and structured evidence for the outcome.
- [ ] Create the tenant follow-up queue for hot, warm, and callback-requested leads.
- [ ] Filter and sort the queue by campaign, batch, call status, outcome, and callback time.
- [ ] Show lead and call evidence before a sales user follows up.
- [ ] No automated live transfer in V1.

## 8. Conversation Records And Audit Trail

- [ ] Create a persisted record for every call attempt, including unanswered and provider failures.
- [ ] Store provider call identifiers, timestamps, duration, and terminal reason.
- [ ] Store recordings for connected calls in tenant-isolated object storage.
- [ ] Store transcripts and conversation summaries where available.
- [ ] Restrict lead data, recordings, transcripts, and private KB content to the owning tenant.
- [ ] Expose tenant call history and call-detail views.
- [ ] Retain call artifacts indefinitely until a later retention policy is adopted.

## 9. Tenant Dashboard And Knowledge Improvement

- [-] Dashboard metrics: lead, campaign, attempted, connected, completed, and failed totals are live; qualification metrics remain planned.
- [x] Organization first-call readiness with guided category, KB, and lead actions.
- [x] Recent operational call activity with lead, status, time, duration, and failure context.
- [ ] Tenant filters for campaigns, lead imports, outcomes, and date ranges.
- [ ] Lead detail view with qualification data, follow-up status, and call history.
- [ ] Identify unanswered or insufficiently-grounded questions as tenant-scoped knowledge gaps.
- [ ] Knowledge-gap list links to the related lead, campaign, call, and KB topic.
- [ ] Let a tenant improve its KB from the gap context; the next call after publication uses the updated KB.

## 10. Platform Administration

- [x] Platform console and platform sign-in route are available.
- [x] Platform overview dashboard is backed by aggregate metadata and keeps tenant-private content outside the console.
- [x] Platform template management is available, without access to tenant private KB, leads, recordings, or transcripts.
- [ ] Platform organization list and organization status management.
- [ ] Platform organization-user list and support metadata.
- [ ] Platform-user administration for the three platform roles.
- [ ] Platform audit trail for administrative actions.
- [ ] Operational reporting that exposes only safe aggregate tenant metadata, never private tenant content.

## Deferred From MVP

- `Deferred` Pricing, subscription billing, and usage metering.
- `Deferred` DND, consent capture, formal regulatory workflows, and retention/deletion controls.
- `Deferred` CRM integrations.
- `Deferred` Automated live transfer to a sales representative.
- `Deferred` Scheduled calling windows and advanced calling policies.
- `Deferred` Vertical-specific product experiences beyond the real-estate-first launch.

## Recommended Next Build Sequence

1. Campaign creation, readiness checks, and PostgreSQL-backed campaign/enrollment/attempt records.
2. Background job processing for the initial call and three unanswered retries.
3. Tenant-grounded production voice calls that consume persisted campaign, lead, and active-KB data.
4. Persist call outcomes, recordings, transcripts, summaries, and structured qualification facts.
5. Classification and follow-up queue.
6. Campaign dashboard and lead detail views.
7. Knowledge-gap improvement loop and the remaining platform administration capabilities.

## Verification Standard For Future Checks

Before changing a planned item to `[x]`, confirm all of the following:

- The user-visible capability works for its intended role.
- Tenant isolation and authorization behavior are covered when the feature handles tenant data.
- Relevant API, database, and UI behavior has automated coverage appropriate to the change.
- The item is linked to the next dependent capability in this tracker.
