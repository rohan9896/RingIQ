# Business Requirements Document: Multi-Tenant Voice AI Lead Calling SaaS

## 1. Executive Summary

The proposed product is a multi-tenant B2B SaaS platform that enables businesses to automatically place introductory calls to uploaded leads using an AI voice agent. Version 1 will focus on real estate companies as the first pilot segment, while the broader product direction remains applicable to gyms, edtech providers, automotive vendors, and other lead-driven businesses that currently rely on human calling teams for first-touch qualification.

The platform will allow each business tenant to upload a CSV of leads, connect or upload its own product knowledge base, configure basic retry behavior, and run outbound AI calling campaigns. The AI agent will conduct natural conversations in Hindi and/or English, answer lead questions using the tenant's private knowledge base, classify lead interest in real time, and surface interested leads for manual follow-up by the tenant's sales team.

The initial product version focuses on validating whether AI voice agents can reliably perform first-touch lead qualification. Automated live transfer, pricing design, and formal regulatory compliance workflows such as DND screening and consent tracking are intentionally out of scope for the validation phase.

## 2. Business Context

Many businesses depend on fast lead follow-up, but first-touch calling is operationally expensive, inconsistent, and difficult to scale. Human calling teams often spend significant time on unanswered calls, low-intent leads, repetitive introductory explanations, and manual disposition updates.

The opportunity is to automate the repetitive first-contact layer while preserving human involvement for high-value follow-up. The product should not attempt to replace the full sales process in the first version. Instead, it should help sales teams focus their effort on leads that show genuine interest after an introductory AI-led conversation.

## 3. Business Objectives

1. Reduce the manual effort required for initial lead outreach.
2. Increase speed-to-lead by enabling automated calls soon after lead upload.
3. Improve sales team productivity by surfacing only interested or promising leads.
4. Provide businesses with auditable call recordings, transcripts, and outcomes.
5. Allow each tenant to ground AI conversations in its own private product knowledge base.
6. Validate market demand and operational feasibility before investing in complex compliance, pricing, and live-transfer workflows.

## 4. Target Customers

### 4.1 Primary Customer Segments

- Real estate brokers, developers, and agencies that receive property inquiry leads. This is the Version 1 pilot segment.
- Gyms and fitness centers that receive membership inquiries.
- Edtech providers that receive course, demo, or admission leads.
- Automotive dealers or vendors that receive vehicle inquiry leads.
- Other SMB or mid-market businesses with high-volume inbound leads and repetitive qualification calls.

### 4.2 Primary Users

- Business owner or operations head: wants reduced calling cost and better lead conversion.
- Sales manager: wants qualified leads, call visibility, and team follow-up workflows.
- Sales representative: manually follows up with interested leads.
- Tenant admin: uploads leads, manages knowledge base content, and configures calling behavior.

## 5. Problem Statement

Lead-driven businesses need a scalable way to contact and qualify large numbers of leads without expanding human calling teams. Existing manual calling processes are slow, expensive, inconsistent, and waste human sales capacity on unanswered or low-intent calls.

The business needs a platform that can perform introductory outbound calls, answer basic questions from tenant-specific knowledge, classify interest, and hand off qualified leads to the business's own team for manual follow-up.

## 6. Scope

### 6.1 In Scope for Version 1

- Multi-tenant SaaS platform.
- Tenant account and workspace separation.
- CSV lead upload.
- Tenant-specific product knowledge base connection or upload.
- One introductory outbound call per lead.
- Configurable retry attempts for unanswered calls.
- AI voice conversation in Hindi and/or English.
- Speech-to-text processing.
- LLM responses grounded in the tenant's private knowledge base.
- Text-to-speech response generation.
- Real-time or near-real-time lead interest classification.
- Dashboard showing lead status and interested leads.
- Call recording, transcript, and conversation log storage.
- Knowledge base gap flagging from unanswered or poorly answered questions.
- Strict data isolation between tenants.

### 6.2 Out of Scope for Version 1

