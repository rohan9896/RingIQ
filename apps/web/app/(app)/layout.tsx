import { auth } from "@clerk/nextjs/server";
import { redirect } from "next/navigation";
import { AppShell } from "@/components/app-shell";
import { TenantProvisioningGate } from "@/components/tenant-provisioning-gate";

export default async function ProtectedAppLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  const { userId, orgId } = await auth();

  if (!userId) {
    redirect("/sign-in");
  }

  if (!orgId) {
    redirect("/workspace/setup");
  }

  return (
    <TenantProvisioningGate>
      <AppShell>{children}</AppShell>
    </TenantProvisioningGate>
  );
}
