"use client";

import { useAuth } from "@clerk/nextjs";
import {
  ChevronDown,
  ChevronUp,
  Headphones,
  Loader2,
  MessageSquareText,
  PhoneCall,
  RefreshCw,
} from "lucide-react";
import Link from "next/link";
import type { Route } from "next";
import { useCallback, useEffect, useState } from "react";

import { fetchCalls, type CallActivity } from "@/lib/api-client";
import { PostCallOutcome } from "@/components/post-call-outcome";

function formatDuration(seconds: number | null) {
  if (seconds == null) return "--";
  const minutes = Math.floor(seconds / 60);
  const remainder = seconds % 60;
  return minutes ? `${minutes}m ${remainder}s` : `${remainder}s`;
}

export function CallsWorkspace() {
  const { getToken } = useAuth();
  const [calls, setCalls] = useState<CallActivity[]>([]);
  const [expandedId, setExpandedId] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    try {
      const token = await getToken();
      if (!token) throw new Error("unauthorized");
      setCalls(await fetchCalls(token));
      setError(null);
    } catch (caught) {
      setError(caught instanceof Error ? caught.message.replaceAll("_", " ") : "Calls could not be loaded.");
    } finally {
      setIsLoading(false);
    }
  }, [getToken]);

  useEffect(() => {
    const initialLoad = window.setTimeout(() => void load(), 0);
    return () => window.clearTimeout(initialLoad);
  }, [load]);

  if (isLoading) {
    return <div className="flex min-h-72 items-center justify-center text-sm font-bold text-[#6d6b64]"><Loader2 className="mr-3 size-5 animate-spin" />Loading calls</div>;
  }

  return <div className="mx-auto max-w-6xl">
    <header className="flex items-end justify-between border-b border-[#171714] pb-7">
      <div>
        <p className="utility-label !text-[#d73a2f]">Calls</p>
        <h1 className="mt-3 text-3xl font-black text-[#171714] sm:text-4xl">Call activity</h1>
      </div>
      <button className="inline-flex size-10 items-center justify-center border border-[#171714] hover:bg-[#f0eee8]" onClick={() => void load()} title="Refresh calls" type="button"><RefreshCw className="size-4" /></button>
    </header>

    {error ? <div className="mt-6 border-l-2 border-[#d73a2f] bg-[#f6e9e6] p-4 text-sm text-[#8f221c]">{error}</div> : null}

    <section className="mt-7 border border-[#d8d5cc] bg-[#fffefa]">
      <div className="hidden grid-cols-[minmax(0,1fr)_130px_100px_120px_44px] gap-4 border-b border-[#d8d5cc] px-5 py-3 text-xs font-black uppercase text-[#6d6b64] md:grid">
        <span>Lead</span><span>Status</span><span>Duration</span><span>Recording</span><span />
      </div>
      <div className="divide-y divide-[#e3e0d8]">
        {calls.map((call) => {
          const isExpanded = expandedId === call.id;
          return <article key={call.id}>
            <div className="grid gap-4 p-5 md:grid-cols-[minmax(0,1fr)_130px_100px_120px_44px] md:items-center">
              <div className="min-w-0">
                <Link className="font-black text-[#171714] hover:text-[#d73a2f]" href={`/leads/${call.lead_id}` as Route}>{call.lead_name}</Link>
                <p className="mt-1 truncate text-xs text-[#6d6b64]">{call.campaign_name} · {call.lead_phone_number}{call.started_at ? ` · ${new Date(call.started_at).toLocaleString()}` : ""}</p>
              </div>
              <div><span className="text-sm font-bold capitalize">{call.status.replaceAll("_", " ")}</span><div className="mt-1"><PostCallOutcome callStatus={call.status} compact outcome={call.outcome} /></div></div>
              <span className="text-sm text-[#6d6b64]">{formatDuration(call.duration_seconds)}</span>
              <div>
                {call.recording_url ? <audio className="h-8 w-28" controls preload="none" src={call.recording_url}><track kind="captions" /></audio> : <span className="inline-flex items-center gap-2 text-xs font-bold text-[#6d6b64]"><Headphones className="size-4" />{call.recording_status === "recording" ? "Processing" : "Unavailable"}</span>}
              </div>
              <button aria-expanded={isExpanded} className="inline-flex size-9 items-center justify-center border border-[#d8d5cc] hover:border-[#171714] disabled:opacity-40" disabled={!call.transcript.length && !call.outcome} onClick={() => setExpandedId(isExpanded ? null : call.id)} title={isExpanded ? "Hide call details" : "Show call details"} type="button">{isExpanded ? <ChevronUp className="size-4" /> : <ChevronDown className="size-4" />}</button>
            </div>
            {isExpanded ? <div className="border-t border-[#e3e0d8] bg-[#f7f6f1] px-5 py-5">
              <PostCallOutcome callStatus={call.status} outcome={call.outcome} />
              {call.transcript.length ? <div className="mt-6 border-t border-[#d8d5cc] pt-5"><div className="mb-4 flex items-center gap-2 text-xs font-black uppercase text-[#6d6b64]"><MessageSquareText className="size-4" />Transcript</div>
              <div className="space-y-3">{call.transcript.map((turn, index) => <div className="grid gap-1 sm:grid-cols-[80px_minmax(0,1fr)]" key={`${call.id}-${index}`}><span className="text-xs font-black uppercase text-[#6d6b64]">{turn.role === "assistant" ? "Agent" : "Customer"}</span><p className="text-sm leading-6 text-[#171714]">{turn.text}</p></div>)}</div></div> : null}
            </div> : null}
          </article>;
        })}
        {!calls.length ? <div className="p-10 text-center"><PhoneCall className="mx-auto size-6 text-[#6d6b64]" /><p className="mt-3 text-sm text-[#6d6b64]">No calls yet.</p></div> : null}
      </div>
    </section>
  </div>;
}
