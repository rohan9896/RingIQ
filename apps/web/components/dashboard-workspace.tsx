"use client";

import Link from "next/link";
import type { Route } from "next";
import { useAuth } from "@clerk/nextjs";
import { Activity, BookOpenText, Check, CircleAlert, Loader2, PhoneCall, RefreshCw, UsersRound } from "lucide-react";
import { useCallback, useEffect, useState } from "react";
import {
  fetchDashboard,
  fetchWorkspaceCategories,
  updateWorkspaceCategory,
  type DashboardData,
  type WorkspaceCategory,
} from "@/lib/api-client";

const blockerLabels: Record<string, string> = {
  organization_category_required: "Choose your business category",
  active_knowledge_base_required: "Publish your knowledge base",
  business_profile_required: "Complete the business profile",
  knowledge_base_category_mismatch: "Publish a knowledge base for the selected category",
};

export function DashboardWorkspace() {
  const { getToken } = useAuth();
  const [data, setData] = useState<DashboardData | null>(null);
  const [categories, setCategories] = useState<WorkspaceCategory[]>([]);
  const [categoryId, setCategoryId] = useState("");
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const withToken = useCallback(async <T,>(callback: (token: string) => Promise<T>) => {
    const token = await getToken();
    if (!token) throw new Error("unauthorized");
    return callback(token);
  }, [getToken]);

  const load = useCallback(async (quiet = false) => {
    if (!quiet) setIsLoading(true);
    try {
      const [nextData, nextCategories] = await Promise.all([
        withToken(fetchDashboard),
        withToken(fetchWorkspaceCategories),
      ]);
      setData(nextData);
      setCategories(nextCategories);
      setCategoryId(nextData.workspace.category?.id ?? "");
      setError(null);
    } catch (caught) {
      setError(caught instanceof Error ? caught.message.replaceAll("_", " ") : "Dashboard could not be loaded.");
    } finally {
      if (!quiet) setIsLoading(false);
    }
  }, [withToken]);

  useEffect(() => {
    const initialLoad = window.setTimeout(() => void load(), 0);
    const timer = window.setInterval(() => void load(true), 10000);
    return () => {
      window.clearTimeout(initialLoad);
      window.clearInterval(timer);
    };
  }, [load]);

  async function saveCategory() {
    if (!categoryId) return;
    try {
      setIsSaving(true);
      await withToken((token) => updateWorkspaceCategory(token, categoryId));
      await load(true);
    } catch (caught) {
      setError(caught instanceof Error ? caught.message.replaceAll("_", " ") : "Category could not be saved.");
    } finally {
      setIsSaving(false);
    }
  }

  if (isLoading) return <div className="flex min-h-72 items-center justify-center text-sm font-bold text-[#6d6b64]"><Loader2 className="mr-3 size-5 animate-spin" />Loading workspace</div>;
  if (!data) return <div className="border-l-2 border-[#d73a2f] bg-[#f6e9e6] p-4 text-sm text-[#8f221c]">{error ?? "Dashboard unavailable."}</div>;

  const metrics = [
    { label: "Active leads", value: data.totals.leads, icon: UsersRound },
    { label: "Call attempts", value: data.totals.call_attempts, icon: PhoneCall },
    { label: "Connected", value: data.totals.connected, icon: Activity },
    { label: "Failed", value: data.totals.failed, icon: CircleAlert },
  ];
  const nextBlocker = data.workspace.readiness_blockers[0];

  return <div className="mx-auto max-w-6xl">
    <header className="flex flex-col gap-4 border-b border-[#171714] pb-7 sm:flex-row sm:items-end sm:justify-between">
      <div><p className="utility-label !text-[#d73a2f]">Overview</p><h1 className="mt-3 text-3xl font-black text-[#171714] sm:text-4xl">{data.workspace.name}</h1><p className="mt-3 text-sm text-[#6d6b64]">Workspace readiness and recent calling activity.</p></div>
      <button className="inline-flex size-10 items-center justify-center border border-[#171714] hover:bg-[#f0eee8]" onClick={() => void load()} title="Refresh dashboard" type="button"><RefreshCw className="size-4" /></button>
    </header>
    {error ? <div className="mt-6 border-l-2 border-[#d73a2f] bg-[#f6e9e6] p-4 text-sm text-[#8f221c]">{error}</div> : null}

    <section className={`mt-7 border ${data.workspace.is_call_ready ? "border-[#66735b] bg-[#eef0ea]" : "border-[#c6923b] bg-[#f7edd8]"}`}>
      <div className="flex flex-col gap-5 p-5 md:flex-row md:items-center md:justify-between">
        <div className="flex gap-3">{data.workspace.is_call_ready ? <Check className="mt-1 size-5 text-[#4d5b44]" /> : <CircleAlert className="mt-1 size-5 text-[#805111]" />}<div><p className="utility-label">First-call readiness</p><h2 className="mt-2 text-xl font-black">{data.workspace.is_call_ready ? "Ready to call" : blockerLabels[nextBlocker] ?? "Setup needs attention"}</h2><p className="mt-2 text-sm">{data.workspace.is_call_ready ? "Your category and published knowledge base are ready." : "Complete this step before placing a tenant-grounded call."}</p></div></div>
        {!data.workspace.category ? <div className="flex w-full max-w-md gap-2"><select className="field-control" onChange={(event) => setCategoryId(event.target.value)} value={categoryId}><option value="">Choose category</option>{categories.map((category) => <option key={category.id} value={category.id}>{category.name}</option>)}</select><button className="h-10 bg-[#171714] px-4 text-sm font-bold text-white disabled:opacity-50" disabled={!categoryId || isSaving} onClick={() => void saveCategory()} type="button">{isSaving ? "Saving" : "Select"}</button></div> : !data.workspace.has_active_knowledge_base || nextBlocker === "knowledge_base_category_mismatch" || nextBlocker === "business_profile_required" ? <Link className="inline-flex h-10 items-center gap-2 bg-[#171714] px-4 text-sm font-bold text-white hover:bg-[#d73a2f]" href="/knowledge-base"><BookOpenText className="size-4" />Open knowledge base</Link> : <Link className="inline-flex h-10 items-center gap-2 bg-[#171714] px-4 text-sm font-bold text-white hover:bg-[#d73a2f]" href="/leads"><PhoneCall className="size-4" />Choose a lead</Link>}
      </div>
    </section>

    <section className="mt-7 grid gap-4 sm:grid-cols-2 xl:grid-cols-4">{metrics.map((metric) => <article className="border border-[#d8d5cc] bg-[#fffefa] p-5" key={metric.label}><div className="flex items-center justify-between"><p className="utility-label">{metric.label}</p><metric.icon className="size-4 text-[#d73a2f]" /></div><p className="mt-5 text-4xl font-black">{metric.value}</p></article>)}</section>

    <section className="mt-7 border border-[#d8d5cc] bg-[#fffefa]"><div className="flex items-center justify-between border-b border-[#d8d5cc] p-5"><div><p className="utility-label">Recent calls</p><p className="mt-2 text-sm text-[#6d6b64]">Updates automatically every ten seconds.</p></div><span className="text-xs font-bold text-[#6d6b64]">{data.totals.campaigns} call groups</span></div><div className="divide-y divide-[#e3e0d8]">{data.recent_calls.map((call) => <div className="grid gap-3 p-5 sm:grid-cols-[minmax(0,1fr)_120px_100px] sm:items-center" key={call.attempt_id}><div><Link className="font-black hover:text-[#d73a2f]" href={`/leads/${call.lead_id}` as Route}>{call.lead_name}</Link><p className="mt-1 text-xs text-[#6d6b64]">{call.campaign_name}{call.started_at ? ` · ${new Date(call.started_at).toLocaleString()}` : ""}</p>{call.failure_detail ? <p className="mt-2 text-xs text-[#8f221c]">{call.failure_detail}</p> : null}</div><span className="text-sm font-bold capitalize">{call.status.replaceAll("_", " ")}</span><span className="text-sm text-[#6d6b64]">{call.duration_seconds == null ? "—" : `${call.duration_seconds}s`}</span></div>)}{!data.recent_calls.length ? <div className="p-8 text-center text-sm text-[#6d6b64]">No calls yet. Add a lead and place the first call.</div> : null}</div></section>
  </div>;
}
