"use client";

import { useState } from "react";
import { RefreshCw, ShieldCheck, TriangleAlert } from "lucide-react";
import { useAuth, useOrganization } from "@clerk/nextjs";
import { fetchBackendIdentity, type BackendIdentity } from "@/lib/api-client";

export function BackendContextPanel() {
  const { getToken } = useAuth();
  const { organization } = useOrganization();
  const [identity, setIdentity] = useState<BackendIdentity | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  async function refreshContext() {
    setIsLoading(true);
    setError(null);

    try {
      const token = await getToken();
      if (!token) {
        setError("No active Clerk session token is available.");
        return;
      }

      setIdentity(await fetchBackendIdentity(token));
    } catch (err) {
      setIdentity(null);
      setError(err instanceof Error ? err.message : "Backend context request failed.");
    } finally {
      setIsLoading(false);
    }
  }

  return (
    <section className="border border-[#d8d5cc] bg-[#fffefa] p-6">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
        <div>
          <p className="utility-label !text-[#2f4e6f]">Connection check</p>
          <h2 className="mt-3 text-xl font-black text-[#171714]">
            App and API connection
          </h2>
          <p className="mt-3 max-w-2xl text-sm leading-6 text-[#6d6b64]">
            Confirm that your signed-in session can securely reach the RingIQ API.
          </p>
        </div>
        <button
          className="inline-flex h-10 items-center justify-center gap-2 bg-[#171714] px-4 text-sm font-bold text-white transition hover:bg-[#d73a2f] disabled:cursor-not-allowed disabled:opacity-70"
          disabled={isLoading}
          onClick={refreshContext}
          type="button"
        >
          <RefreshCw className={`size-4 ${isLoading ? "animate-spin" : ""}`} aria-hidden />
          Refresh
        </button>
      </div>

      {!organization ? (
        <div className="mt-5 flex gap-3 border-l-2 border-[#9a6517] bg-[#f5eddb] p-4 text-sm text-[#7c5114]">
          <TriangleAlert className="mt-0.5 size-4 shrink-0" aria-hidden />
          <p>
            Choose a workspace in your account before checking the API connection.
          </p>
        </div>
      ) : null}

      {error ? (
        <div className="mt-5 flex gap-3 border-l-2 border-[#d73a2f] bg-[#f6e9e6] p-4 text-sm text-[#8f221c]">
          <TriangleAlert className="mt-0.5 size-4 shrink-0" aria-hidden />
          <p>{error}</p>
        </div>
      ) : null}

      {identity ? (
        <div className="mt-5 border border-[#aeb6a7] bg-[#eef0ea] p-4">
          <div className="mb-4 flex items-center gap-2 text-sm font-bold text-[#4d5b44]">
            <ShieldCheck className="size-4" aria-hidden />
            Backend context resolved
          </div>
          <dl className="grid gap-3 text-sm sm:grid-cols-3">
            <div>
              <dt className="text-[#6d6b64]">Workspace</dt>
              <dd className="mt-1 font-bold text-[#171714]">{identity.tenant.name}</dd>
            </div>
            <div>
              <dt className="text-[#6d6b64]">User</dt>
              <dd className="mt-1 font-bold text-[#171714]">{identity.user.email}</dd>
            </div>
            <div>
              <dt className="text-[#6d6b64]">Role</dt>
              <dd className="mt-1 font-bold text-[#171714]">{identity.membership.role}</dd>
            </div>
          </dl>
        </div>
      ) : null}
    </section>
  );
}
