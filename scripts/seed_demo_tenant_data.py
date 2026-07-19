import argparse
import asyncio
import sys
from datetime import datetime, timezone
from pathlib import Path

from sqlalchemy import func, select
from sqlalchemy.orm import selectinload

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from apps.api.ringiq_api.db.session import dispose_database, get_session_factory  # noqa: E402
from apps.api.ringiq_api.models.campaigns import (  # noqa: E402
    Campaign,
    CampaignEnrollment,
    CampaignStatus,
)
from apps.api.ringiq_api.models.catalog import (  # noqa: E402
    Category,
    CategoryStatus,
    CategoryTemplateVersion,
    QnaQuestion,
    QuestionAnswerType,
    TemplateStatus,
)
from apps.api.ringiq_api.models.identity import (  # noqa: E402
    RecordStatus,
    Tenant,
    TenantMembership,
    User,
    UserRealm,
)
from apps.api.ringiq_api.models.knowledge import (  # noqa: E402
    TenantKnowledgeBase,
    TenantKnowledgeBaseVersion,
    TenantKnowledgeQuestion,
)
from apps.api.ringiq_api.models.leads import (  # noqa: E402
    Lead,
    LeadImport,
    LeadImportRow,
    LeadImportRowStatus,
)


CATEGORY_KEY = "real_estate"
TEMPLATE_TITLE = "Real Estate Starter Knowledge"
DEMO_IMPORT_FILENAME = "ringiq-demo-real-estate-leads.csv"
DEMO_CAMPAIGN_NAME = "Demo Real Estate Outreach"
DEMO_BUSINESS_NAME_TOKEN = "{business_name}"

LEAD_SCHEMA = {
    "required": ["name", "email", "phone_number"],
    "optional": [
        {
            "key": "area_of_interest",
            "label": "Area of interest",
            "type": "short_text",
        },
        {
            "key": "budget_range",
            "label": "Budget range",
            "type": "short_text",
        },
        {
            "key": "property_type",
            "label": "Property type",
            "type": "single_select",
            "options": ["Apartment", "Villa", "Plot", "Commercial"],
        },
        {
            "key": "buying_timeline",
            "label": "Buying timeline",
            "type": "short_text",
        },
    ],
}

