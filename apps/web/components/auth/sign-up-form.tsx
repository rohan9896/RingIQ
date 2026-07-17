"use client";

import { useMemo, useState } from "react";
import { useRouter } from "next/navigation";
import { Loader2 } from "lucide-react";
import { useSignUp } from "@clerk/nextjs";
import { AuthErrors } from "@/components/auth/auth-errors";
import { AuthField } from "@/components/auth/auth-field";
import { navigateWithClerk } from "@/lib/clerk-navigation";

export function SignUpForm() {
  const router = useRouter();
  const { signUp, errors, fetchStatus } = useSignUp();
  const [localError, setLocalError] = useState<string | null>(null);
  const isLoading = fetchStatus === "fetching";
  const needsEmailCode =
    signUp.status === "missing_requirements" &&
    signUp.unverifiedFields.includes("email_address") &&
    signUp.missingFields.length === 0;

  const globalErrors = useMemo(
    () =>
      [
        localError,
        ...(errors.global ?? []).map((error) => error.message),
      ].filter(Boolean) as string[],
    [errors.global, localError],
  );

  async function handleCreate(formData: FormData) {
    setLocalError(null);

    const firstName = String(formData.get("firstName") ?? "").trim();
    const lastName = String(formData.get("lastName") ?? "").trim();
    const emailAddress = String(formData.get("emailAddress") ?? "").trim();
    const password = String(formData.get("password") ?? "");

    const { error } = await signUp.password({
      emailAddress,
      password,
      firstName,
      lastName,
    });

    if (error) {
      setLocalError(error.message);
      return;
    }

    if (signUp.status === "complete") {
      await finalize();
      return;
    }

    if (signUp.unverifiedFields.includes("email_address")) {
      const result = await signUp.verifications.sendEmailCode();
      if (result.error) {
        setLocalError(result.error.message);
      }
    }
  }

  async function handleVerify(formData: FormData) {
    setLocalError(null);

    const code = String(formData.get("code") ?? "").trim();
    const { error } = await signUp.verifications.verifyEmailCode({ code });
    if (error) {
      setLocalError(error.message);
      return;
    }

    if (signUp.status === "complete") {
      await finalize();
      return;
    }

    setLocalError("Email verified, but sign-up still needs another step.");
  }

  async function finalize() {
    const result = await signUp.finalize({
      navigate: ({ session, decorateUrl }) => {
        const destination = session.currentTask?.key === "choose-organization"
          ? "/workspace/setup"
          : "/dashboard";
        return navigateWithClerk(decorateUrl(destination), router);
      },
    });
    if (result.error) {
      setLocalError(result.error.message);
    }
  }

  if (needsEmailCode) {
    return (
      <form action={handleVerify} className="space-y-5">
        <AuthErrors messages={globalErrors} />
        <AuthField
          id="code"
          label="Verification code"
          name="code"
          type="text"
          autoComplete="one-time-code"
          error={errors.fields.code?.message}
        />
        <button
          className="inline-flex h-12 w-full items-center justify-center gap-2 bg-[#171714] px-4 text-sm font-bold text-white transition hover:bg-[#d73a2f] disabled:cursor-not-allowed disabled:opacity-70"
          disabled={isLoading}
          type="submit"
        >
          {isLoading ? <Loader2 className="size-4 animate-spin" aria-hidden /> : null}
          Verify email
        </button>
        <button
          className="h-10 text-sm font-bold text-[#d73a2f] hover:text-[#b72c24]"
          disabled={isLoading}
          onClick={() => signUp.verifications.sendEmailCode()}
          type="button"
        >
          Send a new code
        </button>
      </form>
    );
  }

  return (
    <form action={handleCreate} className="space-y-5">
      <AuthErrors messages={globalErrors} />
      <div className="grid gap-4 sm:grid-cols-2">
        <AuthField
          id="firstName"
          label="First name"
          name="firstName"
          type="text"
          autoComplete="given-name"
          error={errors.fields.firstName?.message}
        />
        <AuthField
          id="lastName"
          label="Last name"
          name="lastName"
          type="text"
          autoComplete="family-name"
          error={errors.fields.lastName?.message}
        />
      </div>
      <AuthField
        id="emailAddress"
        label="Work email"
        name="emailAddress"
        type="email"
        autoComplete="email"
        error={errors.fields.emailAddress?.message}
      />
      <AuthField
        id="password"
        label="Password"
        name="password"
        type="password"
        autoComplete="new-password"
        error={errors.fields.password?.message}
      />
      <div id="clerk-captcha" />
      <button
        className="inline-flex h-12 w-full items-center justify-center gap-2 bg-[#171714] px-4 text-sm font-bold text-white transition hover:bg-[#d73a2f] disabled:cursor-not-allowed disabled:opacity-70"
        disabled={isLoading}
        type="submit"
      >
        {isLoading ? <Loader2 className="size-4 animate-spin" aria-hidden /> : null}
        Create account
      </button>
    </form>
  );
}
