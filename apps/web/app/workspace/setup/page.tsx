import { auth } from "@clerk/nextjs/server";
import { redirect } from "next/navigation";
import { WorkspaceSetup } from "@/components/workspace-setup";

export default async function WorkspaceSetupPage() {
  const { orgId } = await auth();

  if (orgId) {
    redirect("/dashboard");
  }

  return <WorkspaceSetup />;
}
