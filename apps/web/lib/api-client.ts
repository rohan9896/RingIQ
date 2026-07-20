const apiBaseUrl =
  process.env.NEXT_PUBLIC_API_BASE_URL?.replace(/\/$/, "") ??
  "http://127.0.0.1:8000";

export type BackendIdentity = {
  tenant: {
    id: string;
    clerk_organization_id: string;
    name: string;
    slug: string | null;
  };
  user: {
    id: string;
    clerk_user_id: string;
    email: string;
    first_name: string | null;
    last_name: string | null;
  };
  membership: {
    id: string;
    role: string;
    status: string;
  };
};

export type TenantBootstrap = {
  tenant_id: string;
  user_id: string;
  membership_id: string;
  clerk_organization_id: string;
  clerk_user_id: string;
  clerk_membership_id: string;
  tenant_name: string;
  tenant_slug: string;
  timezone: string;
};

export async function fetchBackendIdentity(token: string) {
  const response = await fetch(`${apiBaseUrl}/v1/me`, {
    headers: {
      Authorization: `Bearer ${token}`,
    },
  });

  if (!response.ok) {
    const body = await response.json().catch(() => null);
    const detail =
      typeof body?.detail === "string"
        ? body.detail
        : `Backend returned ${response.status}`;
    throw new Error(detail);
  }

  return (await response.json()) as BackendIdentity;
}

export async function bootstrapTenantMembership(
  token: string,
  signal?: AbortSignal,
) {
  const response = await fetch(`${apiBaseUrl}/v1/onboarding/bootstrap`, {
    method: "POST",
    headers: {
      Authorization: `Bearer ${token}`,
    },
    signal,
  });

  if (!response.ok) {
    const body = await response.json().catch(() => null);
    const detail =
      typeof body?.detail === "string"
        ? body.detail
        : `Backend returned ${response.status}`;
    throw new Error(detail);
  }

  return (await response.json()) as TenantBootstrap;
}

export type PlatformRole =
  | "platform_super_admin"
  | "platform_operations"
  | "template_manager";

export type PlatformIdentity = {
  user_id: string;
  clerk_user_id: string;
  primary_email: string | null;
  display_name: string | null;
  role: PlatformRole;
};

export type PlatformOverview = {
  counts: {
    organizations: number;
    active_organizations: number;
    suspended_organizations: number;
    tenant_users: number;
    platform_users: number;
    categories: number;
    active_categories: number;
    draft_templates: number;
    published_templates: number;
  };
  first_template_seeded: boolean;
};

export async function fetchPlatformIdentity(token: string) {
  const response = await fetch(`${apiBaseUrl}/v1/platform/me`, {
    headers: {
      Authorization: `Bearer ${token}`,
    },
  });

  if (!response.ok) {
    const body = await response.json().catch(() => null);
    const detail =
      typeof body?.detail === "string"
        ? body.detail
        : `Backend returned ${response.status}`;
    throw new Error(detail);
  }

  return (await response.json()) as PlatformIdentity;
}

export type CategoryStatus = "active" | "inactive";
export type TemplateStatus = "draft" | "published" | "archived";
export type QuestionAnswerType =
  | "short_text"
  | "long_text"
  | "number"
  | "boolean"
  | "single_select"
  | "multi_select"
  | "date";

export type PlatformCategory = {
  id: string;
  key: string;
  name: string;
  description: string | null;
  status: CategoryStatus;
  created_at: string;
  updated_at: string;
};

export type TemplateQuestion = {
  id: string;
  key: string;
  label: string;
  help_text: string | null;
  answer_type: QuestionAnswerType;
  required: boolean;
  display_order: number;
  validation_json: Record<string, unknown>;
  options_json: unknown[] | null;
  created_at: string;
  updated_at: string;
};

export type TemplateQuestionInput = Omit<TemplateQuestion, "id" | "created_at" | "updated_at">;

export type PlatformTemplateVersion = {
  id: string;
  category_id: string;
  version: number;
  title: string;
  description: string | null;
  status: TemplateStatus;
  lead_schema_json: Record<string, unknown>;
  published_at: string | null;
  published_by_user_id: string | null;
  created_at: string;
  updated_at: string;
  qna_questions: TemplateQuestion[];
};

