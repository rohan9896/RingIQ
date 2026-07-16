# RingIQ Product Feature Stories

## Purpose

This document breaks the RingIQ Version 1 PRD into high-level product feature stories. It is intentionally not a technical implementation plan. It does not prescribe tools, frameworks, database schema design, provider choices, API shapes, or internal architecture.

The stories describe what the product must enable for tenants, leads, and tenant sales teams. Technical architecture and implementation design should come after this feature story map.

## Product North Star

RingIQ Version 1 helps real estate businesses automatically perform first-touch lead qualification through an AI voice agent, then surfaces hot, warm, and callback-requested leads for manual sales follow-up.

## Feature Story Map

### Epic 1: Tenant Accounts And Organization Separation

**Product goal:** Each business should have its own RingIQ workspace where its users, leads, knowledge, campaigns, recordings, transcripts, and dashboards are separated from every other business.

**Feature stories:**

- As a business, I can have my own RingIQ tenant workspace so that my lead and call data is not mixed with another business.
- As a tenant user, I can sign in and access only my tenant's workspace so that my team sees the right leads, campaigns, and call records.
- As a tenant user, I can invite or use other tenant users within the same workspace so that the business team can collaborate during pilots.
- As RingIQ, the product can maintain strict tenant separation across leads, knowledge base content, call records, recordings, transcripts, summaries, and dashboards.

**Product acceptance:**

- Tenant users can only see their own tenant's data.
- Tenant users cannot access another tenant's leads, knowledge base, recordings, transcripts, or dashboards.
- Version 1 supports a simple tenant-user access model where all tenant users can access tenant call artifacts.

### Epic 2: Tenant Business Profile Setup

**Product goal:** A tenant can describe its business clearly enough for the AI voice agent to represent it accurately during calls.

**Feature stories:**

- As a tenant admin, I can enter my business name, category, served locations, language preference, contact instructions, and business description so that the AI can introduce the business correctly.
- As a real estate tenant, I can enter project/property names, property locations, property types, budget ranges, availability or possession status, and site-visit process so that the AI has approved business context.
- As a tenant admin, I can define key value propositions and follow-up instructions so that the AI knows what to emphasize and how to route interested leads.
- As a tenant admin, I can define disallowed claims or topics so that the AI avoids saying things the business has not approved.

**Product acceptance:**

- A tenant can complete a minimum viable business profile before running a campaign.
- The AI call flow uses tenant business profile information.
- Missing business profile information blocks campaign readiness when it is required for safe calling.

### Epic 3: Category-Specific Knowledge Base Q&A

**Product goal:** A tenant can provide approved answers through a structured Q&A form instead of needing to prepare a technical knowledge base format.

**Feature stories:**

- As a tenant admin, I can complete a real-estate-specific Knowledge Base Q&A Form so that RingIQ knows what the AI is allowed to say.
- As a tenant admin, I can answer questions about business/project overview, areas served, property types, budget ranges, availability, site visits, pricing disclaimers, common objections, escalation instructions, and disallowed claims.
- As a tenant admin, I can see which Q&A fields are required before a campaign can start so that I know what is blocking readiness.
- As a tenant admin, I can add optional supporting knowledge beyond required Q&A fields so that the AI has richer context.
- As RingIQ, the product can treat unanswered optional Q&A fields as unknown information so that the AI does not invent facts.

**Product acceptance:**

- Version 1 provides a real-estate-specific Q&A intake path.
- Required Q&A fields must be completed before campaign launch.
- Optional additional knowledge can supplement but not replace the Q&A form.
- Missing or insufficient knowledge can become a knowledge gap after calls.

### Epic 4: Lead Upload And Validation

**Product goal:** A tenant can upload real estate leads quickly without needing a complex data model.

**Feature stories:**

- As a tenant admin, I can upload a CSV of leads so that RingIQ can prepare them for calling.
- As a tenant admin, I can provide mandatory lead fields: name, email, and phone number.
- As a tenant admin, I can optionally include real estate qualification fields such as area of interest, budget range, property type, buying/renting intent, and preferred timeline.
- As a tenant admin, I can see which lead rows were imported and which were rejected so that I can fix bad data.
- As RingIQ, the product can allow missing optional real estate qualification fields because the AI can collect them during the call.

**Product acceptance:**

- Valid lead rows are imported into the tenant workspace.
- Invalid rows are rejected or flagged with clear reasons.
- Optional real estate qualification fields do not block upload.

### Epic 5: Campaign Creation And Call Readiness

**Product goal:** A tenant can turn an uploaded lead batch into a ready-to-run AI calling campaign.

**Feature stories:**

- As a tenant admin, I can create a campaign from uploaded leads so that RingIQ knows which leads to call.
- As a tenant admin, I can see whether the tenant business profile and required Q&A fields are complete before launching a campaign.
- As a tenant admin, I can use a default retry setting of 3 retries after the initial unanswered call so that unanswered leads are attempted again.
- As RingIQ, the product can prevent campaign launch when required tenant knowledge is incomplete.
- As RingIQ, the product can keep campaign setup focused on first-touch qualification, not billing, CRM setup, or scheduled calling windows.

**Product acceptance:**

