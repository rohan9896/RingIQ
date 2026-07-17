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