TEMPLATE_QUESTIONS = [
    {
        "key": "business_summary",
        "label": "What does your real estate business offer?",
        "help_text": "Cover city, project types, target buyers, and positioning.",
        "answer_type": QuestionAnswerType.LONG_TEXT.value,
        "required": True,
        "display_order": 0,
        "answer": (
            f"{DEMO_BUSINESS_NAME_TOKEN} helps home buyers discover ready-to-move and "
            "under-construction residential projects across Gurgaon and Noida. "
            "The team focuses on first-home buyers, working professionals, and "
            "families upgrading from rented apartments. The assistant should help "
            "the caller narrow location, budget, property type, and callback intent."
        ),
    },
    {
        "key": "locations_served",
        "label": "Which locations do you serve?",
        "help_text": "List the areas that callers can ask about.",
        "answer_type": QuestionAnswerType.LONG_TEXT.value,
        "required": True,
        "display_order": 1,
        "answer": (
            "Golf Course Extension Road, Sector 62, Sector 65, Dwarka Expressway, "
            "Noida Sector 150, and Noida Extension. Gurgaon is better for buyers "
            "prioritizing office commute, premium gated societies, and quicker rental "
            "demand. Noida is better for buyers looking for relatively larger layouts, "
            "newer infrastructure, and a more value-focused entry price."
        ),
    },
    {
        "key": "budget_ranges",
        "label": "What budget ranges are available?",
        "help_text": "Mention broad bands rather than exact pricing promises.",
        "answer_type": QuestionAnswerType.LONG_TEXT.value,
        "required": True,
        "display_order": 2,
        "answer": (
            "Most current options start around 85 lakh and go up to 3.5 crore, "
            "depending on location, configuration, floor, and possession stage. "
            "For 2 BHK homes, guide callers to 85 lakh-1.35 crore. For 3 BHK homes, "
            "guide callers to 1.25-2.4 crore. For premium 3/4 BHK homes or villas, "
            "guide callers to 2.25-3.5 crore. Avoid promising exact pricing because "
            "inventory, floor rise, PLC, taxes, parking, and offers may change."
        ),
    },
    {
        "key": "qualification_questions",
        "label": "What should the assistant ask to qualify interest?",
        "help_text": "Questions used during the first introductory call.",
        "answer_type": QuestionAnswerType.LONG_TEXT.value,
        "required": True,
        "display_order": 3,
        "answer": (
            "Ask preferred location, budget range, property type, purchase timeline, "
            "and whether the customer wants a callback from a sales advisor. Good "
            "questions: Are you looking for Gurgaon or Noida? What budget range are "
            "you comfortable with? Do you prefer ready-to-move or under-construction? "
            "Is this for self-use or investment? When would you like to visit the site? "
            "Should our sales advisor call you today?"
        ),
    },
    {
        "key": "handoff_criteria",
        "label": "When should the lead be marked interested?",
        "help_text": "Signals that should surface the lead on the dashboard.",
        "answer_type": QuestionAnswerType.LONG_TEXT.value,
        "required": True,
        "display_order": 4,
        "answer": (
            "Mark interested when the person shares a location or budget, asks for "
            "project details, requests a site visit, asks about payment plans, confirms "
            "purchase timeline, or agrees to a callback. Mark warm if they are exploring "
            "but reveal budget/location. Mark not interested if they clearly decline, ask "
            "not to be contacted, say wrong number, or have no property requirement."
        ),
    },
    {
        "key": "project_inventory",
        "label": "What sample projects and inventory can the assistant mention?",
        "help_text": "Use illustrative demo inventory for natural conversations.",
        "answer_type": QuestionAnswerType.LONG_TEXT.value,
        "required": False,
        "display_order": 5,
        "answer": (
            "Demo inventory: 2 and 3 BHK apartments near Dwarka Expressway with expected "
            "possession in 18-30 months; ready-to-move 3 BHK homes near Golf Course "
            "Extension Road; premium gated apartments in Sector 65; value-focused 2/3 BHK "
            "options in Noida Extension; low-density residential projects around Noida "
            "Sector 150. The assistant can say these are broad available options and a "
            "sales advisor will confirm live inventory."
        ),
    },
    {
        "key": "amenities_and_highlights",
        "label": "Which amenities and selling points should be mentioned?",
        "help_text": "Useful when a caller asks why a project is worth considering.",
        "answer_type": QuestionAnswerType.LONG_TEXT.value,
        "required": False,
        "display_order": 6,
        "answer": (
            "Common highlights include gated security, clubhouse, gym, swimming pool, "
            "children's play area, landscaped greens, basement parking, power backup, "
            "high-speed lifts, and proximity to schools, hospitals, metro/expressway "
            "connectivity, offices, and retail. For investment-oriented callers, mention "
            "rental demand, infrastructure growth, and developer track record without "
            "guaranteeing returns."
        ),
    },
    {
        "key": "payment_and_loan_guidance",
        "label": "How should the assistant answer payment and loan questions?",
        "help_text": "Keep financial guidance useful but non-committal.",
        "answer_type": QuestionAnswerType.LONG_TEXT.value,
        "required": False,
        "display_order": 7,
        "answer": (
            "The assistant can say that most projects support bank loans from major banks, "
            "booking amounts vary by project, and payment plans can include construction-"
            "linked, possession-linked, or limited-period offer plans. Do not quote final "
            "EMI, loan eligibility, discounts, or legal/tax advice. Offer to arrange a "
            "callback so the sales advisor can share the latest payment plan."
        ),
    },
    {
        "key": "site_visit_process",
        "label": "How are site visits handled?",
        "help_text": "The call should be able to convert interest into follow-up.",
        "answer_type": QuestionAnswerType.LONG_TEXT.value,
        "required": False,
        "display_order": 8,
        "answer": (
            "If a caller wants a site visit, capture preferred location, day, time window, "
            "number of visitors, and whether pickup assistance is needed. Say that a sales "
            "advisor will call back to confirm the exact slot, meeting point, and project "
            "availability. Do not promise a confirmed visit during the automated call."
        ),
    },
    {
        "key": "common_objections",
        "label": "How should common objections be handled?",
        "help_text": "Short responses for natural call handling.",
        "answer_type": QuestionAnswerType.LONG_TEXT.value,
        "required": False,
        "display_order": 9,
        "answer": (
            "If the caller says price is high, ask their preferred budget and suggest that "
            "there may be alternate projects. If they are only browsing, ask when they plan "
            "to buy and whether a short WhatsApp summary or callback would help. If they "
            "ask for exact inventory or discounts, say the advisor will confirm live details. "
            "If they are busy, politely ask for a better callback time."
        ),
    },
    {
        "key": "conversation_guardrails",
        "label": "What should the assistant avoid saying?",
        "help_text": "Protects the call from overpromising.",
        "answer_type": QuestionAnswerType.LONG_TEXT.value,
        "required": False,
        "display_order": 10,
        "answer": (
            "Do not claim guaranteed appreciation, guaranteed rental returns, fixed discounts, "
            "legal clearance, RERA status, exact possession date, or final all-inclusive price "
            "unless the knowledge base explicitly provides it. Do not pressure the caller. "
            "Do not say the caller is speaking to an AI assistant. Keep answers concise and "
            "move toward a human callback when details become specific."
        ),
    },
    {
        "key": "language_and_tone",
        "label": "What language and tone should the assistant use?",
        "help_text": "Keeps Hindi, English, and Hinglish calls natural.",
        "answer_type": QuestionAnswerType.LONG_TEXT.value,
        "required": False,
        "display_order": 11,
        "answer": (
            "Start with: Namaste! Kaise hain aap? Introduce as RingIQ ka assistant for "
            "the tenant organization. Use polite Indian business Hinglish by default. "
            "Mirror the caller's language: Hindi, English, or Hinglish. Use masculine "
            "self-reference for the assistant voice where needed, such as bol raha hoon. "
            "Avoid long monologues; ask one question at a time."
        ),
    },
    {
        "key": "sales_callback_payload",
        "label": "What information should be captured for the sales team?",
        "help_text": "Defines the handoff summary.",
        "answer_type": QuestionAnswerType.LONG_TEXT.value,
        "required": False,
        "display_order": 12,
        "answer": (
            "Capture name confirmation, preferred location, budget, property type, buying "
            "timeline, self-use or investment intent, site visit interest, best callback "
            "time, and any objection or specific question. Interested leads should include "
            "a short summary that a human sales advisor can act on immediately."
        ),
    },
]