- Automated live transfer to human sales agents.
- Payment, subscription, or pricing workflows.
- Formal DND registry checks.
- Consent tracking workflows.
- Full regulatory compliance automation.
- CRM marketplace integrations unless added later as a separate requirement.
- Multi-step sales nurture sequences beyond the introductory call and configured retries.
- Scheduled calling windows.
- Human review workflows for AI lead classification.
- Fully autonomous deal closing or payment collection.

## 7. Key Business Capabilities

### 7.1 Tenant Management

The platform must support multiple business tenants with strict separation of users, leads, knowledge base content, calls, recordings, transcripts, analytics, and configuration.

### 7.2 Lead Upload and Campaign Creation

Tenant users must be able to upload leads through CSV files. The system must validate required fields, identify invalid records, and prepare valid leads for calling.

### 7.3 Knowledge Base Grounding

Each tenant must be able to provide product or service knowledge that the AI agent uses during calls. The AI must not use one tenant's knowledge base to answer another tenant's lead.

### 7.4 AI Voice Calling

The system must place outbound calls to leads and conduct an introductory conversation through a voice AI agent. The agent must be able to communicate in Hindi, English, or a natural mix of both where appropriate.

### 7.5 Lead Qualification

The system must classify each lead's interest level based on the conversation. Leads marked as hot, warm, or callback requested must be surfaced clearly for manual sales follow-up.

Initial classification definitions:

- Hot: lead expresses clear intent to proceed, visit, book, buy, rent, or speak with a sales representative soon.
- Warm: lead shows meaningful interest but needs more information, time, budget fit, location fit, or family or stakeholder discussion.
- Cold: lead gives weak, vague, or non-committal interest without a clear next step.
- Callback requested: lead explicitly asks to be contacted later.
- Not interested: lead clearly declines or says the offering is not relevant.
- Unanswered: call does not connect with the lead.
- Invalid number: number is unreachable, incorrect, or not usable for calling.
- Needs review: conversation outcome is ambiguous or system confidence is too low to classify reliably.

### 7.6 Conversation Audit Trail

Every completed conversation must produce a call record containing call metadata, recording, transcript, summary, disposition, and interest classification.

### 7.7 Knowledge Base Gap Detection

The system must flag questions or conversation moments where the AI could not answer confidently due to missing or insufficient tenant knowledge.

## 8. Functional Requirements

| ID | Requirement | Priority |
| --- | --- | --- |
| BR-FR-001 | The system shall allow a tenant admin to upload a CSV file containing lead records. | Must |
| BR-FR-002 | The system shall validate uploaded CSV files for required lead fields: name, email, and phone number. | Must |
| BR-FR-003 | The system shall show rejected or invalid lead rows with reasons. | Must |
| BR-FR-004 | The system shall allow each tenant to configure the number of retry attempts for unanswered calls. | Must |
| BR-FR-005 | The system shall place one introductory call per valid lead, with retries only when the lead does not answer. | Must |
| BR-FR-006 | The system shall support AI voice conversations in Hindi and English. | Must |
| BR-FR-007 | The system shall convert lead speech to text during calls. | Must |
| BR-FR-008 | The system shall generate AI responses using an LLM grounded in the tenant's private knowledge base. | Must |
| BR-FR-009 | The system shall convert AI responses to speech during calls. | Must |
| BR-FR-010 | The system shall classify lead interest during or immediately after the call. | Must |
| BR-FR-011 | The system shall provide at least these lead outcomes: hot, warm, cold, callback requested, not interested, unanswered, invalid number, and needs review. | Must |
| BR-FR-012 | The system shall display interested leads on a dashboard for tenant sales teams. | Must |
| BR-FR-013 | The system shall store a call recording for every connected call. | Must |
| BR-FR-014 | The system shall store a transcript for every connected call where transcription is available. | Must |
| BR-FR-015 | The system shall store call metadata, including call time, duration, status, lead, tenant, and outcome. | Must |
| BR-FR-016 | The system shall identify and flag knowledge base gaps from conversations. | Should |
| BR-FR-017 | The system shall allow tenant users to view conversation logs and recordings from the dashboard. | Must |
| BR-FR-018 | The system shall prevent users from accessing data belonging to another tenant. | Must |
| BR-FR-019 | The system shall allow tenant users to filter leads by status, interest level, upload batch, and call date. | Should |
| BR-FR-020 | The system shall provide a summary of each completed conversation. | Should |
| BR-FR-021 | The system shall allow the AI agent to generate the call flow from the tenant's business profile, knowledge base, and a platform-managed system prompt. | Must |
| BR-FR-022 | The system shall support optional vertical-specific lead fields, starting with real estate fields such as area of interest, budget range, property type, buying or renting intent, and preferred timeline. | Should |
| BR-FR-023 | The system shall capture callback date and time when a lead asks to be contacted later. | Must |

