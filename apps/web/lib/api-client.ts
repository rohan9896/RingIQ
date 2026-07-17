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
