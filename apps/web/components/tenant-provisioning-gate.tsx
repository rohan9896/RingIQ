"use client";

import { useEffect, useState } from "react";
import { Loader2, LogOut, RefreshCw, TriangleAlert } from "lucide-react";
import { useAuth, useClerk } from "@clerk/nextjs";
import { bootstrapTenantMembership } from "@/lib/api-client";

type ProvisioningState = "loading" | "ready" | "error";

export function TenantProvisioningGate({ children }: { children: React.ReactNode }) {
  const { isLoaded, orgId, getToken } = useAuth();
  const { signOut } = useClerk();
  const [state, setState] = useState<ProvisioningState>("loading");
  const [provisionedOrgId, setProvisionedOrgId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [attempt, setAttempt] = useState(0);

  useEffect(() => {
    if (!isLoaded || !orgId) return;

    const controller = new AbortController();
    const timeout = window.setTimeout(() => controller.abort(), 15000);

    void getToken()
      .then((token) => {
        if (!token) throw new Error("No active session token is available.");
        return bootstrapTenantMembership(token, controller.signal);
      })
      .then(() => {
        setProvisionedOrgId(orgId);
        setState("ready");
      })
      .catch((caught: unknown) => {
        setProvisionedOrgId(orgId);
        if (controller.signal.aborted) {
          setError("Workspace setup timed out. Check the API server and retry.");
        } else {
          setError(
            caught instanceof Error
              ? caught.message.replaceAll("_", " ")
              : "Workspace setup failed.",
          );
        }
        setState("error");
      })
      .finally(() => window.clearTimeout(timeout));

    return () => {
      window.clearTimeout(timeout);
      controller.abort();
    };
  }, [attempt, getToken, isLoaded, orgId]);

  if (state === "ready" && provisionedOrgId === orgId) return children;

  const isLoading = state === "loading" || provisionedOrgId !== orgId;

  return (
    <main className="paper-grid grid min-h-screen place-items-center bg-[#f7f6f2] px-5 py-10">
      <section className="w-full max-w-lg border border-[#171714] bg-[#fffefa] p-7 sm:p-9">
        {isLoading ? (
          <div className="flex items-center gap-4">
            <Loader2 className="size-6 animate-spin text-[#d73a2f]" aria-hidden />
            <div>
              <p className="utility-label !text-[#d73a2f]">Preparing workspace</p>
              <h1 className="mt-2 text-xl font-black text-[#171714]">
                Confirming organization membership
              </h1>
            </div>
          </div>
        ) : (
          <>
            <div className="flex gap-3 border-l-2 border-[#d73a2f] bg-[#f6e9e6] p-4 text-sm text-[#8f221c]">
              <TriangleAlert className="mt-0.5 size-4 shrink-0" aria-hidden />
              <p>{error ?? "Workspace setup failed."}</p>
            </div>
            <div className="mt-6 flex flex-col gap-3 sm:flex-row">
              <button
                className="inline-flex h-11 flex-1 items-center justify-center gap-2 bg-[#171714] px-4 text-sm font-bold text-white hover:bg-[#d73a2f]"
                onClick={() => {
                  setState("loading");
                  setError(null);
                  setAttempt((value) => value + 1);
                }}
                type="button"
              >
                <RefreshCw className="size-4" aria-hidden />
                Retry
              </button>
              <button
                className="inline-flex h-11 flex-1 items-center justify-center gap-2 border border-[#171714] px-4 text-sm font-bold text-[#171714] hover:bg-[#f0eee8]"
                onClick={() => signOut({ redirectUrl: "/sign-in" })}
                type="button"
              >
                <LogOut className="size-4" aria-hidden />
                Sign out
              </button>
            </div>
          </>
        )}
      </section>
    </main>
  );
}