## 9. Non-Functional Requirements

| ID | Requirement | Priority |
| --- | --- | --- |
| BR-NFR-001 | Tenant data must be strictly isolated at the application and data-access layers. | Must |
| BR-NFR-002 | The platform must maintain separate knowledge base indexes or access boundaries per tenant. | Must |
| BR-NFR-003 | The system must be designed to support concurrent campaigns across multiple tenants. | Must |
| BR-NFR-004 | Call logs, recordings, transcripts, and classifications must be auditable. | Must |
| BR-NFR-005 | The AI agent should respond with low enough latency to preserve natural conversation flow. | Must |
| BR-NFR-006 | The system should degrade gracefully when STT, LLM, TTS, or telephony services fail. | Must |
| BR-NFR-007 | The dashboard should make high-priority leads easy to identify without manual spreadsheet work. | Must |
| BR-NFR-008 | The system should retain enough diagnostic information to debug failed calls and AI response issues. | Should |
| BR-NFR-009 | The product should be extensible for future compliance, CRM integration, pricing, and live-transfer modules. | Should |
| BR-NFR-010 | Recordings, transcripts, call logs, and lead records shall be retained indefinitely until a later retention policy is defined. | Must |

## 10. Business Rules

1. A lead belongs to exactly one tenant.
2. A knowledge base belongs to exactly one tenant.
3. A call campaign may only use the knowledge base configured for the same tenant.
4. The AI agent must not access or infer data from another tenant.
5. A lead should receive only one introductory connected call in Version 1.
6. Retry attempts apply only when a call is unanswered or fails to connect.
7. Interested leads are handed off through the dashboard, not through live transfer.
8. All connected conversations must be recorded and logged for audit.
9. Knowledge base gaps should be visible to tenant admins or operators for improvement.
10. Compliance workflows are acknowledged as future requirements, but not part of Version 1 validation scope.
11. All tenant users may access recordings, transcripts, and lead call logs in Version 1.
12. Human review is not required before the system surfaces or stores AI-generated lead classifications.
13. The AI call flow is generated by the system using tenant context and a platform-managed system prompt; tenants do not need to manually author a full call script in Version 1.
14. The default retry count is 3 retries after the initial unanswered call.
15. Callback date and time should be captured as structured data when the lead provides it during the call.

## 11. Lead Lifecycle

1. Tenant uploads a CSV of leads.
2. System validates and imports valid leads.
3. Tenant confirms or configures call campaign settings.
4. System places an introductory outbound call to each lead.
5. If unanswered, the system retries according to tenant configuration.
6. If connected, the AI agent conducts the conversation.
7. System records, transcribes, summarizes, and classifies the conversation.
8. Hot, warm, and callback-requested leads appear on the tenant dashboard.
9. Tenant sales team manually follows up outside or alongside the platform.
10. Knowledge base gaps are reviewed and used to improve future calls.

## 12. Dashboard Requirements

The tenant dashboard must give business users a clear operating view of uploaded leads, call progress, and qualified follow-up leads.