- A campaign can be created from valid uploaded leads.
- Campaign launch requires required business profile and Q&A readiness.
- Unanswered calls can be retried according to the Version 1 retry rule.
- Connected leads receive only one introductory connected call in Version 1.

### Epic 6: Voice AI Qualification Pipeline

**Product goal:** RingIQ can place introductory AI voice calls that qualify leads in Hindi, English, or mixed Hindi-English.

**Feature stories:**

- As a lead, I can receive a clear introductory call from the AI on behalf of the real estate business.
- As a lead, I can speak naturally in Hindi, English, or a mix of both.
- As a lead, I can ask basic property or business questions and receive answers based only on approved tenant knowledge.
- As a lead, I can share missing qualification details such as area, budget, property type, intent, and timeline during the call.
- As a lead, I can ask for a later callback and provide a date or time.
- As RingIQ, the product can avoid unsupported claims when knowledge is missing.
- As RingIQ, the product can classify the call outcome after or during the conversation.

**Product acceptance:**

- AI calls can conduct first-touch qualification conversations.
- The AI uses tenant-approved business profile and Q&A knowledge.
- The AI captures callback requests where provided.
- The AI does not invent real estate availability, pricing, legal status, possession timelines, discounts, or guarantees.

### Epic 7: Lead Classification And Follow-Up Queue

**Product goal:** Tenant sales teams can quickly identify which leads deserve manual follow-up.

**Feature stories:**

- As a sales manager, I can see leads classified as hot, warm, cold, callback requested, not interested, unanswered, invalid number, or needs review.
- As a sales manager, I can focus on hot, warm, and callback-requested leads so that my team spends time on promising opportunities.
- As a sales representative, I can open a qualified lead and see the reason the lead was surfaced.
- As a sales representative, I can see callback date/time when the lead requested later follow-up.
- As RingIQ, the product can classify unanswered and invalid-number outcomes even when no conversation happened.

**Product acceptance:**

- Hot, warm, and callback-requested leads appear in a follow-up queue.
- Each surfaced lead has enough call evidence for a tenant user to understand why it was surfaced.
- Needs-review outcomes are available for ambiguous conversations.

### Epic 8: Conversation Audit Trail

**Product goal:** Every attempted or completed call should leave a clear record for trust, review, and improvement.

**Feature stories:**

- As a tenant user, I can see call attempts for each lead so that I know what happened.
- As a tenant user, I can access recordings for connected calls so that I can audit the actual conversation.
- As a tenant user, I can read transcripts where available so that I can review call content without always listening.
- As a tenant user, I can read a conversation summary so that I can quickly understand the call.
- As RingIQ, the product can preserve call status, classification, callback request, and failure reason where available.

**Product acceptance:**

- Every call attempt creates a call record.
- Connected calls include recording, transcript where available, and summary where available.
- Tenant users can access their tenant's call artifacts.
- Call artifacts are retained indefinitely until a future retention policy is defined.

### Epic 9: Tenant Dashboard And Campaign Monitoring

**Product goal:** Tenants can monitor campaign progress and lead outcomes without managing spreadsheets manually.

**Feature stories:**

- As a tenant admin, I can see campaign progress so that I know how many leads were uploaded, called, connected, unanswered, failed, or invalid.
- As a sales manager, I can filter leads by campaign, upload batch, call status, interest classification, and call date.
- As a sales manager, I can open a lead detail view so that I can inspect call history and follow-up information.
- As a tenant user, I can see dashboard metrics for hot leads, warm leads, callback requests, unanswered calls, and knowledge gaps.

**Product acceptance:**

- Tenant users can track campaign progress.
- Tenant users can filter and inspect lead outcomes.
- The dashboard does not expose data from other tenants.

### Epic 10: Knowledge Gap Improvement Loop

**Product goal:** Tenants can improve future AI calls by reviewing what the AI could not answer.

**Feature stories:**

- As a tenant admin, I can see questions or moments where the AI lacked enough approved knowledge.
- As a tenant admin, I can connect a knowledge gap back to the related lead, campaign, and call.
- As a tenant admin, I can update the Knowledge Base Q&A Form or add supporting knowledge so that future calls improve.
- As RingIQ, the product can preserve knowledge gaps even when the lead was otherwise classified as hot, warm, or callback requested.

**Product acceptance:**

- Knowledge gaps are visible in a dedicated dashboard area.
- Each knowledge gap has enough context for the tenant to improve answers.
- Knowledge gaps remain tenant-scoped.

## Suggested Product Build Sequence

1. Tenant accounts and workspace separation.
2. Tenant business profile setup.
3. Real estate Knowledge Base Q&A setup.
4. Lead CSV upload and validation.
5. Campaign creation and readiness checks.
6. Voice AI qualification pipeline.
7. Lead classification and follow-up queue.
8. Conversation records, recordings, transcripts, and summaries.
9. Tenant dashboard and campaign monitoring.
10. Knowledge gap improvement loop.

## Explicitly Not Included In This Story Map

- Provider selection.
- Framework selection.
- Database schema design.
- API endpoint design.
- Prompt implementation details.
- Telephony implementation details.
- Speech-to-text, LLM, or text-to-speech vendor decisions.
- Deployment architecture.
- Payment or billing implementation.
- Formal DND or consent workflows.
- CRM integration.
- Automated live transfer.