async function platformRequest<T>(token: string, path: string, options?: RequestInit): Promise<T> {
  const response = await fetch(`${apiBaseUrl}/v1/platform${path}`, {
    ...options,
    headers: {
      Authorization: `Bearer ${token}`,
      "Content-Type": "application/json",
      ...options?.headers,
    },
  });

  if (!response.ok) {
    const body = await response.json().catch(() => null);
    const detail = typeof body?.detail === "string" ? body.detail : `Backend returned ${response.status}`;
    throw new Error(detail);
  }

  return (await response.json()) as T;
}

export function fetchPlatformCategories(token: string) {
  return platformRequest<PlatformCategory[]>(token, "/categories");
}

export function fetchPlatformOverview(token: string) {
  return platformRequest<PlatformOverview>(token, "/overview");
}

export function seedRealEstateStarterTemplate(token: string) {
  return platformRequest<{
    category: PlatformCategory;
    template_version: PlatformTemplateVersion;
    created_category: boolean;
    created_template: boolean;
  }>(token, "/starter-template-seeds/real-estate", {
    method: "POST",
  });
}

export function createPlatformCategory(
  token: string,
  payload: Pick<PlatformCategory, "key" | "name" | "description" | "status">,
) {
  return platformRequest<PlatformCategory>(token, "/categories", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function updatePlatformCategory(
  token: string,
  categoryId: string,
  payload: Partial<Pick<PlatformCategory, "name" | "description" | "status">>,
) {
  return platformRequest<PlatformCategory>(token, `/categories/${categoryId}`, {
    method: "PATCH",
    body: JSON.stringify(payload),
  });
}

export function fetchCategoryTemplateVersions(token: string, categoryId: string) {
  return platformRequest<PlatformTemplateVersion[]>(token, `/categories/${categoryId}/template-versions`);
}

export function createCategoryTemplateVersion(
  token: string,
  categoryId: string,
  payload: Pick<PlatformTemplateVersion, "title" | "description" | "lead_schema_json"> & {
    qna_questions: TemplateQuestionInput[];
  },
) {
  return platformRequest<PlatformTemplateVersion>(token, `/categories/${categoryId}/template-versions`, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function updateCategoryTemplateVersion(
  token: string,
  templateVersionId: string,
  payload: Partial<Pick<PlatformTemplateVersion, "title" | "description" | "lead_schema_json">>,
) {
  return platformRequest<PlatformTemplateVersion>(token, `/template-versions/${templateVersionId}`, {
    method: "PATCH",
    body: JSON.stringify(payload),
  });
}

export function replaceTemplateQuestions(
  token: string,
  templateVersionId: string,
  qnaQuestions: TemplateQuestionInput[],
) {
  return platformRequest<PlatformTemplateVersion>(token, `/template-versions/${templateVersionId}/questions`, {
    method: "PUT",
    body: JSON.stringify({ qna_questions: qnaQuestions }),
  });
}

export function publishCategoryTemplateVersion(token: string, templateVersionId: string) {
  return platformRequest<PlatformTemplateVersion>(token, `/template-versions/${templateVersionId}/publish`, {
    method: "POST",
  });
}

export type StarterTemplate = {
  id: string;
  category_id: string;
  category_key: string;
  category_name: string;
  title: string;
  description: string | null;
  lead_schema_json: Record<string, unknown>;
  qna_questions: Omit<TemplateQuestion, "created_at" | "updated_at">[];
};

export type TenantKnowledgeQuestion = TemplateQuestion & {
  answer_value_json: unknown | null;
};

export type TenantKnowledgeVersion = {
  id: string;
  knowledge_base_id: string;
  tenant_id: string;
  category_id: string | null;
  source_template_version_id: string | null;
  version: number;
  title: string;
  business_profile_json: Record<string, unknown>;
  additional_notes: string | null;
  status: TemplateStatus;
  published_at: string | null;
  created_at: string;
  updated_at: string;
  questions: TenantKnowledgeQuestion[];
};

export type TenantKnowledgeBase = {
  id: string;
  tenant_id: string;
  active_version: TenantKnowledgeVersion | null;
  draft_version: TenantKnowledgeVersion | null;
};

async function tenantRequest<T>(token: string, path: string, options?: RequestInit): Promise<T> {
  const response = await fetch(`${apiBaseUrl}/v1/knowledge-base${path}`, {
    ...options,
    headers: {
      Authorization: `Bearer ${token}`,
      "Content-Type": "application/json",
      ...options?.headers,
    },
  });

  if (!response.ok) {
    const body = await response.json().catch(() => null);
    const detail = typeof body?.detail === "string" ? body.detail : body?.detail ?? `Backend returned ${response.status}`;
    throw new Error(typeof detail === "string" ? detail : JSON.stringify(detail));
  }
  return (await response.json()) as T;
}

export function fetchStarterTemplates(token: string) {
  return tenantRequest<StarterTemplate[]>(token, "/starter-templates");
}

export function fetchTenantKnowledgeBase(token: string) {
  return tenantRequest<TenantKnowledgeBase | null>(token, "");
}

export function createTenantKnowledgeDraft(token: string, starterTemplateVersionId?: string) {
  return tenantRequest<TenantKnowledgeVersion>(token, "/drafts", {
    method: "POST",
    body: JSON.stringify({ starter_template_version_id: starterTemplateVersionId ?? null }),
  });
}

export function updateTenantKnowledgeDraft(
  token: string,
  versionId: string,
  payload: Pick<TenantKnowledgeVersion, "title" | "business_profile_json" | "additional_notes">,
) {
  return tenantRequest<TenantKnowledgeVersion>(token, `/drafts/${versionId}`, {
    method: "PATCH",
    body: JSON.stringify(payload),
  });
}

export function replaceTenantKnowledgeQuestions(
  token: string,
  versionId: string,
  questions: Array<Omit<TenantKnowledgeQuestion, "id" | "created_at" | "updated_at">>,
) {
  return tenantRequest<TenantKnowledgeVersion>(token, `/drafts/${versionId}/questions`, {
    method: "PUT",
    body: JSON.stringify({ questions }),
  });
}

export function publishTenantKnowledgeDraft(token: string, versionId: string) {
  return tenantRequest<TenantKnowledgeVersion>(token, `/drafts/${versionId}/publish`, { method: "POST" });
}

export type Lead = {
  id: string;
  name: string;
  email: string;
  phone_number: string;
  normalized_phone_number: string;
  attributes_json: Record<string, unknown>;
  status: "active" | "archived";
  manual_status: "new" | "in_progress" | "follow_up" | "closed";
  archived_at: string | null;
  created_at: string;
  updated_at: string;
};

export type LeadImportRow = {
  id: string;
  lead_id: string | null;
  row_number: number;
  status: "imported" | "invalid" | "duplicate";
  error_code: string | null;
  error_message: string | null;
  raw_data_json: Record<string, unknown>;
  created_at: string;
};

export type LeadImport = {
  id: string;
  filename: string;
  status: "completed";
  total_rows: number;
  imported_rows: number;
  invalid_rows: number;
  duplicate_rows: number;
  column_mapping_json: Record<string, string>;
  created_at: string;
};

export type LeadImportDetail = LeadImport & { rows: LeadImportRow[] };

async function leadsRequest<T>(token: string, path: string, options?: RequestInit): Promise<T> {
  const response = await fetch(`${apiBaseUrl}/v1${path}`, {
    ...options,
    headers: { Authorization: `Bearer ${token}`, "Content-Type": "application/json", ...options?.headers },
  });
  if (!response.ok) {
    const body = await response.json().catch(() => null);
    const detail = typeof body?.detail === "string" ? body.detail : body?.detail ?? `Backend returned ${response.status}`;
    throw new Error(typeof detail === "string" ? detail : JSON.stringify(detail));
  }
  return (await response.json()) as T;
}

export function fetchLeads(token: string, query?: string, includeArchived = false) {
  const params = new URLSearchParams();
  if (query?.trim()) params.set("query", query.trim());
  if (includeArchived) params.set("include_archived", "true");
  const search = params.size ? `?${params.toString()}` : "";
  return leadsRequest<Lead[]>(token, `/leads${search}`);
}

export function createLead(
  token: string,
  payload: Pick<Lead, "name" | "email" | "phone_number" | "attributes_json">,
) {
  return leadsRequest<Lead>(token, "/leads", { method: "POST", body: JSON.stringify(payload) });
}

export function fetchLeadImports(token: string) {
  return leadsRequest<LeadImport[]>(token, "/lead-imports");
}

export function createLeadImport(
  token: string,
  payload: { filename: string; csv_content: string; column_mapping: Record<string, string> },
) {
  return leadsRequest<LeadImportDetail>(token, "/lead-imports", { method: "POST", body: JSON.stringify(payload) });
}

export function fetchLeadImport(token: string, importId: string) {
  return leadsRequest<LeadImportDetail>(token, `/lead-imports/${importId}`);
}

export function fetchLead(token: string, leadId: string) {
  return leadsRequest<Lead>(token, `/leads/${leadId}`);
}

export function updateLead(
  token: string,
  leadId: string,
  payload: Partial<Pick<Lead, "name" | "email" | "phone_number" | "attributes_json" | "manual_status">>,
) {
  return leadsRequest<Lead>(token, `/leads/${leadId}`, {
    method: "PATCH",
    body: JSON.stringify(payload),
  });
}

export function archiveLead(token: string, leadId: string) {
  return leadsRequest<Lead>(token, `/leads/${leadId}/archive`, { method: "POST" });
}

export function restoreLead(token: string, leadId: string) {
  return leadsRequest<Lead>(token, `/leads/${leadId}/restore`, { method: "POST" });
}

export type CampaignStatus =
  | "draft"
  | "ready"
  | "running"
  | "paused"
  | "completed"
  | "cancelled"
  | "failed";

export type EnrollmentStatus =
  | "pending"
  | "queued"
  | "calling"
  | "connected"
  | "retry_scheduled"
  | "completed"
  | "invalid_number"
  | "exhausted"
  | "cancelled";

export type CallAttempt = {
  id: string;
  attempt_number: number;
  status: string;
  scheduled_at: string;
  started_at: string | null;
  answered_at: string | null;
  ended_at: string | null;
  duration_seconds: number | null;
  provider: string | null;
  provider_call_id: string | null;
  livekit_room_name: string | null;
  failure_code: string | null;
  failure_detail: string | null;
  terminal_reason: string | null;
  artifacts_finalized_at: string | null;
  outcome: PostCallOutcome | null;
};

export type TranscriptTurn = {
  role: "user" | "assistant";
  text: string;
  interrupted: boolean;
};

export type OutcomeLabel =
  | "hot"
  | "warm"
  | "cold"
  | "callback_requested"
  | "not_interested"
  | "unanswered"
  | "invalid_number"
  | "needs_review";

export type PostCallOutcome = {
  id: string;
  processing_status: "pending" | "processing" | "completed" | "failed";
  processing_error: string | null;
  processed_at: string | null;
  label: OutcomeLabel | null;
  confidence: number | null;
  rationale: string | null;
  summary: string | null;
  qualification_facts: {
    area: string | null;
    budget: string | null;
    property_type: string | null;
    intent: string | null;
    timeline: string | null;
  };
  evidence: Array<{ turn_index: number; speaker: "user" | "assistant"; quote: string }>;
  callback_original_phrase: string | null;
  callback_timezone: string | null;
  callback_at: string | null;
  terminal_reason: string | null;
};

export type CallActivity = {
  id: string;
  lead_id: string;
  lead_name: string;
  lead_phone_number: string;
  campaign_id: string;
  campaign_name: string;
  attempt_number: number;
  status: string;
  started_at: string | null;
  answered_at: string | null;
  ended_at: string | null;
  duration_seconds: number | null;
  transcript: TranscriptTurn[];
  recording_status: string | null;
  recording_url: string | null;
  terminal_reason: string | null;
  outcome: PostCallOutcome | null;
};

export function fetchCalls(token: string) {
  return leadsRequest<CallActivity[]>(token, "/calls");
}

export type CampaignProgress = Record<EnrollmentStatus, number> & { total: number };

export type CampaignKnowledgeBase = {
  id: string;
  title: string;
  version: number;
  status: string;
  category_id: string | null;
  is_pinned: boolean;
};

export type Campaign = {
  id: string;
  name: string;
  status: CampaignStatus;
  source_import_id: string | null;
  knowledge_base_version_id: string | null;
  knowledge_base: CampaignKnowledgeBase | null;
  retry_limit: number;
  retry_policy_json: Record<string, unknown>;
  started_at: string | null;
  completed_at: string | null;
  created_at: string;
  updated_at: string;
  readiness: { is_ready: boolean; blockers: string[] };
  progress: CampaignProgress;
};

export type CampaignEnrollment = {
  id: string;
  lead_id: string;
  lead_name: string;
  lead_email: string;
  lead_phone_number: string;
  status: EnrollmentStatus;
  attempt_count: number;
  next_attempt_at: string | null;
  last_error_code: string | null;
  attempts: CallAttempt[];
};

export type CampaignDetail = Campaign & { enrollments: CampaignEnrollment[] };

export type LeadCampaignHistory = {
  campaign_id: string;
  campaign_name: string;
  campaign_status: CampaignStatus;
  enrollment_id: string;
  enrollment_status: EnrollmentStatus;
  attempt_count: number;
  attempts: CallAttempt[];
};

export function fetchCampaigns(token: string) {
  return leadsRequest<Campaign[]>(token, "/campaigns");
}

export function fetchCampaign(token: string, campaignId: string) {
  return leadsRequest<CampaignDetail>(token, `/campaigns/${campaignId}`);
}

export function createCampaign(
  token: string,
  payload: { name: string; lead_ids: string[]; retry_limit?: number; source_import_id?: string | null },
) {
  return leadsRequest<CampaignDetail>(token, "/campaigns", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function changeCampaignState(
  token: string,
  campaignId: string,
  action: "start" | "pause" | "resume" | "cancel",
) {
  return leadsRequest<CampaignDetail>(token, `/campaigns/${campaignId}/${action}`, {
    method: "POST",
  });
}

export function fetchLeadCampaignHistory(token: string, leadId: string) {
  return leadsRequest<LeadCampaignHistory[]>(token, `/leads/${leadId}/campaign-history`);
}

export function callLeadNow(token: string, leadId: string) {
  return leadsRequest<CampaignDetail>(token, `/leads/${leadId}/call-now`, { method: "POST" });
}

export type WorkspaceCategory = { id: string; key: string; name: string };
export type Workspace = {
  tenant_id: string;
  name: string;
  timezone: string;
  category: WorkspaceCategory | null;
  has_active_knowledge_base: boolean;
  is_call_ready: boolean;
  readiness_blockers: string[];
};
export type DashboardData = {
  workspace: Workspace;
  totals: {
    leads: number;
    campaigns: number;
    call_attempts: number;
    connected: number;
    completed: number;
    failed: number;
  };
  recent_calls: Array<{
    attempt_id: string;
    lead_id: string;
    lead_name: string;
    campaign_id: string;
    campaign_name: string;
    status: string;
    started_at: string | null;
    ended_at: string | null;
    duration_seconds: number | null;
    failure_code: string | null;
    failure_detail: string | null;
  }>;
};

export function fetchWorkspace(token: string) {
  return leadsRequest<Workspace>(token, "/workspace");
}

export function fetchWorkspaceCategories(token: string) {
  return leadsRequest<WorkspaceCategory[]>(token, "/workspace/categories");
}

export function updateWorkspaceCategory(token: string, primaryCategoryId: string) {
  return leadsRequest<Workspace>(token, "/workspace", {
    method: "PATCH",
    body: JSON.stringify({ primary_category_id: primaryCategoryId }),
  });
}

export function fetchDashboard(token: string) {
  return leadsRequest<DashboardData>(token, "/dashboard");
}