DEMO_LEADS = [
    {
        "name": "Aarav Mehta",
        "email": "aarav.mehta@example.com",
        "phone_number": "+12025550101",
        "area_of_interest": "Gurgaon Sector 65",
        "budget_range": "1.5-2 crore",
        "property_type": "Apartment",
        "buying_timeline": "This quarter",
    },
    {
        "name": "Nisha Kapoor",
        "email": "nisha.kapoor@example.com",
        "phone_number": "+12025550102",
        "area_of_interest": "Dwarka Expressway",
        "budget_range": "90 lakh-1.2 crore",
        "property_type": "Apartment",
        "buying_timeline": "Next 3 months",
    },
    {
        "name": "Kabir Sethi",
        "email": "kabir.sethi@example.com",
        "phone_number": "+12025550103",
        "area_of_interest": "Noida Sector 150",
        "budget_range": "1-1.4 crore",
        "property_type": "Apartment",
        "buying_timeline": "Exploring",
    },
    {
        "name": "Meera Bansal",
        "email": "meera.bansal@example.com",
        "phone_number": "+12025550104",
        "area_of_interest": "Noida Extension",
        "budget_range": "80 lakh-1 crore",
        "property_type": "Apartment",
        "buying_timeline": "Within 6 months",
    },
    {
        "name": "Rohan Malhotra",
        "email": "rohan.malhotra@example.com",
        "phone_number": "+12025550105",
        "area_of_interest": "Golf Course Extension Road",
        "budget_range": "2-3 crore",
        "property_type": "Villa",
        "buying_timeline": "Immediate",
    },
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Seed demo catalog, knowledge base, leads, and campaign data for one tenant."
    )
    parser.add_argument("--clerk-user-id", help="Tenant Clerk user id to seed for.")
    parser.add_argument("--email", help="Tenant user email to seed for.")
    parser.add_argument(
        "--tenant-id",
        help="Tenant UUID to seed. Use this when the database has multiple memberships.",
    )
    parser.add_argument(
        "--list-tenants",
        action="store_true",
        help="Print active tenant memberships and exit without seeding.",
    )
    return parser.parse_args()


