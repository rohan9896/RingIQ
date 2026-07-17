"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { BookOpenText, LayoutDashboard, LogOut, PhoneCall, Settings, UploadCloud } from "lucide-react";
import { useClerk, useOrganization, useUser } from "@clerk/nextjs";
import { BrandMark } from "@/components/brand-mark";

const navItems = [
  { href: "/dashboard", label: "Dashboard", icon: LayoutDashboard },
  { href: "/leads", label: "Leads", icon: UploadCloud },
  { href: "/knowledge-base", label: "Knowledge Base", icon: BookOpenText },
  { href: "/calls", label: "Calls", icon: PhoneCall },
  { href: "/settings", label: "Settings", icon: Settings },
] as const;

export function AppShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const { signOut } = useClerk();
  const { user } = useUser();
  const { organization } = useOrganization();

  return (
    <div className="min-h-screen bg-[#f7f6f2]">
      <aside className="fixed inset-y-0 left-0 hidden w-64 border-r border-[#171714] bg-[#fffefa] lg:block">
        <div className="flex h-full flex-col">
          <div className="border-b border-[#171714] px-5 py-5">
            <BrandMark />
          </div>

          <nav className="flex-1 space-y-1 px-3 py-5">
            {navItems.map((item) => {
              const isActive = pathname === item.href;
              return (
                <Link
                  key={item.href}
                  href={item.href}
                  className={`flex h-11 items-center gap-3 border-l-2 px-3 text-sm font-bold transition ${
                    isActive
                      ? "border-[#d73a2f] bg-[#f3e8e5] text-[#b72c24]"
                      : "border-transparent text-[#4e4c46] hover:bg-[#f0eee8] hover:text-[#171714]"
                  }`}
                >
                  <item.icon className="size-4" aria-hidden />
                  {item.label}
                </Link>
              );
            })}
          </nav>

          <div className="border-t border-[#171714] p-4">
            <div className="mb-3 border border-[#d8d5cc] bg-[#f7f6f2] p-3">
              <p className="truncate text-sm font-bold text-[#171714]">
                {user?.fullName ?? user?.primaryEmailAddress?.emailAddress ?? "Loading"}
              </p>
              <p className="mt-1 truncate text-xs text-[#6d6b64]">
                {organization?.name ?? "Your workspace"}
              </p>
            </div>
            <button
              className="flex h-10 w-full items-center gap-3 px-3 text-left text-sm font-bold text-[#4e4c46] hover:bg-[#f0eee8]"
              onClick={() => signOut({ redirectUrl: "/sign-in" })}
              type="button"
            >
              <LogOut className="size-4" aria-hidden />
              Sign out
            </button>
          </div>
        </div>
      </aside>

      <div className="lg:pl-64">
        <header className="sticky top-0 z-10 border-b border-[#171714] bg-[#fffefa]/95 backdrop-blur">
          <div className="flex h-16 items-center justify-between gap-4 px-5 lg:px-8">
            <div className="lg:hidden"><BrandMark /></div>
            <div className="hidden min-w-0 lg:block">
              <p className="utility-label">Active workspace</p>
              <p className="truncate text-sm font-bold text-[#171714]">
                {organization?.name ?? "RingIQ workspace"}
              </p>
            </div>
            <button
              className="inline-flex size-10 items-center justify-center border border-[#d8d5cc] text-[#4e4c46] transition hover:border-[#d73a2f] hover:text-[#d73a2f] lg:hidden"
              onClick={() => signOut({ redirectUrl: "/sign-in" })}
              title="Sign out"
              type="button"
            >
              <LogOut className="size-4" aria-hidden />
              <span className="sr-only">Sign out</span>
            </button>
          </div>
          <nav className="flex overflow-x-auto border-t border-[#d8d5cc] px-2 lg:hidden" aria-label="Product navigation">
            {navItems.map((item) => {
              const isActive = pathname === item.href;
              return (
                <Link key={item.href} href={item.href} className={`flex h-12 min-w-[4.5rem] flex-1 items-center justify-center gap-2 border-b-2 px-2 text-xs font-bold ${isActive ? "border-[#d73a2f] text-[#b72c24]" : "border-transparent text-[#6d6b64]"}`}>
                  <item.icon className="size-4 shrink-0" aria-hidden />
                  <span className="hidden sm:inline">{item.label}</span>
                </Link>
              );
            })}
          </nav>
        </header>
        <main className="px-5 py-7 lg:px-8 lg:py-9">{children}</main>
      </div>
    </div>
  );
}
