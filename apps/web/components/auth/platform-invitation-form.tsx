"use client";

import { FormEvent, useMemo, useState } from "react";
import type { Route } from "next";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { ArrowRight, Loader2, LogOut, ShieldAlert } from "lucide-react";
import { useAuth, useClerk, useSignUp } from "@clerk/nextjs";
import { AuthErrors } from "@/components/auth/auth-errors";
import { AuthField } from "@/components/auth/auth-field";
import { completePlatformOnboarding } from "@/lib/api-client";
import { navigateWithClerk } from "@/lib/clerk-navigation";

type TicketState = "ready" | "invalid";

function clerkErrorMessage(error: unknown) {
  if (error && typeof error === "object" && "errors" in error) {
    const errors = (error as {
      errors?: Array<{ longMessage?: string; message?: string }>;
    }).errors;
    const message = errors?.[0]?.longMessage ?? errors?.[0]?.message;
    if (message) return platformInvitationErrorMessage(message);
  }

  return error instanceof Error
    ? platformInvitationErrorMessage(error.message)
    : "This invitation could not be accepted.";
}

function platformInvitationErrorMessage(message: string) {
  const messages: Record<string, string> = {
    platform_invitation_invalid:
      "This platform invitation is invalid, expired, revoked, or already belongs to another account.",
    platform_identity_conflict:
      "This email already belongs to a RingIQ identity. Use the dedicated account named in the invitation.",
    platform_identity_has_active_organization:
      "Platform invitations must be accepted with an account that has no active organization.",
    clerk_directory_unavailable:
      "Clerk is temporarily unavailable. Your invitation was not reassigned; please try again.",
    platform_identity_unavailable:
      "Platform onboarding is temporarily unavailable. Please try again.",
  };
  return messages[message] ?? message;
}