def normalize_phone(value: str) -> str:
    return "+" + "".join(character for character in value if character.isdigit())


async def list_tenant_memberships(session) -> list[tuple[Tenant, User, TenantMembership]]:
    statement = (
        select(Tenant, User, TenantMembership)
        .join(TenantMembership, TenantMembership.tenant_id == Tenant.id)
        .join(User, User.id == TenantMembership.user_id)
        .where(
            Tenant.status == RecordStatus.ACTIVE.value,
            TenantMembership.status == RecordStatus.ACTIVE.value,
            User.status == RecordStatus.ACTIVE.value,
            User.realm == UserRealm.TENANT.value,
        )
        .order_by(Tenant.created_at.desc(), User.created_at.desc())
    )
    return list((await session.execute(statement)).all())


async def select_membership(session, args: argparse.Namespace) -> tuple[Tenant, User, TenantMembership]:
    rows = await list_tenant_memberships(session)
    if args.list_tenants:
        for tenant, user, membership in rows:
            print(
                f"tenant_id={tenant.id} tenant={tenant.name!r} "
                f"user={user.primary_email!r} clerk_user_id={user.clerk_user_id} "
                f"membership_id={membership.id}"
            )
        raise SystemExit(0)

    if args.tenant_id:
        rows = [row for row in rows if str(row[0].id) == args.tenant_id]
    if args.clerk_user_id:
        rows = [row for row in rows if row[1].clerk_user_id == args.clerk_user_id]
    if args.email:
        rows = [
            row
            for row in rows
            if (row[1].primary_email or "").lower() == args.email.lower()
        ]

    if not rows:
        raise SystemExit(
            "No active tenant membership matched. Run with --list-tenants to inspect options."
        )
    if len(rows) > 1:
        print("Multiple active tenant memberships found. Re-run with --tenant-id, --email, or --clerk-user-id:")
        for tenant, user, _membership in rows:
            print(
                f"  tenant_id={tenant.id} tenant={tenant.name!r} "
                f"user={user.primary_email!r} clerk_user_id={user.clerk_user_id}"
            )
        raise SystemExit(2)
    return rows[0]


