---
title: RingIQ Voice AI Lead Calling SaaS
status: draft
created: 2026-07-16
updated: 2026-07-16
source_brd: ../../voice-ai-saas-business-requirements.md
---

# PRD: RingIQ Voice AI Lead Calling SaaS

## 0. Document Purpose

This Product Requirements Document defines the Version 1 product scope for RingIQ, a multi-tenant B2B SaaS platform that lets real estate businesses run AI voice-led first-touch lead qualification campaigns. It is written for product, UX, architecture, engineering, and future story creation. The document builds on the approved BRD at `../../voice-ai-saas-business-requirements.md` and translates it into user journeys, glossary terms, feature-level requirements, measurable outcomes, explicit non-goals, constraints, and architecture-facing open items.

The PRD deliberately avoids choosing implementation vendors or architecture. Telephony, STT, LLM, TTS, vector storage, database, authentication, hosting, and observability decisions belong in the architecture phase.

## 1. Vision

RingIQ helps lead-driven businesses stop wasting human sales capacity on repetitive first-touch calls. In Version 1, the product focuses on real estate companies that receive property inquiry leads and need to quickly identify which leads are worth a human follow-up.

A tenant uploads a CSV of leads, configures a business profile and knowledge base, and starts a campaign. RingIQ calls each lead, conducts a natural Hindi and/or English conversation, answers basic questions using only the tenant's private knowledge, classifies the lead's interest, captures callback requests, records the conversation, and surfaces hot, warm, and callback-requested leads for the tenant's sales team.

The product thesis is narrow: RingIQ does not replace real estate sales teams. It removes the noisy first-contact layer so human teams spend more time on leads with actual intent. Version 1 is successful if tenants can trust the AI agent to perform basic introductory qualification safely, consistently, and with enough evidence in the dashboard to support manual follow-up.

## 2. Context And Landscape

AI voice and AI SDR products are increasingly targeting the first layer of sales, support, and property-management communication. The current landscape matters because RingIQ needs a crisp wedge rather than a generic "AI caller" promise.

Relevant signals:

- Real estate CRMs such as CINC, BoomTown, Lofty, and RealOffice360 focus on lead management, pipeline, automation, and integrations, but they are broader CRM suites rather than narrow AI-first outbound qualification tools.
- Voice AI platforms and AI SDR products are moving toward autonomous qualification, appointment booking, and CRM-integrated workflows. Examples include Qualified's Piper for AI SDR workflows, EliseAI in housing and healthcare operations, OpenPhone/Quo's Sona voice agent, and NLPearl's phone-agent automation.
- Research and industry work around low-latency voice agents reinforces that natural voice interaction depends on streaming speech recognition, grounded dialogue management, and responsive text-to-speech rather than simple batch transcription.

Version 1 wedge:

- Real-estate-first, not horizontal-first.
- Outbound first-touch qualification, not full CRM replacement.
- Dashboard handoff to tenant sales teams, not autonomous closing.
- Hindi and English conversations for Indian market fit.
- Tenant-specific knowledge grounding and tenant data isolation from the beginning.

Sources consulted during PRD drafting:

- [Qualified company profile](https://en.wikipedia.org/wiki/Qualified_%28company%29)
- [EliseAI company profile](https://en.wikipedia.org/wiki/EliseAI)
- [NLPearl company profile](https://en.wikipedia.org/wiki/NLPearl)
- [TechRadar review of Quo/OpenPhone](https://www.techradar.com/pro/phone-communications/quo-review)
- [Low-latency telecom voice agent paper](https://arxiv.org/abs/2508.04721)
- [Call center transcript dataset paper](https://arxiv.org/abs/2507.02958)

## 3. Target Users

### 3.1 Primary Users

- Tenant Admin: configures tenant profile, uploads leads, manages knowledge base sources, starts campaigns, and reviews campaign health.
- Sales Manager: monitors lead outcomes, identifies hot and warm leads, checks call evidence, and assigns manual follow-up.
- Sales Representative: reviews qualified leads, listens to recordings or reads summaries when needed, and manually follows up outside RingIQ or through a future CRM workflow.
- Business Owner or Operations Head: evaluates whether RingIQ reduces first-touch calling workload and improves speed-to-lead.

### 3.2 Non-Users In Version 1

- End leads as logged-in users. Leads only interact through phone calls.
- Tenant billing administrators. Pricing and subscription management are out of scope.
- Compliance administrators. DND, consent tracking, and formal compliance workflows are deferred.
- Human call center agents using RingIQ as a live transfer console. Live transfer is out of scope.
- CRM operations teams. CRM integration is deferred.

### 3.3 Jobs To Be Done

- When I receive many new real estate leads, I want to contact them quickly so that interested buyers or renters do not go cold.
- When my sales team is overloaded, I want AI to filter first-touch conversations so humans focus on promising leads.
- When an AI call happens, I want recordings, transcripts, summaries, and classifications so I can trust and audit the outcome.
- When the AI cannot answer a lead's question, I want to see the knowledge gap so I can improve future calls.
- When a lead asks for a callback, I want the requested callback date and time captured so my sales team can act on it.
- When I use the platform as a tenant, I need confidence that my leads, recordings, transcripts, and knowledge base cannot leak into another tenant's workspace.

## 4. Key User Journeys

### UJ-1. Ananya uploads a real estate lead batch and starts first-touch qualification.

**Persona + context:** Ananya is a sales operations manager at a real estate brokerage. She receives a spreadsheet of property inquiry leads from a campaign and wants RingIQ to call them before the day ends.

**Entry state:** Ananya is authenticated as a tenant user in the RingIQ web dashboard. Her tenant already has a business profile and at least one active knowledge base source.

**Path:**

1. Ananya opens the Leads area and chooses to upload a CSV.
2. She uploads a file containing mandatory fields: lead name, email, and phone number.
3. The system validates the file, imports valid rows, and shows invalid rows with reasons.
4. Optional real estate fields such as area of interest, budget range, property type, buying or renting intent, and preferred timeline are accepted when present but not required.
5. Ananya confirms the campaign and keeps the default 3 retries after the initial unanswered call.

**Climax:** The campaign begins with valid leads queued for AI calls, and Ananya can see upload totals, rejected rows, and campaign status.

**Resolution:** Ananya leaves with a campaign in progress and a dashboard view that will update as calls are attempted.

**Edge case:** If mandatory fields are missing, Ananya sees row-level errors and can download or view rejected rows for correction.

### UJ-2. Imran receives an AI call and expresses buying intent.

**Persona + context:** Imran is a prospective home buyer who submitted a property inquiry. He prefers a Hindi-English conversation and wants to know whether properties are available in his preferred area and budget.

**Entry state:** Imran receives an outbound phone call from RingIQ on behalf of the real estate tenant.

**Path:**

1. The AI agent introduces itself and the represented real estate business.
2. The AI detects or adapts to Imran's Hindi, English, or mixed-language speech.
3. The AI answers property questions using only the tenant's knowledge base and business profile.
4. When optional lead fields are missing, the AI asks for details such as area of interest, budget range, property type, intent, and preferred timeline.
5. Imran says he wants to speak with someone about a site visit.

**Climax:** The AI classifies Imran as hot and records the qualification evidence.

**Resolution:** Imran is politely told that the business's sales team may follow up. The tenant sees Imran in the follow-up queue.

**Edge case:** If Imran asks a question not covered by the knowledge base, the AI avoids unsupported claims and flags a knowledge gap.

### UJ-3. Kavya reviews qualified leads for manual follow-up.

**Persona + context:** Kavya is a sales manager. She wants to know which leads deserve immediate human attention without listening to every call.

**Entry state:** Kavya opens the tenant dashboard after a campaign has run.

**Path:**

1. Kavya filters the lead list by hot, warm, and callback-requested outcomes.
2. She opens a lead detail page and reviews the call summary, interest classification, transcript, recording, callback date/time if present, and metadata.
3. She checks the campaign-level metrics to understand connection rate and unanswered call volume.
4. She shares or assigns follow-up manually outside RingIQ in Version 1.

**Climax:** Kavya confidently identifies leads worth manual follow-up.

**Resolution:** Sales representatives focus on qualified leads rather than the full uploaded batch.

**Edge case:** If a classification looks ambiguous, Kavya can inspect the transcript and recording, but formal human override workflows are deferred.

### UJ-4. Rakesh improves the tenant knowledge base after seeing gaps.

**Persona + context:** Rakesh is a tenant admin responsible for improving call quality. Several leads asked questions that the AI could not answer confidently.

**Entry state:** Rakesh opens the Knowledge Gaps view.

**Path:**

1. Rakesh reviews questions or conversation moments flagged as knowledge gaps.
2. He sees which campaign and call each gap came from.
3. He updates the Tenant's Knowledge Base Q&A Form or adds supporting Additional Knowledge Data.
4. Future calls use the updated Tenant knowledge after re-indexing or refresh.

**Climax:** Rakesh turns failed answers into concrete knowledge base improvements.

**Resolution:** The tenant's AI agent becomes better at answering common lead questions over time.

**Edge case:** If source refresh fails, RingIQ must preserve the prior active knowledge base version and surface the failure to the tenant admin.

## 5. Glossary

- **RingIQ** — The multi-tenant SaaS platform described by this PRD.
- **Tenant** — A business customer workspace. All Leads, Knowledge Base Q&A Forms, Knowledge Base Sources, Campaigns, Call Records, Recordings, Transcripts, Business Profiles, and Users belong to exactly one Tenant.
- **Tenant User** — A user who can access a Tenant workspace. In Version 1, all Tenant Users can access Recordings, Transcripts, and Call Records.
- **Lead** — A person uploaded by a Tenant for first-touch AI calling. A Lead must have name, email, and phone number.
- **Real Estate Qualification Fields** — Optional Lead fields for Version 1 real estate pilots: area of interest, budget range, property type, buying or renting intent, and preferred timeline.
- **Business Profile** — Tenant-provided structured context used by the AI Agent to generate the call flow and represent the business accurately.
- **Knowledge Base Source** — Tenant-provided knowledge content that grounds AI answers, including Knowledge Base Q&A Form answers and any approved Additional Knowledge Data.
- **Knowledge Base Q&A Form** — Category-specific structured question set that a Tenant completes to provide approved answers for the AI Agent. Version 1 includes a real estate question set.
- **Required Q&A Field** — A question in the Knowledge Base Q&A Form that must be answered before a Campaign can start.
- **Additional Knowledge Data** — Optional supporting information supplied by the Tenant beyond Required Q&A Fields.
- **Knowledge Base Index** — Searchable representation of a Tenant's Knowledge Base Sources used by the AI Agent. It must be tenant-isolated.
- **Campaign** — A batch-based calling run created from imported Leads and Tenant configuration.
- **Call Attempt** — One outbound dial attempt to a Lead.
- **Connected Call** — A Call Attempt where the Lead answers and the AI Agent conducts a conversation.
- **Retry** — A subsequent Call Attempt after an unanswered call. Version 1 default is 3 retries after the initial unanswered call.
- **AI Agent** — The voice agent that conducts the call using STT, LLM reasoning grounded in the Tenant Knowledge Base, and TTS.
- **Call Record** — The auditable record of a Call Attempt or Connected Call, including metadata, outcome, summary, Transcript reference, Recording reference, and failure reason where applicable.
- **Recording** — Audio captured for a Connected Call.
- **Transcript** — Text representation of a Connected Call.
- **Conversation Summary** — Short human-readable summary of the conversation.
- **Interest Classification** — Lead outcome assigned by the system: hot, warm, cold, callback requested, not interested, unanswered, invalid number, or needs review.
- **Hot Lead** — Lead expresses clear intent to proceed, visit, book, buy, rent, or speak with a sales representative soon.
- **Warm Lead** — Lead shows meaningful interest but needs more information, time, budget fit, location fit, or family or stakeholder discussion.
- **Cold Lead** — Lead gives weak, vague, or non-committal interest without a clear next step.
- **Callback Requested Lead** — Lead explicitly asks to be contacted later. Callback date/time should be captured when provided.
- **Knowledge Gap** — A question or call moment where the AI Agent could not answer confidently due to missing or insufficient Tenant knowledge.
- **Follow-Up Queue** — Dashboard view containing hot, warm, and callback-requested Leads for manual sales action.

## 6. Features And Functional Requirements

### 6.1 Tenant Workspace And Data Isolation

**Description:** RingIQ must support multiple Tenants while strictly isolating each Tenant's data and knowledge. This is the foundation for every other feature. A Tenant User must only access data belonging to their Tenant. Realizes UJ-1, UJ-3, and UJ-4.

#### FR-1: Tenant-scoped workspace

A Tenant User can access a Tenant workspace containing that Tenant's Leads, Campaigns, Business Profile, Knowledge Base Q&A Forms, Knowledge Base Sources, Call Records, Recordings, Transcripts, and dashboard views.

**Consequences:**

- Every persisted domain record is associated with exactly one Tenant.
- A Tenant User cannot view, search, list, download, or infer another Tenant's records.
- Tenant scoping applies to list views, detail views, file references, generated summaries, and Knowledge Base retrieval.

#### FR-2: Tenant-isolated knowledge retrieval

The AI Agent can retrieve answers only from the active Knowledge Base Index belonging to the same Tenant as the Campaign.

**Consequences:**

- Retrieval requests must include Tenant context.
- A Campaign cannot bind to a Knowledge Base Index owned by a different Tenant.
- Knowledge Gap flags must be stored under the same Tenant as the Call Record.

#### FR-3: Version 1 tenant access model

All Tenant Users can access Recordings, Transcripts, Call Records, imported Leads, and dashboard views for their Tenant.

**Consequences:**

- Version 1 does not require role-based access control inside a Tenant.
- The product must not imply private per-user access boundaries inside the same Tenant.
- Future role-based access control must remain possible without changing the core Tenant ownership model.

**Out of Scope:**

- Role-based access control within a Tenant.
- Per-record permissioning.
- Cross-tenant admin console.

### 6.2 Tenant Business Profile

**Description:** The Business Profile gives the AI Agent enough structured context to introduce the Tenant, generate the call flow, set expectations, and avoid unsupported claims. Realizes UJ-1 and UJ-2.

#### FR-4: Business profile creation and editing

A Tenant User can create and edit a Business Profile before running a Campaign.

**Consequences:**

- The Business Profile supports at least: business name, business category or vertical, primary locations served, default language preference, public contact number or follow-up contact instructions, short business description, promoted offerings, key value propositions, common customer questions and approved answers, follow-up instructions for hot/warm/callback-requested Leads, and disallowed claims or topics.
- For real estate Tenants, the Business Profile also supports project or property names, property locations, property types offered, budget ranges, availability or possession status where known, and site visit or sales follow-up process.
- A Campaign cannot start unless the Tenant has a minimum viable Business Profile.

#### FR-5: Business profile use in call-flow generation

The AI Agent can generate the conversation flow from the Business Profile, active Knowledge Base Index, platform-managed system prompt, and available Lead context.

**Consequences:**

- Tenant Users do not need to manually author a complete call script in Version 1.
- The generated flow must include business introduction, lead qualification, answer behavior, classification criteria, callback capture, and polite close.
- The generated flow must respect disallowed claims or topics.

**Out of Scope:**

- Visual script builder.
- A/B testing of call scripts.
- Tenant-authored advanced prompt editing.

### 6.3 Knowledge Base Management

**Description:** Tenants provide product, project, service, and FAQ knowledge through a structured Knowledge Base Q&A Form. The form is category-specific, with Version 1 focused on real estate. The system must support active knowledge content, required Q&A completion, optional Additional Knowledge Data, and knowledge gap feedback. Realizes UJ-2 and UJ-4.

#### FR-6: Category-specific knowledge base Q&A setup

A Tenant User can complete a Knowledge Base Q&A Form for the Tenant's business category.

**Consequences:**

- The system provides a category-specific question set, starting with real estate.
- The real estate question set covers at least business/project overview, locations and areas served, property types, budget ranges, availability or possession status, site visit process, pricing or payment disclaimers, common objections and approved responses, disallowed claims, and escalation or follow-up instructions.
- Tenant answers become Tenant-approved knowledge available to the AI Agent.
- The system stores Q&A content with Tenant ownership, update timestamp or version, active/inactive status, and indexed content reference where applicable.

#### FR-29: Required Q&A completion gate

The system requires Required Q&A Fields to be completed before a Campaign can start.

**Consequences:**

- A Campaign cannot start with an incomplete minimum Knowledge Base Q&A Form.
- Missing optional Q&A answers do not block Campaign creation.
- If the AI Agent encounters a topic missing from optional answers or Additional Knowledge Data, it must avoid unsupported claims and may create a Knowledge Gap.

#### FR-30: Additional knowledge data

A Tenant User can provide Additional Knowledge Data to supplement the Knowledge Base Q&A Form.

**Consequences:**

- Additional Knowledge Data can add context beyond Required Q&A Fields but does not replace the category-specific Q&A form.
- The AI Agent may use Additional Knowledge Data only when it belongs to the same Tenant and active knowledge set.
- Unusable or unsupported additional data is rejected or flagged rather than silently included.

#### FR-7: Knowledge-grounded answers

The AI Agent answers Lead questions using the Tenant's active Knowledge Base Index and Business Profile.

**Consequences:**

- If the AI Agent lacks sufficient knowledge, it must avoid unsupported claims.
- The AI Agent must remain within introductory qualification scope.
- The AI Agent must not answer from another Tenant's Knowledge Base Index.
- The AI Agent treats unanswered Q&A items as unknown information, not as permission to infer facts.

#### FR-8: Knowledge gap detection

The system identifies Knowledge Gaps from Connected Calls.

**Consequences:**

- A Knowledge Gap includes the question or moment, associated Tenant, Lead, Campaign, Call Record, and relevant Transcript reference where available.
- Knowledge Gaps appear in a dashboard view for Tenant Users.
- A Knowledge Gap can exist even when the final Interest Classification is hot, warm, or callback requested.

### 6.4 Lead Import And Validation

**Description:** Tenant Users upload CSV files of Leads. Version 1 requires only name, email, and phone number. Real estate qualification details are optional and may be collected by the AI Agent during the call. Realizes UJ-1.

#### FR-9: CSV upload

A Tenant User can upload a CSV of Leads.

**Consequences:**

- The CSV parser accepts mandatory fields: name, email, and phone number.
- The CSV parser accepts optional fields: city or location, source, product or service interest, notes, custom Tenant fields, requested callback date/time, and Real Estate Qualification Fields.
- Uploaded Leads are associated with a Tenant and Upload Batch.

#### FR-10: Row-level validation

The system validates uploaded Lead rows before Campaign calling begins.

**Consequences:**

- Rows missing name, email, or phone number are rejected.
- Invalid or unusable phone numbers are rejected or marked invalid before calling where detectable.
- The upload result shows imported rows, rejected rows, and rejection reasons.

#### FR-11: Optional real estate qualification fields

Real Estate Qualification Fields are optional in the uploaded CSV and can be collected by the AI Agent during a Connected Call.

**Consequences:**

- Missing area of interest, budget range, property type, buying or renting intent, or preferred timeline must not block import.
- If these fields are present, the AI Agent can use them to personalize the call.
- If these fields are missing, the AI Agent may ask for them during qualification.

### 6.5 Campaign Configuration And Calling

**Description:** A Campaign turns imported Leads into outbound AI calls. Version 1 supports one introductory Connected Call per Lead and retries only for unanswered calls. Realizes UJ-1 and UJ-2.

#### FR-12: Campaign creation from uploaded Leads

A Tenant User can create a Campaign from an Upload Batch of valid Leads.

**Consequences:**

- A Campaign must reference one Tenant, one set of Leads, the active Business Profile, the completed Required Q&A Fields, and the active Knowledge Base Index at the time the Campaign runs.
- Campaign status must be visible to Tenant Users.
- Campaign creation must not require pricing, billing, CRM integration, or scheduled calling windows.

#### FR-13: Default unanswered-call retry behavior

The system retries unanswered Leads up to 3 retries after the initial unanswered call unless Tenant configuration changes the retry count.

**Consequences:**

- Retries only apply when the call is unanswered or fails to connect.
- Retries do not apply after a Connected Call.
- A Lead should receive only one introductory Connected Call in Version 1.
- Call Attempts and retry counts are visible in Lead or Call Record details.

#### FR-14: Outbound call placement

The system places outbound calls to valid Campaign Leads.

**Consequences:**

- Each Call Attempt results in a Call Record.
- Call status includes at least queued, attempted, connected, unanswered, failed, and invalid number.
- Failure reason is captured where available.

**Out of Scope:**

- Scheduled calling windows.
- Multi-call nurture sequences.
- Automated live transfer.

### 6.6 AI Voice Conversation

**Description:** The AI Agent conducts the introductory phone conversation in Hindi, English, or mixed Hindi-English. It introduces the Tenant, qualifies the Lead, answers from Tenant knowledge, captures callback requests, and closes politely. Realizes UJ-2.

#### FR-15: Voice conversation loop

The AI Agent can conduct a natural voice conversation using speech-to-text, LLM response generation, and text-to-speech.

**Consequences:**

- The conversation supports Hindi, English, and natural mixed-language interaction.
- The AI Agent must be responsive enough to preserve a natural call experience.
- The AI Agent must continue to use Tenant context throughout the call.

#### FR-16: Business introduction and expectation setting

The AI Agent introduces itself and the represented Tenant clearly at the start of the call.

**Consequences:**

- The Lead understands which business the call is on behalf of.
- The AI Agent frames the call as introductory qualification.
- The AI Agent does not imply live human transfer or automated closing.

#### FR-17: Conversational qualification

The AI Agent asks enough questions to classify Lead interest using Version 1 Interest Classification labels.

**Consequences:**

- The AI Agent can classify the Lead as hot, warm, cold, callback requested, not interested, unanswered, invalid number, or needs review.
- The AI Agent can collect missing Real Estate Qualification Fields during the call.
- The AI Agent captures evidence for the classification in the Transcript, Conversation Summary, or Call Record.

#### FR-18: Callback capture

The AI Agent asks for and captures requested callback date and time when a Lead asks to be contacted later.

**Consequences:**

- Callback date/time is stored as structured data where the Lead provides it.
- Callback-requested Leads appear in the Follow-Up Queue.
- If the Lead requests a callback but does not provide a specific time, the Call Record indicates callback requested without a precise date/time.

#### FR-19: Safe answer behavior

The AI Agent avoids unsupported claims when knowledge is missing.

**Consequences:**

- The AI Agent may say that the sales team can follow up when it lacks approved knowledge.
- The AI Agent flags a Knowledge Gap for missing or insufficient information.
- The AI Agent does not invent property availability, pricing, legal terms, possession dates, discounts, or guarantees not present in Tenant knowledge.

### 6.7 Classification And Follow-Up Queue

**Description:** The system classifies every Lead outcome and makes hot, warm, and callback-requested Leads easy for sales teams to act on. Realizes UJ-3.

#### FR-20: Interest classification

The system assigns an Interest Classification during or immediately after the call lifecycle.

**Consequences:**

- Connected Calls receive a classification based on the conversation.
- Unanswered and invalid number outcomes can be assigned without a Connected Call.
- Needs review is used when the outcome is ambiguous or system confidence is too low.

#### FR-21: Follow-Up Queue

Tenant Users can view a Follow-Up Queue containing hot, warm, and callback-requested Leads.

**Consequences:**

- The queue shows Lead name, phone number, email, Interest Classification, Campaign, call time, callback date/time where applicable, and summary preview.
- Tenant Users can open a Lead detail view from the queue.
- The queue is tenant-scoped.

#### FR-22: Lead filtering

Tenant Users can filter Leads by status, Interest Classification, Upload Batch, Campaign, and call date.

**Consequences:**

- Filters can isolate unanswered, invalid number, hot, warm, callback requested, and needs review Leads.
- Filters do not expose cross-tenant data.
- Filters support campaign monitoring and follow-up triage.

### 6.8 Conversation Records, Recordings, And Transcripts

**Description:** Every Call Attempt and Connected Call must be auditable. Tenant Users need enough evidence to trust the classification and debug problems. Realizes UJ-3 and UJ-4.

#### FR-23: Call record creation

The system creates a Call Record for every Call Attempt.

**Consequences:**

- A Call Record includes Call ID, Tenant ID, Lead ID, Campaign or Upload Batch ID, start time, end time where available, duration where available, call status, Interest Classification where available, and failure reason where applicable.
- Connected Call records include Recording reference, Transcript reference where available, Conversation Summary, callback date/time where applicable, and Knowledge Gap flags.
- Call Records are retained indefinitely until a later retention policy is defined.

#### FR-24: Recording storage

The system stores a Recording for every Connected Call.

**Consequences:**

- The Recording is accessible to Tenant Users in Version 1.
- The Recording is linked from the Lead detail or Call Record detail view.
- Recordings are retained indefinitely until a later retention policy is defined.

#### FR-25: Transcript and summary storage

The system stores a Transcript where transcription is available and a Conversation Summary for every Connected Call where summary generation succeeds.

**Consequences:**

- Tenant Users can review the Transcript and Conversation Summary from the dashboard.
- If Transcript generation fails, the Call Record still exists and indicates the failure.
- Conversation Summary must not introduce claims unsupported by the Transcript.

### 6.9 Dashboard And Campaign Monitoring

**Description:** The dashboard is the Tenant's operating surface. It must help users understand upload health, call progress, lead outcomes, and knowledge gaps without spreadsheet work. Realizes UJ-1, UJ-3, and UJ-4.

#### FR-26: Campaign progress dashboard

Tenant Users can view Campaign progress.

**Consequences:**

- The dashboard shows total Leads uploaded, valid Leads, rejected Leads, calls queued, calls attempted, calls connected, calls unanswered, failed calls, invalid numbers, and Campaign status.
- Metrics are tenant-scoped.
- Campaign progress updates as call outcomes are recorded.

#### FR-27: Lead detail view

Tenant Users can open a Lead detail view.

**Consequences:**

- The Lead detail view shows Lead fields, Real Estate Qualification Fields where available, Campaign membership, Call Attempts, latest Interest Classification, Conversation Summary, Transcript, Recording, callback date/time where applicable, and Knowledge Gap flags.
- The Lead detail view is accessible from the Lead list and Follow-Up Queue.
- The Lead detail view does not provide automated live transfer or CRM push in Version 1.

#### FR-28: Knowledge gaps view

Tenant Users can view Knowledge Gaps discovered from Connected Calls.

**Consequences:**

- The view shows the gap content, associated Campaign, Lead, Call Record, and call date.
- Knowledge Gaps can be filtered by Campaign or date.
- Knowledge Gaps do not expose data from another Tenant.

## 7. Cross-Cutting Non-Functional Requirements

### 7.1 Tenant Isolation And Security

- **NFR-1:** Tenant data must be isolated at application, retrieval, storage, and dashboard access layers.
- **NFR-2:** Knowledge Base retrieval must never cross Tenant boundaries.
- **NFR-3:** Recordings, Transcripts, Lead records, and Call Records must be treated as sensitive data.
- **NFR-4:** The system should preserve an audit trail sufficient to investigate wrong classifications, failed calls, and knowledge leakage concerns.

### 7.2 Voice Experience And Performance

- **NFR-5:** Voice response latency should be low enough to preserve natural conversation flow. Exact thresholds will be set during architecture after provider selection. [ASSUMPTION: Version 1 will measure perceived conversation usability during pilots rather than commit to a hard latency SLA in the PRD.]
- **NFR-6:** The system should degrade gracefully when telephony, STT, LLM, TTS, retrieval, recording, or summarization fails.
- **NFR-7:** The system should support Hindi, English, and mixed Hindi-English conversations for Version 1 pilots.

### 7.3 Reliability And Observability

- **NFR-8:** Each Call Attempt must produce enough diagnostic information to understand status, timing, and failure reason where available.
- **NFR-9:** Failed downstream processing, such as Transcript or summary generation, must not erase the Call Record.
- **NFR-10:** Campaign-level counts must remain internally consistent with underlying Call Records.

### 7.4 Data Retention

- **NFR-11:** Lead records, Call Records, Recordings, Transcripts, Conversation Summaries, and Knowledge Gaps are retained indefinitely until a later retention policy is defined.
- **NFR-12:** The product should be designed so configurable retention and deletion policies can be added later without redesigning core data ownership.

## 8. Constraints And Guardrails

### 8.1 Product Guardrails

- RingIQ is a first-touch qualification tool in Version 1, not a full sales automation platform.
- Human sales teams remain responsible for final conversion and manual follow-up.
- The AI Agent must not claim that a human is live on the call.
- The AI Agent must not perform payment collection, deal closing, or legal commitment.

### 8.2 Compliance Guardrails

- DND registry checks are out of scope for Version 1.
- Consent tracking workflows are out of scope for Version 1.
- Formal regulatory compliance automation is out of scope for Version 1.
- The architecture should avoid choices that would make future DND, consent, retention, deletion, and audit features difficult.

### 8.3 AI Safety Guardrails

- The AI Agent must not invent real estate availability, price, discount, possession timeline, legal status, financing terms, or guarantees.
- The AI Agent must stay grounded in the Tenant Business Profile, Knowledge Base Q&A Form answers, and approved Additional Knowledge Data.
- Missing information should become a Knowledge Gap, not a hallucinated answer.

## 9. Non-Goals

- No automated live transfer to human sales representatives.
- No CRM integration.
- No pricing, billing, subscription, or invoicing workflows.
- No DND screening or consent tracking.
- No scheduled calling windows.
- No multi-call nurture sequence after a Connected Call.
- No full real estate CRM replacement.
- No role-based permissions inside a Tenant.
- No human review or approval workflow before AI classifications are surfaced.
- No autonomous deal closing, site-visit booking confirmation, payment collection, or legal commitment.
- No tenant-authored advanced prompt builder.

## 10. MVP Scope

### 10.1 In Scope

- Multi-tenant web SaaS workspace.
- Real-estate-first Version 1 pilot.
- Tenant Business Profile setup.
- Tenant Knowledge Base Q&A Form setup with real estate category questions.
- Optional Additional Knowledge Data for Tenant-approved context beyond the Q&A form.
- CSV Lead upload with mandatory name, email, and phone number.
- Optional Real Estate Qualification Fields.
- Campaign creation from imported Leads.
- Outbound introductory AI calls.
- Default 3 retries after the initial unanswered call.
- Hindi, English, and mixed-language AI voice conversation.
- Tenant-grounded AI answers.
- Interest Classification.
- Callback date/time capture.
- Recording, Transcript, Conversation Summary, and Call Record storage.
- Follow-Up Queue for hot, warm, and callback-requested Leads.
- Lead list, Lead detail, Campaign progress, and Knowledge Gaps dashboard views.
- Indefinite data retention until future policy exists.

### 10.2 Out Of Scope For MVP

- Pricing and billing.
- DND and consent workflows.
- Scheduled calling windows.
- CRM integrations.
- Automated live transfer.
- Human classification review workflow.
- Role-based access control.
- Multi-vertical launch beyond real estate pilots.
- Generic template upload as the primary knowledge base intake path.
- Advanced script designer or prompt editing.
- A/B testing.
- Lead scoring beyond Interest Classification.

## 11. Success Metrics

### Primary Metrics

- **SM-1: Qualified lead surfacing rate** — Percentage of valid uploaded Leads classified as hot, warm, or callback requested. Validates FR-17, FR-20, FR-21.
- **SM-2: Sales-accepted qualified lead rate** — Percentage of hot, warm, and callback-requested Leads that Tenant sales teams consider worth manual follow-up. Validates FR-20, FR-21, FR-25.
- **SM-3: First-touch workload reduction** — Percentage reduction in human first-touch calls required for uploaded Campaign Leads. Validates FR-12, FR-13, FR-14, FR-20.

### Secondary Metrics

- **SM-4: Upload success rate** — Percentage of uploaded rows accepted as valid Leads. Validates FR-9, FR-10.
- **SM-5: Call placement success rate** — Percentage of valid Leads with at least one Call Attempt. Validates FR-12, FR-14.
- **SM-6: Connection rate** — Percentage of valid Leads with a Connected Call. Validates FR-13, FR-14.
- **SM-7: Transcript availability rate** — Percentage of Connected Calls with usable Transcripts. Validates FR-25.
- **SM-8: Knowledge gap rate** — Number of Knowledge Gaps per Connected Call. Validates FR-8, FR-19, FR-28.
- **SM-9: Required Q&A completion rate** — Percentage of onboarded Tenants that complete Required Q&A Fields before their first Campaign. Validates FR-6, FR-29.
- **SM-10: Repeat campaign usage** — Percentage of pilot Tenants that run more than one Campaign. Validates overall product usefulness.

### Counter-Metrics

- **SM-C1: Wrong qualification complaints** — Track Tenant complaints where a Lead was clearly misclassified. Counterbalances SM-1 and SM-2.
- **SM-C2: Unsupported answer incidents** — Track calls where the AI Agent made a claim not grounded in Tenant knowledge. Counterbalances automation speed.
- **SM-C3: Excessive call duration** — Track calls that become too long without improving qualification. Counterbalances conversational completeness.
- **SM-C4: High knowledge gap rate without improvement** — Track Tenants whose Knowledge Gaps remain unresolved across Campaigns. Counterbalances reliance on weak knowledge content.

## 12. Risk Register

| Risk | Impact | Mitigation |
| --- | --- | --- |
| AI gives unsupported real estate answers | Tenant trust loss and potential lead harm | Knowledge-grounded answers, disallowed claims, Knowledge Gap flagging |
| Hindi-English voice quality feels unnatural | Leads hang up or do not engage | Pilot with realistic Indian real estate conversations and track call completion |
| Tenant data leakage | Severe trust and security failure | Tenant isolation as a first-class product and architecture invariant |
| Low answer rates | Weak campaign value | Default retries, connection metrics, future calling-window support |
| Lead classification errors | Sales teams waste time or miss opportunities | Evidence-backed summaries, recordings, transcripts, needs review outcome |
| Indefinite retention increases exposure | Privacy and storage risk | Treat call artifacts as sensitive and design future retention controls |
| Incomplete Tenant knowledge | AI cannot answer common questions | Required Knowledge Base Q&A Form, Additional Knowledge Data, Knowledge Gap workflow, and source refresh process |
| Compliance requirements become urgent | Pilot or launch delay | Keep DND, consent, and retention extensibility explicit in architecture |

## 13. Open Questions For Architecture And UX

These are not blockers for the PRD, but they must be resolved before implementation planning.

1. Which telephony provider will support outbound calling, retries, recording, and call status callbacks for the target market?
2. Which STT, LLM, retrieval, and TTS providers meet Hindi-English quality and latency needs?
3. What exact latency budget defines an acceptable voice conversation for Version 1?
4. What storage model should be used for Recordings and Transcripts under indefinite retention?
5. How should Tenant isolation be enforced across database access, object storage, retrieval, and background jobs?
6. What UX should Tenant Users see while a Campaign is running: live progress, periodic refresh, or post-run results?
7. How should callback date/time be normalized when Leads provide vague phrases such as "tomorrow evening"?
8. What is the minimum Business Profile validation required before allowing a Campaign to start?
9. Which real estate Knowledge Base Q&A questions are Required Q&A Fields versus optional questions?
10. How should Knowledge Base Q&A refresh and re-indexing be represented to Tenant Users?
11. What analytics events are required to measure the success metrics without over-instrumenting the MVP?

## 14. Assumptions Index

- §7.2 NFR-5 — [ASSUMPTION] Version 1 will measure perceived conversation usability during pilots rather than commit to a hard latency SLA in the PRD.

## 15. Release Readiness Checklist

Before architecture ideation begins, the team should confirm:

- The PRD's Glossary terms are accepted as canonical.
- The Version 1 non-goals are accepted and will not be reintroduced during architecture.
- The architecture will treat Tenant isolation, Knowledge Base isolation, and call artifact retention as core invariants.
- The architecture will explicitly evaluate Hindi-English voice quality and latency.
- UX work will cover Business Profile setup, Knowledge Base Q&A Form setup, upload validation, Campaign progress, Lead detail, Follow-Up Queue, and Knowledge Gaps views.
- Future compliance, retention, RBAC, CRM integration, scheduled calling, and live transfer will remain extensibility considerations rather than Version 1 scope.
