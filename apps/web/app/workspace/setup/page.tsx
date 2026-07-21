import { redirect } from "next/navigation";
import { WorkspaceSetup } from "@/components/workspace-setup";
import { resolveAuthenticatedDestination } from "@/lib/server-post-auth-destination";

export default async function WorkspaceSetupPage() {
  const destination = await resolveAuthenticatedDestination();
  if (!destination) redirect("/sign-in");
  if (destination !== "/workspace/setup") redirect(destination);

  return <WorkspaceSetup />;
}