async def ensure_real_estate_template(session) -> tuple[Category, CategoryTemplateVersion]:
    category = (
        await session.execute(select(Category).where(Category.key == CATEGORY_KEY))
    ).scalar_one_or_none()
    if category is None:
        category = Category(
            key=CATEGORY_KEY,
            name="Real Estate",
            description="Real estate brokerage, builders, and property sales teams.",
            status=CategoryStatus.ACTIVE.value,
        )
        session.add(category)
        await session.flush()
    else:
        category.name = "Real Estate"
        category.description = "Real estate brokerage, builders, and property sales teams."
        category.status = CategoryStatus.ACTIVE.value

    template = (
        await session.execute(
            select(CategoryTemplateVersion)
            .options(selectinload(CategoryTemplateVersion.qna_questions))
            .where(
                CategoryTemplateVersion.category_id == category.id,
                CategoryTemplateVersion.version == 1,
            )
        )
    ).scalar_one_or_none()
    if template is None:
        template = CategoryTemplateVersion(
            category_id=category.id,
            version=1,
            title=TEMPLATE_TITLE,
            description="Starter questions for a first real estate outreach assistant.",
            status=TemplateStatus.PUBLISHED.value,
            lead_schema_json=LEAD_SCHEMA,
            published_at=datetime.now(timezone.utc),
        )
        session.add(template)
        await session.flush()
    else:
        template.title = TEMPLATE_TITLE
        template.description = "Starter questions for a first real estate outreach assistant."
        template.status = TemplateStatus.PUBLISHED.value
        template.lead_schema_json = LEAD_SCHEMA
        if template.published_at is None:
            template.published_at = datetime.now(timezone.utc)

    existing_questions = {
        question.key: question
        for question in (
            await session.execute(
                select(QnaQuestion).where(QnaQuestion.category_template_version_id == template.id)
            )
        ).scalars()
    }
    for question_data in TEMPLATE_QUESTIONS:
        question = existing_questions.get(question_data["key"])
        if question is None:
            session.add(
                QnaQuestion(
                    category_template_version_id=template.id,
                    key=question_data["key"],
                    label=question_data["label"],
                    help_text=question_data["help_text"],
                    answer_type=question_data["answer_type"],
                    required=question_data["required"],
                    display_order=question_data["display_order"],
                    validation_json={},
                    options_json=None,
                )
            )
        else:
            question.label = question_data["label"]
            question.help_text = question_data["help_text"]
            question.answer_type = question_data["answer_type"]
            question.required = question_data["required"]
            question.display_order = question_data["display_order"]
            question.validation_json = {}
            question.options_json = None

    return category, template


async def ensure_published_tenant_kb(
    session,
    tenant: Tenant,
    user: User,
    category: Category,
    template: CategoryTemplateVersion,
) -> TenantKnowledgeBaseVersion:
    workspace = (
        await session.execute(
            select(TenantKnowledgeBase)
            .options(
                selectinload(TenantKnowledgeBase.versions).selectinload(
                    TenantKnowledgeBaseVersion.questions
                ),
                selectinload(TenantKnowledgeBase.active_version),
            )
            .where(TenantKnowledgeBase.tenant_id == tenant.id)
        )
    ).scalar_one_or_none()
    if workspace is None:
        workspace = TenantKnowledgeBase(tenant_id=tenant.id)
        session.add(workspace)
        await session.flush()

    active_version = workspace.active_version
    if active_version is None:
        next_version = (
            (
                await session.execute(
                    select(func.max(TenantKnowledgeBaseVersion.version)).where(
                        TenantKnowledgeBaseVersion.knowledge_base_id == workspace.id
                    )
                )
            ).scalar_one()
            or 0
        ) + 1
        active_version = TenantKnowledgeBaseVersion(
            knowledge_base_id=workspace.id,
            tenant_id=tenant.id,
            category_id=category.id,
            source_template_version_id=template.id,
            version=next_version,
            title=f"{tenant.name} Real Estate Knowledge",
            business_profile_json={
                "business_name": tenant.name,
                "business_summary": TEMPLATE_QUESTIONS[0]["answer"],
            },
            additional_notes=(
                "Begin calls with Namaste! Kaise hain aap? Introduce yourself as "
                f"{tenant.name} ka assistant from RingIQ. Keep the first call concise, "
                "polite, and focused on whether the person wants a human callback."
            ),
            status=TemplateStatus.PUBLISHED.value,
            published_at=datetime.now(timezone.utc),
            published_by_user_id=user.id,
            created_by_user_id=user.id,
            updated_by_user_id=user.id,
        )
        session.add(active_version)
        await session.flush()
        workspace.active_version_id = active_version.id
    else:
        active_version.category_id = category.id
        active_version.source_template_version_id = template.id
        active_version.title = f"{tenant.name} Real Estate Knowledge"
        active_version.business_profile_json = {
            "business_name": tenant.name,
            "business_summary": TEMPLATE_QUESTIONS[0]["answer"],
        }
        active_version.additional_notes = (
            "Begin calls with Namaste! Kaise hain aap? Introduce yourself as "
            f"{tenant.name} ka assistant from RingIQ. Keep the first call concise, "
            "polite, and focused on whether the person wants a human callback."
        )
        active_version.status = TemplateStatus.PUBLISHED.value
        active_version.updated_by_user_id = user.id
        if active_version.published_at is None:
            active_version.published_at = datetime.now(timezone.utc)
        workspace.active_version_id = active_version.id

    existing_questions = {
        question.key: question
        for question in (
            await session.execute(
                select(TenantKnowledgeQuestion).where(
                    TenantKnowledgeQuestion.tenant_knowledge_base_version_id == active_version.id
                )
            )
        ).scalars()
    }
    for question_data in TEMPLATE_QUESTIONS:
        answer = question_data["answer"]
        if isinstance(answer, str):
            answer = answer.replace(DEMO_BUSINESS_NAME_TOKEN, tenant.name)
        question = existing_questions.get(question_data["key"])
        if question is None:
            session.add(
                TenantKnowledgeQuestion(
                    tenant_knowledge_base_version_id=active_version.id,
                    key=question_data["key"],
                    label=question_data["label"],
                    help_text=question_data["help_text"],
                    answer_type=question_data["answer_type"],
                    required=question_data["required"],
                    display_order=question_data["display_order"],
                    validation_json={},
                    options_json=None,
                    answer_value_json=answer,
                )
            )
        else:
            question.label = question_data["label"]
            question.help_text = question_data["help_text"]
            question.answer_type = question_data["answer_type"]
            question.required = question_data["required"]
            question.display_order = question_data["display_order"]
            question.validation_json = {}
            question.options_json = None
            question.answer_value_json = answer

    tenant.primary_category_id = category.id
    return active_version


