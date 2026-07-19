"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import Link from "next/link";
import {
  Activity,
  Building2,
  CheckCircle2,
  FileQuestion,
  Loader2,
  ShieldCheck,
  Sparkles,
  TriangleAlert,
  Users,
  X,
} from "lucide-react";
import { useAuth } from "@clerk/nextjs";
import {
  fetchPlatformIdentity,
  fetchPlatformOverview,
  seedRealEstateStarterTemplate,
  type PlatformIdentity,
  type PlatformOverview,
} from "@/lib/api-client";

function humanizeError(error: unknown) {
  const value = error instanceof Error ? error.message : "Unable to complete that request.";
  return value.replaceAll("_", " ");
}

export function PlatformDashboard() {
  const { getToken } = useAuth();
  const [identity, setIdentity] = useState<PlatformIdentity | null>(null);
  const [overview, setOverview] = useState<PlatformOverview | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isSeeding, setIsSeeding] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);

  const canSeedTemplate = useMemo(
    () => identity?.role === "platform_super_admin" || identity?.role === "template_manager",
    [identity?.role],
  );

  const withToken = useCallback(async <T,>(callback: (token: string) => Promise<T>) => {
    const token = await getToken();
    if (!token) throw new Error("unauthorized");
    return callback(token);
  }, [getToken]);

  const loadDashboard = useCallback(async () => {
    const [platformIdentity, platformOverview] = await Promise.all([
      withToken(fetchPlatformIdentity),
      withToken(fetchPlatformOverview),
    ]);
    setIdentity(platformIdentity);
    setOverview(platformOverview);
  }, [withToken]);

  useEffect(() => {
    let cancelled = false;
    async function load() {
      try {
        await loadDashboard();
      } catch (caught) {
        if (!cancelled) setError(humanizeError(caught));
      } finally {
        if (!cancelled) setIsLoading(false);
      }
    }
    void load();
    return () => { cancelled = true; };
  }, [loadDashboard]);

  async function seedTemplate() {
    try {
      setIsSeeding(true);
      setError(null);
      const result = await withToken(seedRealEstateStarterTemplate);
      await loadDashboard();
      setNotice(result.created_template ? "Real-estate starter template created." : "Real-estate starter template already exists.");
    } catch (caught) {
      setError(humanizeError(caught));
    } finally {
      setIsSeeding(false);
    }
  }

  if (isLoading) {
    return (
      <div className="flex min-h-96 items-center justify-center text-sm font-bold text-[#6d6b64]">
        <Loader2 className="mr-3 size-5 animate-spin" aria-hidden />
        Loading platform dashboard
      </div>
    );
  }

  const counts = overview?.counts;
  const metrics = [
    { label: "Organizations", value: counts?.organizations ?? 0, detail: `${counts?.active_organizations ?? 0} active`, icon: Building2 },
    { label: "Tenant users", value: counts?.tenant_users ?? 0, detail: "Customer workspace accounts", icon: Users },
    { label: "Platform users", value: counts?.platform_users ?? 0, detail: "RingIQ console accounts", icon: ShieldCheck },
    { label: "Published templates", value: counts?.published_templates ?? 0, detail: `${counts?.draft_templates ?? 0} drafts`, icon: FileQuestion },
  ];

  return (
    <div className="mx-auto max-w-6xl">
      <div className="border-b border-[#171714] pb-7">
        <p className="utility-label !text-[#d73a2f]">Platform overview</p>
        <div className="mt-3 flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
          <div>
            <h1 className="text-3xl font-black text-[#171714] sm:text-4xl">Operations workspace</h1>
            <p className="mt-3 max-w-2xl text-sm leading-6 text-[#6d6b64]">
              Platform controls and aggregate service visibility for the RingIQ team.
            </p>
          </div>
          <div className="inline-flex h-10 items-center gap-2 border border-[#aeb6a7] bg-[#eef0ea] px-3 text-sm font-bold text-[#4d5b44]">
            <ShieldCheck className="size-4" aria-hidden />
            Privacy boundary active
          </div>
        </div>
      </div>

      {error ? (
        <div className="mt-6 flex items-start gap-3 border-l-2 border-[#d73a2f] bg-[#f6e9e6] p-4 text-sm text-[#8f221c]">
          <TriangleAlert className="mt-0.5 size-4 shrink-0" aria-hidden />
          <p>{error}</p>
          <button className="ml-auto" onClick={() => setError(null)} title="Dismiss" type="button"><X className="size-4" /></button>
        </div>
      ) : null}
      {notice ? (
        <div className="mt-6 flex items-center gap-3 border-l-2 border-[#66735b] bg-[#eef0ea] p-4 text-sm text-[#4d5b44]">
          <CheckCircle2 className="size-4" aria-hidden />
          <p>{notice}</p>
          <button className="ml-auto" onClick={() => setNotice(null)} title="Dismiss" type="button"><X className="size-4" /></button>
        </div>
      ) : null}

      <section className="mt-7 grid gap-px border border-[#171714] bg-[#171714] sm:grid-cols-2 lg:grid-cols-4">
        {metrics.map((item) => (
          <article className="min-h-40 bg-[#fffefa] p-5" key={item.label}>
            <item.icon className="size-5 text-[#2f4e6f]" aria-hidden />
            <p className="mt-8 text-3xl font-black text-[#171714]">{item.value}</p>
            <h2 className="mt-2 text-sm font-black text-[#171714]">{item.label}</h2>
            <p className="mt-1 text-xs leading-5 text-[#6d6b64]">{item.detail}</p>
          </article>
        ))}
      </section>

      <section className="mt-8 grid gap-6 lg:grid-cols-[1.2fr_0.8fr]">
        <div className="border border-[#171714] bg-[#fffefa] p-6">
          <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
            <div>
              <p className="utility-label !text-[#2f4e6f]">First category setup</p>
              <h2 className="mt-3 text-xl font-black text-[#171714]">Real-estate starter KB</h2>
              <p className="mt-3 max-w-xl text-sm leading-6 text-[#6d6b64]">
                Seed the first reusable category and draft questionnaire that new organizations can adopt during knowledge-base setup.
              </p>
            </div>
            <div className="shrink-0">
              {overview?.first_template_seeded ? (
                <span className="inline-flex h-10 items-center gap-2 border border-[#aeb6a7] bg-[#eef0ea] px-3 text-sm font-bold text-[#4d5b44]">
                  <CheckCircle2 className="size-4" aria-hidden />
                  Seeded
                </span>
              ) : (
                <span className="inline-flex h-10 items-center gap-2 border border-[#d9bc82] bg-[#f5eddb] px-3 text-sm font-bold text-[#7c5114]">
                  <Sparkles className="size-4" aria-hidden />
                  Ready to create
                </span>
              )}
            </div>
          </div>
          <div className="mt-6 flex flex-wrap gap-3">
            {canSeedTemplate ? (
              <button
                className="inline-flex h-10 items-center gap-2 bg-[#171714] px-4 text-sm font-bold text-white hover:bg-[#d73a2f] disabled:opacity-60"
                disabled={isSeeding}
                onClick={seedTemplate}
                type="button"
              >
                {isSeeding ? <Loader2 className="size-4 animate-spin" aria-hidden /> : <Sparkles className="size-4" aria-hidden />}
                {overview?.first_template_seeded ? "Check seed" : "Seed template"}
              </button>
            ) : null}
            <Link className="inline-flex h-10 items-center gap-2 border border-[#171714] px-4 text-sm font-bold hover:bg-[#f0eee8]" href="/platform/templates">
              <FileQuestion className="size-4" aria-hidden />
              Open templates
            </Link>
          </div>
        </div>

        <div className="border border-[#d8d5cc] bg-[#fffefa] p-6">
          <p className="utility-label !text-[#9a6517]">Service pulse</p>
          <div className="mt-6 space-y-5">
            {[
              { label: "Suspended organizations", value: counts?.suspended_organizations ?? 0 },
              { label: "Active categories", value: counts?.active_categories ?? 0 },
              { label: "Private tenant records exposed", value: 0 },
            ].map((item) => (
              <div className="border-l-2 border-[#d8d5cc] pl-4" key={item.label}>
                <p className="text-sm text-[#6d6b64]">{item.label}</p>
                <p className="mt-1 text-xl font-black text-[#171714]">{item.value}</p>
              </div>
            ))}
          </div>
          <div className="mt-6 flex items-start gap-3 border-t border-[#d8d5cc] pt-5 text-sm leading-6 text-[#4e4c46]">
            <Activity className="mt-0.5 size-4 shrink-0 text-[#2f4e6f]" aria-hidden />
            <p>Lead records, private knowledge bases, transcripts and recordings remain outside this console.</p>
          </div>
        </div>
      </section>
    </div>
  );
}