export function PlatformInvitationForm({ ticket }: { ticket: string | null }) {
  const router = useRouter();
  const { getToken, isLoaded: isAuthLoaded, isSignedIn } = useAuth();
  const { signOut } = useClerk();
  const { signUp, errors, fetchStatus } = useSignUp();
  const ticketState: TicketState = ticket ? "ready" : "invalid";
  const [localError, setLocalError] = useState<string | null>(
    ticket ? null : "This platform invitation link is missing its ticket.",
  );
  const [isCompleting, setIsCompleting] = useState(false);
  const isBusy = fetchStatus === "fetching" || isCompleting;

  const globalErrors = useMemo(
    () =>
      [localError, ...(errors.global ?? []).map((error) => error.message)].filter(
        Boolean,
      ) as string[],
    [errors.global, localError],
  );

  async function finalizeAndProvision() {
    setIsCompleting(true);
    try {
      const result = await signUp.finalize({
        navigate: async ({ session, decorateUrl }) => {
          if (session.currentTask) {
            throw new Error(
              "This platform account cannot be activated while an organization task is pending.",
            );
          }
          const token = await session.getToken();
          if (!token) throw new Error("No active session token is available.");
          await completePlatformOnboarding(token);
          navigateWithClerk(
            decorateUrl("/platform"),
            (url) => router.replace(url as Route),
          );
        },
      });
      if (result.error) throw result.error;
    } catch (caught) {
      setLocalError(clerkErrorMessage(caught));
      setIsCompleting(false);
    }
  }

  async function handleAccept(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setLocalError(null);
    const formData = new FormData(event.currentTarget);

    try {
      if (!ticket) throw new Error("This platform invitation link is missing its ticket.");
      const result = await signUp.create({
        strategy: "ticket",
        ticket,
        password: String(formData.get("password") ?? ""),
        firstName: String(formData.get("firstName") ?? "").trim(),
        lastName: String(formData.get("lastName") ?? "").trim(),
      });
      if (result.error) throw result.error;
      if (signUp.status !== "complete") {
        throw new Error(
          "The invitation is valid, but Clerk still requires another account field.",
        );
      }
      await finalizeAndProvision();
    } catch (caught) {
      setLocalError(clerkErrorMessage(caught));
    }
  }

  async function retryProvisioning() {
    setLocalError(null);
    setIsCompleting(true);
    try {
      const token = await getToken();
      if (!token) throw new Error("No active session token is available.");
      await completePlatformOnboarding(token);
      router.replace("/platform");
      router.refresh();
    } catch (caught) {
      setLocalError(clerkErrorMessage(caught));
      setIsCompleting(false);
    }
  }

  if (!isAuthLoaded) {
    return (
      <div className="flex min-h-56 items-center justify-center gap-3 text-sm font-bold text-[#6d6b64]">
        <Loader2 className="size-5 animate-spin text-[#d73a2f]" aria-hidden />
        Checking your invitation
      </div>
    );
  }

  if (isSignedIn) {
    return (
      <div>
        <AuthErrors messages={globalErrors} />
        <div className="border-l-2 border-[#d73a2f] bg-[#f6e9e6] p-4 text-sm leading-6 text-[#8f221c]">
          <div className="flex gap-3">
            <ShieldAlert className="mt-1 size-4 shrink-0" aria-hidden />
            <p>
              {ticket
                ? "Your Clerk account is active. Finish RingIQ provisioning with this invitation, or sign out to use another account."
                : "Sign out before accepting an invitation. Platform and tenant access must use separate Clerk accounts."}
            </p>
          </div>
        </div>
        {ticket ? (
          <button
            className="mt-6 inline-flex h-11 w-full items-center justify-center gap-2 bg-[#171714] px-4 text-sm font-bold text-white hover:bg-[#d73a2f] disabled:cursor-wait disabled:opacity-70"
            disabled={isCompleting}
            onClick={() => void retryProvisioning()}
            type="button"
          >
            {isCompleting ? (
              <Loader2 className="size-4 animate-spin" aria-hidden />
            ) : (
              <ArrowRight className="size-4" aria-hidden />
            )}
            Finish platform onboarding
          </button>
        ) : null}
        <button
          className="mt-3 inline-flex h-11 w-full items-center justify-center gap-2 border border-[#171714] px-4 text-sm font-bold text-[#171714] hover:bg-[#f0eee8]"
          onClick={() => signOut({ redirectUrl: window.location.href })}
          type="button"
        >
          <LogOut className="size-4" aria-hidden /> Sign out and use another account
        </button>
      </div>
    );
  }

  if (ticketState === "invalid") {
    return (
      <div>
        <AuthErrors messages={globalErrors} />
        <p className="mt-5 text-sm leading-6 text-[#6d6b64]">
          Invitation links are single-use and expire. Ask a platform super admin
          to send a replacement.
        </p>
        <Link
          className="mt-6 inline-flex h-11 items-center gap-2 border border-[#171714] px-4 text-sm font-bold text-[#171714] hover:bg-[#f0eee8]"
          href="/platform/sign-in"
        >
          Platform sign in <ArrowRight className="size-4" aria-hidden />
        </Link>
      </div>
    );
  }

  return (
    <form className="space-y-5" onSubmit={handleAccept}>
      <AuthErrors messages={globalErrors} />
      <div className="grid gap-4 sm:grid-cols-2">
        <AuthField
          autoComplete="given-name"
          error={errors.fields.firstName?.message}
          id="platform-first-name"
          label="First name"
          name="firstName"
          type="text"
        />
        <AuthField
          autoComplete="family-name"
          error={errors.fields.lastName?.message}
          id="platform-last-name"
          label="Last name"
          name="lastName"
          type="text"
        />
      </div>
      <AuthField
        autoComplete="new-password"
        error={errors.fields.password?.message}
        id="platform-password"
        label="Create password"
        name="password"
        type="password"
      />
      <div id="clerk-captcha" />
      <button
        className="inline-flex h-12 w-full items-center justify-center gap-2 bg-[#171714] px-4 text-sm font-bold text-white hover:bg-[#d73a2f] disabled:cursor-wait disabled:opacity-70"
        disabled={isBusy}
        type="submit"
      >
        {isBusy ? (
          <Loader2 className="size-4 animate-spin" aria-hidden />
        ) : (
          <ArrowRight className="size-4" aria-hidden />
        )}
        {isCompleting ? "Opening platform console" : "Accept invitation"}
      </button>
    </form>
  );
}
