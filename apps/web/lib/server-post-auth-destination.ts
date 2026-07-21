import "server-only";

import { auth } from "@clerk/nextjs/server";
import { resolvePostAuthDestination } from "@/lib/post-auth-destination";

export async function resolveAuthenticatedDestination(): Promise<
  "/dashboard" | "/platform" | "/workspace/setup" | null
> {
  const { userId, orgId, getToken } = await auth();

  if (!userId) return null;
  if (orgId) return "/dashboard" as const;

  return (await resolvePostAuthDestination({ getToken })) as
    | "/dashboard"
    | "/platform"
    | "/workspace/setup";
}
