"use client";

import Link from "next/link";
import type { Route } from "next";
import { useCallback, useEffect, useState } from "react";
import { useSearchParams } from "next/navigation";
import {
  Ban,
  CirclePause,
  CirclePlay,
  Loader2,
  Megaphone,
  PhoneCall,
  RefreshCw,
  TriangleAlert,
  UsersRound,
} from "lucide-react";
import { useAuth } from "@clerk/nextjs";
import {
  changeCampaignState,
  fetchCampaign,
  fetchCampaigns,
  type Campaign,
  type CampaignDetail,
} from "@/lib/api-client";

function friendlyError(error: unknown) {
  const value = error instanceof Error ? error.message : "Campaign operation failed.";
  return value.replaceAll("_", " ");
}

const blockerLabels: Record<string, string> = {
  campaign_leads_required: "Add at least one active lead.",
  active_knowledge_base_required: "Publish an active knowledge base.",
  business_profile_required: "Complete the knowledge-base business profile.",
  campaign_knowledge_base_unavailable: "The campaign knowledge base is no longer available.",
  campaign_knowledge_base_unpublished: "The campaign knowledge base must be published.",
  knowledge_base_category_mismatch: "The knowledge base category does not match the workspace category.",
};

export function CampaignsWorkspace() {
  const { getToken } = useAuth();
  const requestedCampaignId = useSearchParams().get("campaign");
  const [campaigns, setCampaigns] = useState<Campaign[]>([]);
  const [selected, setSelected] = useState<CampaignDetail | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isActing, setIsActing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const withToken = useCallback(async <T,>(callback: (token: string) => Promise<T>) => {
    const token = await getToken();
    if (!token) throw new Error("unauthorized");
    return callback(token);
  }, [getToken]);

  const load = useCallback(async (campaignId?: string) => {
    const nextCampaigns = await withToken(fetchCampaigns);
    setCampaigns(nextCampaigns);
    const targetId = campaignId ?? selected?.id ?? nextCampaigns[0]?.id;
    if (targetId) setSelected(await withToken((token) => fetchCampaign(token, targetId)));
    else setSelected(null);
  }, [selected?.id, withToken]);

  useEffect(() => {
    let cancelled = false;
    async function initialize() {
      try {
        const nextCampaigns = await withToken(fetchCampaigns);
        if (cancelled) return;
        setCampaigns(nextCampaigns);
        const initialCampaign = nextCampaigns.find((item) => item.id === requestedCampaignId) ?? nextCampaigns[0];
        if (initialCampaign) {
          const detail = await withToken((token) => fetchCampaign(token, initialCampaign.id));
          if (!cancelled) setSelected(detail);
        }
      } catch (caught) {
        if (!cancelled) setError(friendlyError(caught));
      } finally {
        if (!cancelled) setIsLoading(false);
      }
    }
    void initialize();
    return () => { cancelled = true; };
  }, [requestedCampaignId, withToken]);

  async function selectCampaign(campaignId: string) {
    try {
      setIsLoading(true);
      setSelected(await withToken((token) => fetchCampaign(token, campaignId)));
    } catch (caught) {
      setError(friendlyError(caught));
    } finally {
      setIsLoading(false);
    }
  }

  async function runAction(action: "start" | "pause" | "resume" | "cancel") {
    if (!selected) return;
    try {
      setIsActing(true);
      setError(null);
      const detail = await withToken((token) => changeCampaignState(token, selected.id, action));
      setSelected(detail);
      await load(detail.id);
    } catch (caught) {
      setError(friendlyError(caught));
    } finally {
      setIsActing(false);
    }
  }

  return (
    <div className="mx-auto max-w-7xl">
      <header className="flex flex-col gap-5 border-b border-[#171714] pb-7 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <p className="utility-label !text-[#d73a2f]">Campaigns</p>
          <h1 className="mt-3 text-3xl font-black text-[#171714] sm:text-4xl">Call operations</h1>
          <p className="mt-3 max-w-2xl text-sm leading-6 text-[#6d6b64]">Launch qualified lead batches, watch every enrollment, and intervene when an attempt needs attention.</p>
        </div>
        <Link className="inline-flex h-10 items-center gap-2 bg-[#171714] px-4 text-sm font-bold text-white hover:bg-[#d73a2f]" href="/leads">
          <UsersRound className="size-4" />
          Select leads
        </Link>
      </header>
      {error ? <div className="mt-6 flex gap-3 border-l-2 border-[#d73a2f] bg-[#f6e9e6] p-4 text-sm text-[#8f221c]"><TriangleAlert className="size-4" />{error}</div> : null}
      {isLoading && !selected ? <div className="flex min-h-64 items-center justify-center text-sm font-bold text-[#6d6b64]"><Loader2 className="mr-3 size-5 animate-spin" />Loading campaigns</div> : null}
      {!isLoading && !campaigns.length ? <div className="mt-7 border border-dashed border-[#d8d5cc] p-10 text-center"><Megaphone className="mx-auto size-6 text-[#2f4e6f]" /><p className="mt-4 font-bold">No campaigns yet</p><p className="mt-2 text-sm text-[#6d6b64]">Select active leads to create the first campaign.</p></div> : null}
      {campaigns.length ? (
        <div className="mt-7 grid gap-7 lg:grid-cols-[280px_minmax(0,1fr)]">
          <aside className="border border-[#d8d5cc] bg-[#fffefa]">
            <div className="border-b border-[#d8d5cc] px-4 py-3"><p className="utility-label">Campaign list</p></div>
            <div className="divide-y divide-[#e3e0d8]">{campaigns.map((campaign) => <button className={`block w-full px-4 py-4 text-left ${selected?.id === campaign.id ? "border-l-2 border-[#d73a2f] bg-[#f3e8e5]" : "border-l-2 border-transparent hover:bg-[#f0eee8]"}`} key={campaign.id} onClick={() => void selectCampaign(campaign.id)} type="button"><p className="truncate text-sm font-black">{campaign.name}</p><div className="mt-2 flex items-center justify-between text-xs text-[#6d6b64]"><span>{campaign.progress.total} leads</span><span>{campaign.status}</span></div></button>)}</div>
          </aside>
          {selected ? <CampaignDetailView campaign={selected} isActing={isActing} onAction={runAction} onRefresh={() => void load(selected.id)} /> : null}
        </div>
      ) : null}
    </div>
  );
}

function CampaignDetailView({ campaign, isActing, onAction, onRefresh }: { campaign: CampaignDetail; isActing: boolean; onAction: (action: "start" | "pause" | "resume" | "cancel") => void; onRefresh: () => void }) {
  const canStart = campaign.status === "draft" || campaign.status === "ready";
  const canPause = campaign.status === "running";
  const canResume = campaign.status === "paused";
  const canCancel = ["draft", "ready", "running", "paused"].includes(campaign.status);
  return <section className="min-w-0">
    <div className="flex flex-col gap-4 border border-[#171714] bg-[#fffefa] p-5 sm:flex-row sm:items-start sm:justify-between">
      <div><p className="utility-label !text-[#2f4e6f]">{campaign.status}</p><h2 className="mt-2 text-2xl font-black">{campaign.name}</h2><p className="mt-2 text-sm text-[#6d6b64]">Initial call plus up to {campaign.retry_limit} unanswered retries</p></div>
      <div className="flex flex-wrap gap-2">
        <button className="inline-flex size-9 items-center justify-center border border-[#d8d5cc] hover:border-[#171714]" onClick={onRefresh} title="Refresh campaign" type="button"><RefreshCw className="size-4" /></button>
        {canStart ? <ActionButton disabled={isActing || !campaign.readiness.is_ready} icon={CirclePlay} label="Start" onClick={() => onAction("start")} primary /> : null}
        {canPause ? <ActionButton disabled={isActing} icon={CirclePause} label="Pause" onClick={() => onAction("pause")} /> : null}
        {canResume ? <ActionButton disabled={isActing} icon={CirclePlay} label="Resume" onClick={() => onAction("resume")} primary /> : null}
        {canCancel ? <ActionButton disabled={isActing} icon={Ban} label="Cancel" onClick={() => onAction("cancel")} /> : null}
      </div>
    </div>
    {campaign.knowledge_base ? <div className="border-x border-b border-[#d8d5cc] bg-[#f7f6f2] px-5 py-4">
      <p className="utility-label">{campaign.knowledge_base.is_pinned ? "Pinned knowledge base" : "Active knowledge base"}</p>
      <div className="mt-2 flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
        <p className="text-sm font-bold text-[#171714]">{campaign.knowledge_base.title} <span className="font-normal text-[#6d6b64]">v{campaign.knowledge_base.version}</span></p>
        <span className={`w-fit border px-2 py-1 text-xs font-bold ${campaign.knowledge_base.is_pinned ? "border-[#4d5b44] text-[#4d5b44]" : "border-[#d8d5cc] text-[#6d6b64]"}`}>{campaign.knowledge_base.is_pinned ? "Campaign locked" : "Will lock on start"}</span>
      </div>
    </div> : null}
    {!campaign.readiness.is_ready && canStart ? <div className="border-x border-b border-[#d8d5cc] bg-[#f7edd8] p-4 text-sm text-[#805111]"><p className="font-bold">Not ready to start</p><ul className="mt-2 space-y-1">{campaign.readiness.blockers.map((blocker) => <li key={blocker}>{blockerLabels[blocker] ?? blocker.replaceAll("_", " ")}</li>)}</ul></div> : null}
    <div className="mt-5 grid gap-px border border-[#d8d5cc] bg-[#d8d5cc] sm:grid-cols-4"><Metric label="Total" value={campaign.progress.total} /><Metric label="Queued" value={campaign.progress.queued + campaign.progress.retry_scheduled} /><Metric label="In call" value={campaign.progress.calling + campaign.progress.connected} /><Metric label="Finished" value={campaign.progress.completed + campaign.progress.invalid_number + campaign.progress.exhausted} /></div>
    <div className="mt-5 overflow-x-auto border border-[#d8d5cc] bg-[#fffefa]"><table className="w-full min-w-[760px] text-left"><thead className="border-b border-[#d8d5cc] bg-[#f7f6f2] text-xs uppercase text-[#6d6b64]"><tr><th className="px-4 py-3">Lead</th><th className="px-4 py-3">State</th><th className="px-4 py-3">Attempts</th><th className="px-4 py-3">Next action</th></tr></thead><tbody className="divide-y divide-[#e3e0d8]">{campaign.enrollments.map((item) => <tr key={item.id}><td className="px-4 py-4"><Link className="font-bold hover:text-[#d73a2f]" href={`/leads/${item.lead_id}` as Route}>{item.lead_name}</Link><p className="mt-1 text-xs text-[#6d6b64]">{item.lead_phone_number}</p></td><td className="px-4 py-4 text-sm">{item.status.replaceAll("_", " ")}{item.last_error_code ? <p className="mt-1 text-xs text-[#8f221c]">{item.last_error_code.replaceAll("_", " ")}</p> : null}</td><td className="px-4 py-4 text-sm">{item.attempt_count}<div className="mt-1 flex gap-1">{item.attempts.map((attempt) => <span className="inline-flex size-6 items-center justify-center border border-[#d8d5cc] text-[10px]" key={attempt.id} title={attempt.failure_detail ?? attempt.status}>{attempt.attempt_number}</span>)}</div></td><td className="px-4 py-4 text-xs text-[#6d6b64]">{item.next_attempt_at ? new Date(item.next_attempt_at).toLocaleString() : "-"}</td></tr>)}</tbody></table></div>
  </section>;
}

function Metric({ label, value }: { label: string; value: number }) { return <div className="bg-[#fffefa] p-4"><p className="utility-label">{label}</p><p className="mt-2 text-2xl font-black">{value}</p></div>; }

function ActionButton({ disabled, icon: Icon, label, onClick, primary = false }: { disabled: boolean; icon: typeof PhoneCall; label: string; onClick: () => void; primary?: boolean }) { return <button className={`inline-flex h-9 items-center gap-2 px-3 text-xs font-bold disabled:opacity-50 ${primary ? "bg-[#171714] text-white hover:bg-[#d73a2f]" : "border border-[#d8d5cc] hover:border-[#171714]"}`} disabled={disabled} onClick={onClick} type="button"><Icon className="size-4" />{label}</button>; }