async def ensure_demo_leads(session, tenant: Tenant, user: User) -> tuple[LeadImport, list[Lead]]:
    lead_import = (
        await session.execute(
            select(LeadImport).where(
                LeadImport.tenant_id == tenant.id,
                LeadImport.filename == DEMO_IMPORT_FILENAME,
            )
        )
    ).scalar_one_or_none()
    if lead_import is None:
        lead_import = LeadImport(
            tenant_id=tenant.id,
            filename=DEMO_IMPORT_FILENAME,
            total_rows=len(DEMO_LEADS),
            imported_rows=0,
            invalid_rows=0,
            duplicate_rows=0,
            column_mapping_json={
                "name": "name",
                "email": "email",
                "phone_number": "phone_number",
            },
            created_by_user_id=user.id,
        )
        session.add(lead_import)
        await session.flush()

    leads: list[Lead] = []
    for index, lead_data in enumerate(DEMO_LEADS, start=2):
        normalized_phone = normalize_phone(lead_data["phone_number"])
        lead = (
            await session.execute(
                select(Lead).where(
                    Lead.tenant_id == tenant.id,
                    Lead.normalized_phone_number == normalized_phone,
                )
            )
        ).scalar_one_or_none()
        attributes = {
            key: value
            for key, value in lead_data.items()
            if key not in {"name", "email", "phone_number"}
        }
        if lead is None:
            lead = Lead(
                tenant_id=tenant.id,
                name=lead_data["name"],
                email=lead_data["email"],
                phone_number=lead_data["phone_number"],
                normalized_phone_number=normalized_phone,
                attributes_json=attributes,
                created_by_user_id=user.id,
                updated_by_user_id=user.id,
            )
            session.add(lead)
            await session.flush()
        else:
            lead.name = lead_data["name"]
            lead.email = lead_data["email"]
            lead.phone_number = lead_data["phone_number"]
            lead.attributes_json = attributes
            lead.updated_by_user_id = user.id
        leads.append(lead)

        existing_row = (
            await session.execute(
                select(LeadImportRow).where(
                    LeadImportRow.lead_import_id == lead_import.id,
                    LeadImportRow.row_number == index,
                )
            )
        ).scalar_one_or_none()
        if existing_row is None:
            session.add(
                LeadImportRow(
                    tenant_id=tenant.id,
                    lead_import_id=lead_import.id,
                    lead_id=lead.id,
                    row_number=index,
                    status=LeadImportRowStatus.IMPORTED.value,
                    raw_data_json=lead_data,
                )
            )
        else:
            existing_row.lead_id = lead.id
            existing_row.status = LeadImportRowStatus.IMPORTED.value
            existing_row.error_code = None
            existing_row.error_message = None
            existing_row.raw_data_json = lead_data

    lead_import.total_rows = len(DEMO_LEADS)
    lead_import.imported_rows = len(DEMO_LEADS)
    lead_import.invalid_rows = 0
    lead_import.duplicate_rows = 0
    return lead_import, leads


