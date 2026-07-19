# Organization Activation And First Call TODO

**Created:** 2026-07-18  
**Objective:** Let a new organization select a category, publish its private knowledge base, add a lead, place one tenant-grounded call, and monitor the result from a useful dashboard.

## Completion Definition

This milestone is complete when a tenant user can follow this path without using campaign scheduling:

1. Create or enter a Clerk organization workspace.
2. Select the organization's primary category.
3. Create, customize, and publish a private knowledge base from that category's starter template.
4. Add one lead manually or use an imported lead.
5. Click **Call now**.
6. The voice worker calls the lead using that lead's details and the organization's published knowledge base.
7. The dashboard shows readiness, lead and call totals, recent calls, and operational failures.

## Implementation Checklist

### A. Organization Activation

- [x] Persist a primary category for each tenant organization.
- [x] Provide tenant-scoped organization profile and category-selection APIs.
- [x] Show organization readiness and guide the user to the next incomplete step.
- [x] Filter the starter knowledge-base experience to the selected category.

### B. Knowledge-Base Readiness

- [x] Create a private draft from a published category starter template.
- [x] Edit business profile, questions, and additional notes.
- [x] Validate required answers and publish an active KB version.
- [x] Surface active-KB readiness on the dashboard and before calling.

### C. Lead And Click-To-Call

- [x] Add a lead manually with name, email, phone number, and optional attributes.
- [x] Add **Call now** to the lead workspace and lead detail.
- [x] Create an immediate, single-lead call operation with no scheduled retries.
- [x] Reuse campaign, enrollment, attempt, and PostgreSQL job records internally.
- [x] Prevent calling when the organization has no category or active published KB.

### D. Tenant-Grounded Voice Conversation

- [x] Load the pinned KB version, structured answers, business profile, and notes for the call.
- [x] Pass lead name and optional attributes into the voice-agent context.
- [x] Generate production voice-agent instructions from tenant context instead of the demo prompt.
- [x] Preserve tenant and call-attempt identifiers through LiveKit metadata and callbacks.

### E. Dashboard

- [x] Replace placeholder metrics with tenant-scoped database metrics.
- [x] Show organization activation readiness and direct next actions.
- [x] Show lead, campaign, call-attempt, connected, completed, and failed totals.
- [x] Show recent call activity with lead, status, timestamp, duration, and error context.
- [x] Refresh operational data without requiring a page reload.

### F. Verification

- [x] Add migration and model coverage for tenant category assignment.
- [x] Add API coverage for organization readiness, manual leads, click-to-call, and dashboard metrics.
- [x] Add worker coverage proving tenant KB and lead context reach LiveKit dispatch.
- [x] Pass the PostgreSQL API test suite.
- [x] Pass frontend typecheck, lint, and production build.

## Explicitly Deferred

- Scheduled calling windows and campaign schedules.
- Automatic retry configuration and retry-management UX for click-to-call.
- AI lead classification and follow-up queues.
- Callback scheduling.
- Transcript, recording, and summary persistence.
- Knowledge-gap detection.
- Advanced dashboard date filters and reporting exports.
- Organization user administration and platform organization lifecycle controls.
