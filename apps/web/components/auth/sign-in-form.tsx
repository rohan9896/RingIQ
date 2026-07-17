"use client";

import { useMemo, useState } from "react";
import { useRouter } from "next/navigation";
import { Loader2 } from "lucide-react";
import { useSignIn } from "@clerk/nextjs";
import { AuthErrors } from "@/components/auth/auth-errors";
import { AuthField } from "@/components/auth/auth-field";
import { navigateWithClerk } from "@/lib/clerk-navigation";

type VerificationStrategy = "email_code" | "phone_code" | "totp" | "backup_code";

export function SignInForm() {
  const router = useRouter();
  const { signIn, errors, fetchStatus } = useSignIn();
  const [localError, setLocalError] = useState<string | null>(null);
  const [verificationStrategy, setVerificationStrategy] =
    useState<VerificationStrategy | null>(null);
  const [safeIdentifier, setSafeIdentifier] = useState<string | null>(null);
  const isLoading = fetchStatus === "fetching";

  const globalErrors = useMemo(
    () =>
      [
        localError,
        ...(errors.global ?? []).map((error) => error.message),
      ].filter(Boolean) as string[],
    [errors.global, localError],
  );

  async function handleSubmit(formData: FormData) {
    setLocalError(null);

    const identifier = String(formData.get("identifier") ?? "").trim();
    const password = String(formData.get("password") ?? "");

    const { error } = await signIn.password({ identifier, password });
    if (error) {
      setLocalError(error.message);
      return;
    }

    if (signIn.status === "complete") {
      await finalizeSignIn();
      return;
    }

    if (
      signIn.status === "needs_client_trust" ||
      signIn.status === "needs_second_factor"
    ) {
      await prepareVerification();
      return;
    }

    setLocalError(`Sign-in could not continue from status: ${signIn.status}.`);
  }

  async function finalizeSignIn() {
    const result = await signIn.finalize({
      navigate: ({ session, decorateUrl }) => {
        const destination = session.currentTask?.key === "choose-organization"
          ? "/workspace/setup"
          : "/dashboard";
        return navigateWithClerk(decorateUrl(destination), router);
      },
    });
    if (result.error) setLocalError(result.error.message);
  }

  async function prepareVerification() {
    const emailFactor = signIn.supportedSecondFactors.find(
      (factor) => factor.strategy === "email_code",
    );
    if (emailFactor) {
      const { error } = await signIn.mfa.sendEmailCode();
      if (error) {
        setLocalError(error.message);
        return;
      }
      setSafeIdentifier(emailFactor.safeIdentifier);
      setVerificationStrategy("email_code");
      return;
    }

    const phoneFactor = signIn.supportedSecondFactors.find(
      (factor) => factor.strategy === "phone_code",
    );
    if (phoneFactor) {
      const { error } = await signIn.mfa.sendPhoneCode();
      if (error) {
        setLocalError(error.message);
        return;
      }
      setSafeIdentifier(phoneFactor.safeIdentifier);
      setVerificationStrategy("phone_code");
      return;
    }

    if (signIn.supportedSecondFactors.some((factor) => factor.strategy === "totp")) {
      setVerificationStrategy("totp");
      return;
    }

    if (signIn.supportedSecondFactors.some((factor) => factor.strategy === "backup_code")) {
      setVerificationStrategy("backup_code");
      return;
    }

    setLocalError("No supported verification method is available for this account.");
  }

  async function handleVerification(formData: FormData) {
    setLocalError(null);
    const code = String(formData.get("code") ?? "").trim();
    if (!verificationStrategy) return;

    const result = verificationStrategy === "email_code"
      ? await signIn.mfa.verifyEmailCode({ code })
      : verificationStrategy === "phone_code"
        ? await signIn.mfa.verifyPhoneCode({ code })
        : verificationStrategy === "totp"
          ? await signIn.mfa.verifyTOTP({ code })
          : await signIn.mfa.verifyBackupCode({ code });

    if (result.error) {
      setLocalError(result.error.message);
      return;
    }

    if (signIn.status === "complete") {
      await finalizeSignIn();
      return;
    }

    setLocalError(`Verification could not continue from status: ${signIn.status}.`);
  }

  async function resendCode() {
    setLocalError(null);
    const result = verificationStrategy === "email_code"
      ? await signIn.mfa.sendEmailCode()
      : await signIn.mfa.sendPhoneCode();
    if (result.error) setLocalError(result.error.message);
  }

  if (verificationStrategy) {
    const isCodeDelivery =
      verificationStrategy === "email_code" || verificationStrategy === "phone_code";
    const label = verificationStrategy === "totp"
      ? "Authenticator code"
      : verificationStrategy === "backup_code"
        ? "Backup code"
        : "Verification code";

    return (
      <form action={handleVerification} className="space-y-5">
        <AuthErrors messages={globalErrors} />
        <p className="text-sm leading-6 text-[#6d6b64]">
          {isCodeDelivery
            ? `Enter the code sent to ${safeIdentifier ?? "your account"}.`
            : "Enter the code from your authenticator or recovery codes."}
        </p>
        <AuthField
          id="code"
          label={label}
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
          Verify and continue
        </button>
        {isCodeDelivery ? (
          <button
            className="h-10 text-sm font-bold text-[#d73a2f] hover:text-[#b72c24]"
            disabled={isLoading}
            onClick={resendCode}
            type="button"
          >
            Send a new code
          </button>
        ) : null}
      </form>
    );
  }

  return (
    <form action={handleSubmit} className="space-y-5">
      <AuthErrors messages={globalErrors} />
      <AuthField
        id="identifier"
        label="Email"
        name="identifier"
        type="email"
        autoComplete="email"
        error={errors.fields.identifier?.message}
      />
      <AuthField
        id="password"
        label="Password"
        name="password"
        type="password"
        autoComplete="current-password"
        error={errors.fields.password?.message}
      />
      <button
        className="inline-flex h-12 w-full items-center justify-center gap-2 bg-[#171714] px-4 text-sm font-bold text-white transition hover:bg-[#d73a2f] disabled:cursor-not-allowed disabled:opacity-70"
        disabled={isLoading}
        type="submit"
      >
        {isLoading ? <Loader2 className="size-4 animate-spin" aria-hidden /> : null}
        Sign in
      </button>
    </form>
  );
}