Minimum dashboard views:

- Lead list with call status and interest outcome.
- Follow-up queue for hot, warm, and callback-requested leads.
- Individual lead detail page with call recording, transcript, summary, and metadata.
- Campaign or upload batch progress view.
- Knowledge base gap list.

Recommended dashboard metrics:

- Total leads uploaded.
- Calls attempted.
- Calls connected.
- Calls unanswered.
- Hot leads.
- Warm leads.
- Not interested leads.
- Callback requested leads.
- Knowledge gaps detected.

## 13. Data Requirements

### 13.1 Lead Data

Minimum lead fields:

- Lead name.
- Email.
- Phone number.
- Tenant ID.
- Upload batch ID.
- Call status.
- Interest classification.
- Created date.
- Last call attempt date.

Optional lead fields:

- City or location.
- Source.
- Product or service interest.
- Notes.
- Custom tenant fields.
- Requested callback date and time.

Version 1 real estate lead fields are optional in the uploaded CSV. If these fields are missing, the AI agent may collect them during the call:

- Area of interest.
- Budget range.
- Property type.
- Buying or renting intent.
- Preferred timeline.

Future vertical-specific examples:

- Edtech: domain or course interest.
- Fitness: membership goal or preferred location.
- Automotive: vehicle model or segment of interest.

### 13.2 Call Data

Minimum call fields:

- Call ID.
- Tenant ID.
- Lead ID.
- Campaign or batch ID.
- Call start time.
- Call end time.
- Duration.
- Call status.
- Recording reference.
- Transcript reference.
- Conversation summary.
- Interest classification.
- Requested callback date and time, where applicable.
- Knowledge gap flags.
- Failure reason, where applicable.

### 13.3 Knowledge Base Data

Minimum knowledge base fields:

- Tenant ID.
- Source name.
- Source type.
- Version or update timestamp.
- Indexed content reference.
- Active or inactive status.

### 13.4 Tenant Business Profile Data

Minimum tenant business profile fields:

- Business name.
- Business category or vertical.
- Primary locations served.
- Default language preference.
- Public contact number or follow-up contact instructions.
- Short business description.
- Products, services, projects, or inventory being promoted.
- Key value propositions.
- Common customer questions and approved answers.
- Follow-up instructions for hot, warm, and callback-requested leads.
- Disallowed claims or topics the AI should avoid.

For real estate tenants, the business profile should also capture:

- Project or property names.
- Property locations.
- Property types offered.
- Budget ranges.
- Availability or possession status, where known.
- Site visit or sales follow-up process.

## 14. AI Behavior Requirements

The AI voice agent must:

- Introduce itself and the represented business clearly.
- Keep the conversation focused on introductory qualification.
- Answer questions using only tenant-approved knowledge.
- Avoid making unsupported claims when knowledge is missing.
- Classify the lead as hot, warm, cold, callback requested, not interested, unanswered, invalid number, or needs review.
- Generate the conversation flow using the platform-managed system prompt, tenant business profile, tenant knowledge base, and available lead context.
- Ask for and capture callback date and time when a lead requests a later follow-up.
- Flag questions it could not answer confidently.
- Maintain a natural Hindi, English, or mixed-language conversation based on the lead's language.
- End the call politely and set expectations that a human team member may follow up where appropriate.

## 15. Success Metrics

Initial validation should focus on product usefulness and operational reliability rather than revenue optimization.

Recommended success metrics:

- Lead upload success rate.
- Percentage of calls successfully placed.
- Connection rate.
- Average call duration.
- Percentage of conversations with usable transcripts.
- Lead classification usefulness based on downstream sales team follow-up behavior.
- Percentage of hot, warm, and callback-requested leads accepted by sales teams as worth follow-up.
- Reduction in manual first-touch calling workload.
- Number of knowledge base gaps detected per campaign.
- Tenant retention or repeated campaign usage during pilots.

## 16. Assumptions

