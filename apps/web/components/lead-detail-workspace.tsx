"use client";

import Link from "next/link";
import type { Route } from "next";
import { useCallback, useEffect, useState } from "react";
import { Archive, ArrowLeft, Loader2, RotateCcw, Save, TriangleAlert } from "lucide-react";
import { useAuth } from "@clerk/nextjs";
import {
  archiveLead,
  fetchLead,
  fetchLeadCampaignHistory,
  restoreLead,
  type Lead,
  type LeadCampaignHistory,
  updateLead,
} from "@/lib/api-client";

const manualStatuses = ["new", "in_progress", "follow_up", "closed"] as const;

function friendlyError(error: unknown) {
  const value = error instanceof Error ? error.message : "We could not update this lead.";
  return value.replaceAll("_", " ");
}

export function LeadDetailWorkspace({ leadId }: { leadId: string }) {
  const { getToken } = useAuth();
  const [lead, setLead] = useState<Lead | null>(null);
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [phoneNumber, setPhoneNumber] = useState("");
  const [manualStatus, setManualStatus] = useState<Lead["manual_status"]>("new");
  const [attributes, setAttributes] = useState("{}");
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);
  const [campaignHistory, setCampaignHistory] = useState<LeadCampaignHistory[]>([]);

  const withToken = useCallback(
    async <T,>(callback: (token: string) => Promise<T>) => {
      const token = await getToken();
      if (!token) throw new Error("unauthorized");
      return callback(token);
    },
    [getToken],
  );

  const applyLead = useCallback((nextLead: Lead) => {
    setLead(nextLead);
    setName(nextLead.name);
    setEmail(nextLead.email);
    setPhoneNumber(nextLead.phone_number);
    setManualStatus(nextLead.manual_status);
    setAttributes(JSON.stringify(nextLead.attributes_json, null, 2));
  }, []);

  useEffect(() => {
    let cancelled = false;
    async function load() {
      try {
        const [nextLead, nextHistory] = await Promise.all([
          withToken((token) => fetchLead(token, leadId)),
          withToken((token) => fetchLeadCampaignHistory(token, leadId)),
        ]);
        if (!cancelled) {
          applyLead(nextLead);
          setCampaignHistory(nextHistory);
        }
      } catch (caught) {
        if (!cancelled) setError(friendlyError(caught));
      } finally {
        if (!cancelled) setIsLoading(false);
      }
    }
    void load();
    return () => {
      cancelled = true;
    };
  }, [applyLead, leadId, withToken]);

  async function saveLead() {
    if (!lead) return;
    let attributesJson: Record<string, unknown>;
    try {
      const parsed: unknown = JSON.parse(attributes);
      if (!parsed || Array.isArray(parsed) || typeof parsed !== "object") {
        throw new Error();
      }
      attributesJson = parsed as Record<string, unknown>;
    } catch {
      setError("Optional details must be a valid JSON object.");
      return;
    }
    try {
      setIsSaving(true);
      setError(null);
      const nextLead = await withToken((token) =>
        updateLead(token, lead.id, {
          name,
          email,
          phone_number: phoneNumber,
          attributes_json: attributesJson,
          manual_status: manualStatus,
        }),
      );
      applyLead(nextLead);
      setNotice("Lead updated.");
    } catch (caught) {
      setError(friendlyError(caught));
    } finally {
      setIsSaving(false);
    }
  }

  async function changeArchiveState() {
    if (!lead) return;
    try {
      setIsSaving(true);
      setError(null);
      const nextLead = await withToken((token) =>
        lead.status === "archived"
          ? restoreLead(token, lead.id)
          : archiveLead(token, lead.id),
      );
      applyLead(nextLead);
      setNotice(nextLead.status === "archived" ? "Lead archived." : "Lead restored.");
    } catch (caught) {
      setError(friendlyError(caught));
    } finally {
      setIsSaving(false);
    }
  }

  if (isLoading) {
    return <div className="flex min-h-72 items-center justify-center text-sm font-bold text-[#6d6b64]"><Loader2 className="mr-3 size-5 animate-spin" />Loading lead</div>;
  }

  if (!lead) {
    return <LeadMessage message={error ?? "Lead not found."} />;
  }

  return (
    <div className="mx-auto max-w-4xl">
      <Link className="inline-flex h-9 items-center gap-2 text-sm font-bold text-[#4e4c46] hover:text-[#d73a2f]" href="/leads">
        <ArrowLeft className="size-4" />
        All leads
      </Link>
      <header className="mt-4 flex flex-col gap-5 border-b border-[#171714] pb-7 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <p className="utility-label !text-[#d73a2f]">Lead detail</p>
          <h1 className="mt-3 text-3xl font-black text-[#171714]">{lead.name}</h1>
          <p className="mt-2 text-sm text-[#6d6b64]">Added {new Date(lead.created_at).toLocaleString()}</p>
        </div>
        <span className={`inline-flex h-8 items-center border px-3 text-xs font-bold ${lead.status === "archived" ? "border-[#9a6517] bg-[#f7edd8] text-[#805111]" : "border-[#aeb6a7] bg-[#eef0ea] text-[#4d5b44]"}`}>
          {lead.status}
        </span>
      </header>
      {error ? <LeadMessage message={error} /> : null}
      {notice ? <div className="mt-6 border-l-2 border-[#66735b] bg-[#eef0ea] p-4 text-sm text-[#4d5b44]">{notice}</div> : null}
      <section className="mt-7 border border-[#d8d5cc] bg-[#fffefa]">
        <div className="border-b border-[#d8d5cc] p-5"><p className="utility-label">Contact and sales work</p></div>
        <div className="grid gap-5 p-5 md:grid-cols-2">
          <Field label="Name"><input className="field-control mt-2" onChange={(event) => setName(event.target.value)} value={name} /></Field>
          <Field label="Email"><input className="field-control mt-2" onChange={(event) => setEmail(event.target.value)} type="email" value={email} /></Field>
          <Field label="Phone number"><input className="field-control mt-2" onChange={(event) => setPhoneNumber(event.target.value)} value={phoneNumber} /></Field>
          <Field label="Manual sales status"><select className="field-control mt-2" onChange={(event) => setManualStatus(event.target.value as Lead["manual_status"])} value={manualStatus}>{manualStatuses.map((item) => <option key={item} value={item}>{item.replaceAll("_", " ")}</option>)}</select></Field>
          <div className="md:col-span-2"><Field label="Optional details"><textarea className="field-control mt-2 min-h-40 font-mono text-xs" onChange={(event) => setAttributes(event.target.value)} spellCheck={false} value={attributes} /></Field></div>
        </div>
        <div className="flex flex-col gap-3 border-t border-[#d8d5cc] p-5 sm:flex-row sm:justify-between">
          <button className="inline-flex h-10 items-center justify-center gap-2 border border-[#171714] px-4 text-sm font-bold hover:bg-[#f0eee8] disabled:opacity-60" disabled={isSaving} onClick={() => void changeArchiveState()} type="button">
            {lead.status === "archived" ? <RotateCcw className="size-4" /> : <Archive className="size-4" />}
            {lead.status === "archived" ? "Restore lead" : "Archive lead"}
          </button>
          <button className="inline-flex h-10 items-center justify-center gap-2 bg-[#171714] px-4 text-sm font-bold text-white hover:bg-[#d73a2f] disabled:opacity-60" disabled={isSaving} onClick={() => void saveLead()} type="button">
            {isSaving ? <Loader2 className="size-4 animate-spin" /> : <Save className="size-4" />}
            Save changes
          </button>
        </div>
      </section>
      <section className="mt-7 border border-[#d8d5cc] bg-[#fffefa]">
        <div className="border-b border-[#d8d5cc] p-5"><p className="utility-label">Campaign and call history</p></div>
        <div className="divide-y divide-[#e3e0d8]">
          {campaignHistory.map((item) => (
            <div className="grid gap-4 p-5 sm:grid-cols-[minmax(0,1fr)_120px_120px] sm:items-center" key={item.enrollment_id}>
              <div>
                <Link className="font-black hover:text-[#d73a2f]" href={`/campaigns?campaign=${item.campaign_id}` as Route}>{item.campaign_name}</Link>
                <p className="mt-1 text-xs text-[#6d6b64]">Campaign {item.campaign_status.replaceAll("_", " ")}</p>
              </div>
              <div><p className="utility-label">Enrollment</p><p className="mt-1 text-sm font-bold">{item.enrollment_status.replaceAll("_", " ")}</p></div>
              <div><p className="utility-label">Attempts</p><p className="mt-1 text-sm font-bold">{item.attempt_count}</p></div>
              {item.attempts.length ? <div className="sm:col-span-3"><div className="flex flex-wrap gap-2">{item.attempts.map((attempt) => <span className="border border-[#d8d5cc] px-2 py-1 text-xs" key={attempt.id}>Attempt {attempt.attempt_number}: {attempt.status.replaceAll("_", " ")}</span>)}</div></div> : null}
            </div>
          ))}
          {!campaignHistory.length ? <div className="p-5 text-sm text-[#6d6b64]">This lead has not been enrolled in a campaign.</div> : null}
        </div>
      </section>
    </div>
  );
}

function Field({ children, label }: { children: React.ReactNode; label: string }) {
  return <label className="block text-sm font-bold">{label}{children}</label>;
}

function LeadMessage({ message }: { message: string }) {
  return <div className="mt-6 flex gap-3 border-l-2 border-[#d73a2f] bg-[#f6e9e6] p-4 text-sm text-[#8f221c]"><TriangleAlert className="size-4 shrink-0" />{message}</div>;
}
