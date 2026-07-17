"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import {
  Activity,
  Building2,
  FileQuestion,
  LayoutDashboard,
  Loader2,
  LogOut,
  Shield,
  ShieldAlert,
  Users,
} from "lucide-react";
import { useAuth, useClerk, useUser } from "@clerk/nextjs";
import { BrandMark } from "@/components/brand-mark";
import {
  fetchPlatformIdentity,
  type PlatformIdentity,
  type PlatformRole,
} from "@/lib/api-client";

type PlatformShellProps = { children: React.ReactNode };

const roleLabels: Record<PlatformRole, string> = {
  platform_super_admin: "Super admin",
  platform_operations: "Operations",
  template_manager: "Template manager",
};

type PlatformNavigationItem = {
  label: string;
  href: "/platform";
  icon: typeof LayoutDashboard;
  roles: readonly PlatformRole[] | null;
};

const navigation: PlatformNavigationItem[] = [
  { label: "Overview", href: "/platform", icon: LayoutDashboard, roles: null },
  { label: "Organizations", href: "/platform", icon: Building2, roles: ["platform_super_admin", "platform_operations"] },
  { label: "Org users", href: "/platform", icon: Users, roles: ["platform_super_admin", "platform_operations"] },
  { label: "Platform users", href: "/platform", icon: Shield, roles: ["platform_super_admin"] },
  { label: "Starter templates", href: "/platform", icon: FileQuestion, roles: ["platform_super_admin", "template_manager"] },
  { label: "Service health", href: "/platform", icon: Activity, roles: ["platform_super_admin", "platform_operations"] },
];

export function PlatformShell({ children }: PlatformShellProps) {
  const pathname = usePathname();
  const router = useRouter();
  const { getToken } = useAuth();
  const { signOut } = useClerk();
  const { user } = useUser();
  const [identity, setIdentity] = useState<PlatformIdentity | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;

    async function resolvePlatformAccess() {
      try {
        const token = await getToken();
        if (!token) throw new Error("unauthorized");
        const result = await fetchPlatformIdentity(token);
        if (!cancelled) setIdentity(result);
      } catch (caught) {
        const detail = caught instanceof Error ? caught.message : "platform_access_failed";
        if (cancelled) return;
        if (detail === "platform_identity_has_active_organization") {
          router.replace("/dashboard");
          return;
        }
        if (detail === "platform_access_not_provisioned" || detail === "unauthorized") {
          await signOut({ redirectUrl: "/sign-in" });
          return;
        }
        setError(detail);
      }
    }

    void resolvePlatformAccess();
    return () => { cancelled = true; };
  }, [getToken, router, signOut]);

  if (error) {
    return (
      <main className="paper-grid flex min-h-screen items-center justify-center bg-[#f7f6f2] p-5">
        <section className="w-full max-w-lg border border-[#171714] bg-[#fffefa] p-7">
          <ShieldAlert className="size-6 text-[#d73a2f]" aria-hidden />
          <h1 className="mt-5 text-2xl font-black">Platform access unavailable</h1>
          <p className="mt-3 text-sm leading-6 text-[#6d6b64]">{error}</p>
          <button className="mt-6 h-11 bg-[#171714] px-4 text-sm font-bold text-white" onClick={() => window.location.reload()} type="button">
            Try again
          </button>
        </section>
      </main>
    );
  }

  if (!identity) {
    return (
      <main className="flex min-h-screen items-center justify-center bg-[#f7f6f2] text-[#4e4c46]">
        <Loader2 className="mr-3 size-5 animate-spin" aria-hidden />
        <span className="text-sm font-bold">Verifying platform access</span>
      </main>
    );
  }

  const visibleNavigation = navigation.filter(
    (item) => item.roles === null || item.roles.includes(identity.role),
  );

  return (
    <div className="min-h-screen bg-[#f7f6f2]">
      <aside className="fixed inset-y-0 left-0 hidden w-64 border-r border-[#171714] bg-[#fffefa] lg:block">
        <div className="flex h-full flex-col">
          <div className="border-b border-[#171714] p-5"><BrandMark /></div>
          <div className="border-b border-[#d8d5cc] px-5 py-4">
            <p className="utility-label !text-[#d73a2f]">Platform console</p>
            <p className="mt-2 text-sm font-bold">{roleLabels[identity.role]}</p>
          </div>
          <nav className="flex-1 space-y-1 p-3" aria-label="Platform navigation">
            {visibleNavigation.map((item, index) => {
              const active = index === 0 && pathname === item.href;
              return (
                <Link className={`flex h-10 items-center gap-3 px-3 text-sm font-bold ${active ? "bg-[#171714] text-white" : "text-[#4e4c46] hover:bg-[#f0eee8]"}`} href={item.href} key={item.label}>
                  <item.icon className="size-4" aria-hidden />
                  {item.label}
                </Link>
              );
            })}
          </nav>
          <div className="border-t border-[#171714] p-4">
            <p className="truncate px-3 text-sm font-bold">{identity.display_name ?? user?.fullName ?? identity.primary_email}</p>
            <button className="mt-3 flex h-10 w-full items-center gap-3 px-3 text-sm font-bold text-[#4e4c46] hover:bg-[#f0eee8]" onClick={() => signOut({ redirectUrl: "/platform/sign-in" })} type="button">
              <LogOut className="size-4" aria-hidden /> Sign out
            </button>
          </div>
        </div>
      </aside>
      <div className="lg:pl-64">
        <header className="sticky top-0 z-10 flex h-16 items-center justify-between border-b border-[#171714] bg-[#fffefa]/95 px-5 backdrop-blur lg:px-8">
          <div className="lg:hidden"><BrandMark /></div>
          <p className="hidden text-sm font-bold text-[#4e4c46] lg:block">RingIQ platform / {roleLabels[identity.role]}</p>
          <button className="inline-flex size-10 items-center justify-center border border-[#d8d5cc] lg:hidden" onClick={() => signOut({ redirectUrl: "/platform/sign-in" })} title="Sign out" type="button">
            <LogOut className="size-4" aria-hidden /><span className="sr-only">Sign out</span>
          </button>
        </header>
        <main className="px-5 py-7 lg:px-8 lg:py-9">{children}</main>
      </div>
    </div>
  );
}
