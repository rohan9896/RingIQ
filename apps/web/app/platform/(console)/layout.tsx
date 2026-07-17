import { auth } from "@clerk/nextjs/server";
import { redirect } from "next/navigation";
import { PlatformShell } from "@/components/platform/platform-shell";

export default async function PlatformLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  const { userId, orgId } = await auth();

  if (!userId) redirect("/platform/sign-in");
  if (orgId) redirect("/dashboard");

  return <PlatformShell>{children}</PlatformShell>;
}