1. Tenants have lawful access to the leads they upload.
2. Tenants are responsible for the accuracy of their knowledge base content.
3. Initial pilots will start with real estate companies before broader release to other verticals.
4. Human sales teams remain responsible for final conversion and follow-up.
5. Formal compliance, consent, retention policy, and pricing workflows will be designed after core product validation.
6. Telephony, STT, LLM, TTS, and storage providers will be selected separately during technical planning.

## 17. Risks and Mitigations

| Risk | Business Impact | Mitigation |
| --- | --- | --- |
| AI gives incorrect or unsupported answers | Loss of tenant trust and poor lead experience | Ground responses in tenant knowledge base and flag low-confidence gaps |
| Poor Hindi-English voice quality | Low call completion and weak user experience | Test voice stack with realistic Indian customer conversations |
| Tenant data leakage | Severe trust and security failure | Enforce tenant isolation at data, retrieval, and application layers |
| Low answer rates | Weak campaign ROI | Provide retry configuration and track connection metrics |
| Lead classification errors | Sales teams may miss opportunities or waste time | Provide reviewable transcripts, summaries, and human override later |
| Indefinite data retention increases exposure | Larger privacy, security, and storage risk over time | Treat recordings and transcripts as sensitive data and design future retention controls |
| Regulatory constraints emerge during pilots | Product rollout delays | Keep compliance architecture extensible even if workflows are out of Version 1 scope |
| Knowledge base content is incomplete | AI cannot answer common questions | Surface knowledge gaps as an explicit improvement workflow |

## 18. Future Considerations

Future versions may include:

- DND and consent management.
- CRM integrations.
- Automated human handoff or live transfer.
- Pricing and subscription management.
- More advanced campaign scheduling.
- Lead scoring models.
- Multi-call nurture sequences.
- Human review and correction of AI classifications.
- Role-based access control within each tenant.
- Configurable data retention and deletion policies.
- A/B testing of call scripts and agent personas.
- Analytics for sales conversion after manual follow-up.

## 19. Resolved Decisions

1. Version 1 will start with real estate companies.
2. Name, email, and phone number are mandatory CSV fields.
3. Vertical-specific fields are supported as optional or custom fields; real estate starts with area of interest, budget range, property type, buying or renting intent, and preferred timeline.
4. The AI should generate the call flow using tenant context and a platform-managed system prompt.
5. Suggested Version 1 classification labels are hot, warm, cold, callback requested, not interested, unanswered, invalid number, and needs review.
6. Scheduled calling windows are not part of Version 1.
7. Data is retained indefinitely until a later retention policy is defined.
8. All tenant users may access recordings and transcripts in Version 1.
9. Human review is not required before using AI-generated lead classifications in Version 1.
10. The default retry count is 3 retries after the initial unanswered call.
11. The platform should capture callback date and time when a lead asks to be contacted later.
12. Minimum tenant business profile fields should include business name, vertical, locations served, language preference, follow-up contact instructions, business description, promoted offerings, value propositions, common FAQs, follow-up rules, and disallowed claims.
13. Real estate qualification fields are optional in the uploaded CSV and may be collected by the AI during the call.

## 20. Remaining Open Questions

No open business requirement questions remain from the current discovery pass.

## 21. Acceptance Criteria

The Version 1 business requirement is satisfied when:

1. A tenant can upload leads through CSV with name, email, and phone number.
2. A tenant can provide a private knowledge base.
3. The system can place outbound introductory calls to uploaded leads.
4. The AI agent can conduct Hindi and/or English conversations grounded in tenant knowledge.
5. The system can retry unanswered calls up to the default 3-retry limit unless tenant configuration changes it.
6. The system records and logs each connected conversation.
7. The system classifies lead interest using the Version 1 classification labels.
8. Hot, warm, and callback-requested leads are visible on a tenant-specific dashboard.
9. Tenant data and knowledge bases remain isolated.
10. Knowledge base gaps can be identified from conversations.
11. Callback date and time can be captured when a lead requests a later follow-up.
