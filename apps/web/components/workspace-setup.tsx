"use client";

import { useEffect, useMemo, useState } from "react";
import { useRouter } from "next/navigation";
import { ArrowRight, Building2, Loader2, LogOut } from "lucide-react";
import { useClerk, useOrganizationList, useSessionList } from "@clerk/nextjs";
import { AuthErrors } from "@/components/auth/auth-errors";
import { BrandMark } from "@/components/brand-mark";
import { navigateWithClerk } from "@/lib/clerk-navigation";

function errorMessage(error: unknown) {
  if (error && typeof error === "object" && "errors" in error) {
    const errors = (error as { errors?: Array<{ message?: string }> }).errors;
    if (errors?.[0]?.message) return errors[0].message;
  }
  return error instanceof Error ? error.message : "Workspace setup failed. Please try again.";
}

export function WorkspaceSetup() {
  const router = useRouter();
  const { signOut } = useClerk();
  const { isLoaded: sessionsLoaded, sessions } = useSessionList();
  const {
    isLoaded: organizationsLoaded,
    createOrganization,
    setActive,
    userMemberships,
  } = useOrganizationList({ userMemberships: true });
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const pendingSessionId = useMemo(
    () => sessions?.find((session) => session.currentTask?.key === "choose-organization")?.id,
    [sessions],
  );

  useEffect(() => {
    if (sessionsLoaded && sessions?.length === 0) {
      router.replace("/sign-in");
    }
  }, [router, sessions, sessionsLoaded]);

  async function activateWorkspace(organizationId: string) {
    setError(null);
    setIsSubmitting(true);
    try {
      await setActive?.({
        session: pendingSessionId,
        organization: organizationId,
        navigate: ({ decorateUrl }) =>
          navigateWithClerk(decorateUrl("/dashboard"), router),
      });
      router.refresh();
    } catch (err) {
      setError(errorMessage(err));
      setIsSubmitting(false);
    }
  }

  async function createWorkspace(formData: FormData) {
    const name = String(formData.get("workspaceName") ?? "").trim();
    if (!name) {
      setError("Enter a workspace name.");
      return;
    }

    setError(null);
    setIsSubmitting(true);
    try {
      const organization = await createOrganization?.({ name });
      if (!organization) throw new Error("Clerk could not create the workspace.");
      await activateWorkspace(organization.id);
    } catch (err) {
      setError(errorMessage(err));
      setIsSubmitting(false);
    }
  }

  if (!sessionsLoaded || !organizationsLoaded) {
    return (
      <main className="grid min-h-screen place-items-center bg-[#f7f6f2]">
        <Loader2 className="size-6 animate-spin text-[#d73a2f]" aria-label="Loading" />
      </main>
    );
  }

  return (
    <main className="paper-grid min-h-screen bg-[#f7f6f2] px-5 py-8 sm:px-8">
      <div className="mx-auto max-w-5xl">
        <div className="flex items-center justify-between border-b border-[#171714] pb-6">
          <BrandMark />
          <button
            className="inline-flex size-10 items-center justify-center border border-[#d8d5cc] text-[#4e4c46] hover:border-[#d73a2f] hover:text-[#d73a2f]"
            onClick={() => signOut({ redirectUrl: "/sign-in" })}
            title="Sign out"
            type="button"
          >
            <LogOut className="size-4" aria-hidden />
            <span className="sr-only">Sign out</span>
          </button>
        </div>

        <div className="grid gap-10 py-12 lg:grid-cols-[0.8fr_1.2fr] lg:gap-16 lg:py-20">
          <div>
            <p className="utility-label !text-[#d73a2f]">One last step</p>
            <h1 className="mt-4 text-4xl font-black leading-tight text-[#171714] sm:text-5xl">
              Set up your workspace.
            </h1>
            <p className="mt-5 max-w-md text-base leading-7 text-[#6d6b64]">
              Your workspace keeps your team, leads, calls, and knowledge together.
            </p>
          </div>

          <div className="border border-[#171714] bg-[#fffefa] p-6 sm:p-8">
            <AuthErrors messages={error ? [error] : []} />

            {userMemberships.data?.length ? (
              <section className={error ? "mt-6" : ""}>
                <p className="utility-label">Choose an existing workspace</p>
                <div className="mt-4 space-y-3">
                  {userMemberships.data.map((membership) => (
                    <button
                      className="flex min-h-14 w-full items-center justify-between border border-[#d8d5cc] px-4 text-left transition hover:border-[#d73a2f]"
                      disabled={isSubmitting}
                      key={membership.id}
                      onClick={() => activateWorkspace(membership.organization.id)}
                      type="button"
                    >
                      <span className="flex items-center gap-3 text-sm font-bold">
                        <Building2 className="size-4 text-[#d73a2f]" aria-hidden />
                        {membership.organization.name}
                      </span>
                      {isSubmitting ? <Loader2 className="size-4 animate-spin" aria-hidden /> : <ArrowRight className="size-4" aria-hidden />}
                    </button>
                  ))}
                </div>
                <div className="my-7 flex items-center gap-3"><span className="h-px flex-1 bg-[#d8d5cc]" /><span className="utility-label">or</span><span className="h-px flex-1 bg-[#d8d5cc]" /></div>
              </section>
            ) : null}

            <form action={createWorkspace} className="space-y-4">
              <div>
                <label className="text-sm font-bold text-[#34332f]" htmlFor="workspaceName">Workspace name</label>
                <input
                  className="mt-2 h-12 w-full border border-[#bdbab1] bg-[#fffefa] px-3 text-sm outline-none focus:border-[#d73a2f] focus:ring-2 focus:ring-[#d73a2f]/15"
                  id="workspaceName"
                  name="workspaceName"
                  placeholder="Your company name"
                  required
                  type="text"
                />
              </div>
              <button className="inline-flex h-12 w-full items-center justify-center gap-2 bg-[#171714] px-4 text-sm font-bold text-white hover:bg-[#d73a2f] disabled:opacity-60" disabled={isSubmitting} type="submit">
                {isSubmitting ? <Loader2 className="size-4 animate-spin" aria-hidden /> : null}
                Create workspace
              </button>
            </form>
          </div>
        </div>
      </div>
    </main>
  );
}