async def ensure_demo_campaign(
    session,
    tenant: Tenant,
    user: User,
    lead_import: LeadImport,
    leads: list[Lead],
    knowledge_base_version: TenantKnowledgeBaseVersion,
) -> Campaign:
    campaign = (
        await session.execute(
            select(Campaign)
            .options(selectinload(Campaign.enrollments))
            .where(Campaign.tenant_id == tenant.id, Campaign.name == DEMO_CAMPAIGN_NAME)
        )
    ).scalar_one_or_none()
    if campaign is None:
        campaign = Campaign(
            tenant_id=tenant.id,
            name=DEMO_CAMPAIGN_NAME,
            status=CampaignStatus.DRAFT.value,
            source_import_id=lead_import.id,
            knowledge_base_version_id=knowledge_base_version.id,
            retry_limit=3,
            retry_policy_json={"delay_minutes": 15},
            created_by_user_id=user.id,
            updated_by_user_id=user.id,
        )
        session.add(campaign)
        await session.flush()
    else:
        campaign.status = CampaignStatus.DRAFT.value
        campaign.source_import_id = lead_import.id
        campaign.knowledge_base_version_id = knowledge_base_version.id
        campaign.retry_limit = 3
        campaign.retry_policy_json = {"delay_minutes": 15}
        campaign.updated_by_user_id = user.id

    existing_lead_ids = {
        enrollment.lead_id
        for enrollment in (
            await session.execute(
                select(CampaignEnrollment).where(CampaignEnrollment.campaign_id == campaign.id)
            )
        ).scalars()
    }
    for lead in leads:
        if lead.id not in existing_lead_ids:
            session.add(
                CampaignEnrollment(
                    tenant_id=tenant.id,
                    campaign_id=campaign.id,
                    lead_id=lead.id,
                )
            )
    return campaign


async def seed_demo_data(args: argparse.Namespace) -> None:
    session_factory = get_session_factory()
    async with session_factory() as session:
        tenant, user, _membership = await select_membership(session, args)
        category, template = await ensure_real_estate_template(session)
        knowledge_base_version = await ensure_published_tenant_kb(
            session,
            tenant,
            user,
            category,
            template,
        )
        lead_import, leads = await ensure_demo_leads(session, tenant, user)
        campaign = await ensure_demo_campaign(
            session,
            tenant,
            user,
            lead_import,
            leads,
            knowledge_base_version,
        )
        await session.commit()

        print("Seeded demo tenant data.")
        print(f"Tenant: {tenant.name} ({tenant.id})")
        print(f"Tenant user: {user.primary_email} ({user.clerk_user_id})")
        print(f"Category: {category.name} ({category.id})")
        print(f"Knowledge base version: {knowledge_base_version.id}")
        print(f"Lead import: {lead_import.id}")
        print(f"Leads: {len(leads)}")
        print(f"Campaign: {campaign.name} ({campaign.id})")


async def main() -> None:
    try:
        await seed_demo_data(parse_args())
    finally:
        await dispose_database()


if __name__ == "__main__":
    asyncio.run(main())
