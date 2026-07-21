import { fetchPlatformIdentity } from "./api-client.ts";
import { tenantPostAuthDestination } from "./clerk-navigation.ts";

export type PostAuthSession = {
  currentTask?: { key: string } | null;
  getToken: () => Promise<string | null>;
};

type PlatformIdentityLookup = (
  token: string,
) => Promise<{ role: string } | unknown>;

export async function resolvePostAuthDestination(
  session: PostAuthSession,
  tenantDestination = "/dashboard",
  lookupPlatformIdentity: PlatformIdentityLookup = fetchPlatformIdentity,
) {
  const token = await session.getToken();
  if (!token) throw new Error("No active session token is available.");

  try {
    await lookupPlatformIdentity(token);
    return "/platform";
  } catch (caught) {
    const detail = caught instanceof Error ? caught.message : "";
    if (detail === "platform_identity_has_active_organization") {
      return tenantDestination;
    }
    if (detail === "platform_access_not_provisioned") {
      return tenantPostAuthDestination(
        session.currentTask?.key,
        "/workspace/setup",
      );
    }
    if (detail === "platform_identity_inactive") {
      return "/platform";
    }
    throw caught;
  }
}
