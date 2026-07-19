"use client";

import { FormEvent, useMemo, useRef, useState } from "react";
import type { Route } from "next";
import { ArrowLeft, Loader2 } from "lucide-react";
import { useRouter } from "next/navigation";
import { useSignIn } from "@clerk/nextjs";
import { AuthErrors } from "@/components/auth/auth-errors";
import { AuthField } from "@/components/auth/auth-field";
import { navigateWithClerk } from "@/lib/clerk-navigation";

type PlatformSignInStep = "credentials" | "verification";
type VerificationStrategy = "email_code" | "phone_code" | "totp" | "backup_code";

const FINALIZATION_TIMEOUT_MS = 12_000;

function clerkErrorMessage(error: unknown) {
  if (error && typeof error === "object" && "errors" in error) {
    const errors = (error as { errors?: Array<{ longMessage?: string; message?: string }> }).errors;
    const message = errors?.[0]?.longMessage ?? errors?.[0]?.message;
    if (message) return message;
  }

  return error instanceof Error ? error.message : "Platform sign-in failed. Please try again.";
}

export function PlatformSignInForm() {
  const router = useRouter();
  const { signIn, errors, fetchStatus } = useSignIn();
  const finalizationTimer = useRef<ReturnType<typeof setTimeout> | null>(null);
  const [step, setStep] = useState<PlatformSignInStep>("credentials");
  const [strategy, setStrategy] = useState<VerificationStrategy | null>(null);
  const [safeIdentifier, setSafeIdentifier] = useState<string | null>(null);
  const [isFinalizing, setIsFinalizing] = useState(false);
  const [localError, setLocalError] = useState<string | null>(null);
  const isBusy = fetchStatus === "fetching" || isFinalizing;

  const globalErrors = useMemo(
    () => [localError, ...(errors.global ?? []).map((error) => error.message)].filter(Boolean) as string[],
    [errors.global, localError],
  );

  const stopFinalizing = (message: string) => {
    if (finalizationTimer.current) clearTimeout(finalizationTimer.current);
    finalizationTimer.current = null;
    setIsFinalizing(false);
    setLocalError(message);
  };

  const completePlatformSignIn = async () => {
    setIsFinalizing(true);
    finalizationTimer.current = setTimeout(() => {
      stopFinalizing(
        "Clerk could not activate this session. In Clerk Organization Settings, set membership to optional so platform accounts can sign in without an organization.",
      );
    }, FINALIZATION_TIMEOUT_MS);

    try {
      const result = await signIn.finalize({
        navigate: ({ session, decorateUrl }) => {
          if (session.currentTask) {
            navigateWithClerk(
              decorateUrl("/platform/sign-in?error=personal_accounts_required"),
              (url) => router.replace(url as Route),
            );
            return;
          }

          navigateWithClerk(
            decorateUrl("/platform"),
            (url) => router.replace(url as Route),
          );
        },
      });

      if (result.error) stopFinalizing(result.error.message);
    } catch (error) {
      stopFinalizing(clerkErrorMessage(error));
    }
  };

  const prepareVerification = async () => {
    const emailFactor = signIn.supportedSecondFactors.find(
      (factor) => factor.strategy === "email_code",
    );
    if (emailFactor) {
      const result = await signIn.mfa.sendEmailCode();
      if (result.error) throw result.error;
      setSafeIdentifier(emailFactor.safeIdentifier);
      setStrategy("email_code");
      setStep("verification");
      return;
    }

    const phoneFactor = signIn.supportedSecondFactors.find(
      (factor) => factor.strategy === "phone_code",
    );
    if (phoneFactor) {
      const result = await signIn.mfa.sendPhoneCode();
      if (result.error) throw result.error;
      setSafeIdentifier(phoneFactor.safeIdentifier);
      setStrategy("phone_code");
      setStep("verification");
      return;
    }

    if (signIn.supportedSecondFactors.some((factor) => factor.strategy === "totp")) {
      setStrategy("totp");
      setStep("verification");
      return;
    }

    if (signIn.supportedSecondFactors.some((factor) => factor.strategy === "backup_code")) {
      setStrategy("backup_code");
      setStep("verification");
      return;
    }

    throw new Error("No supported verification method is configured for this account.");
  };

  const handleCredentials = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setLocalError(null);
    const formData = new FormData(event.currentTarget);

    try {
      const result = await signIn.password({
        identifier: String(formData.get("identifier") ?? "").trim(),
        password: String(formData.get("password") ?? ""),
      });
      if (result.error) throw result.error;

      if (signIn.status === "complete") {
        await completePlatformSignIn();
        return;
      }
      if (signIn.status === "needs_client_trust" || signIn.status === "needs_second_factor") {
        await prepareVerification();
        return;
      }

      throw new Error(`Platform sign-in cannot continue from status: ${signIn.status}.`);
    } catch (error) {
      setLocalError(clerkErrorMessage(error));
    }
  };

  const handleVerification = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setLocalError(null);
    const code = String(new FormData(event.currentTarget).get("code") ?? "").trim();
    if (!strategy) return;

    try {
      const result = strategy === "email_code"
        ? await signIn.mfa.verifyEmailCode({ code })
        : strategy === "phone_code"
          ? await signIn.mfa.verifyPhoneCode({ code })
          : strategy === "totp"
            ? await signIn.mfa.verifyTOTP({ code })
            : await signIn.mfa.verifyBackupCode({ code });
      if (result.error) throw result.error;
      if (signIn.status !== "complete") {
        throw new Error(`Verification cannot continue from status: ${signIn.status}.`);
      }

      await completePlatformSignIn();
    } catch (error) {
      setLocalError(clerkErrorMessage(error));
    }
  };

  const resendCode = async () => {
    setLocalError(null);
    try {
      const result = strategy === "email_code"
        ? await signIn.mfa.sendEmailCode()
        : await signIn.mfa.sendPhoneCode();
      if (result.error) throw result.error;
    } catch (error) {
      setLocalError(clerkErrorMessage(error));
    }
  };

  const restart = async () => {
    if (finalizationTimer.current) clearTimeout(finalizationTimer.current);
    await signIn.reset();
    setStep("credentials");
    setStrategy(null);
    setSafeIdentifier(null);
    setIsFinalizing(false);
    setLocalError(null);
  };

  if (step === "verification") {
    const codeDelivery = strategy === "email_code" || strategy === "phone_code";
    const codeLabel = strategy === "totp"
      ? "Authenticator code"
      : strategy === "backup_code"
        ? "Backup code"
        : "Verification code";

    return (
      <form className="space-y-5" onSubmit={handleVerification}>
        <AuthErrors messages={globalErrors} />
        <p className="text-sm leading-6 text-[#6d6b64]">
          {codeDelivery
            ? `Enter the code sent to ${safeIdentifier ?? "your platform account"}.`
            : "Enter the code from your authenticator or recovery codes."}
        </p>
        <AuthField
          autoComplete="one-time-code"
          error={errors.fields.code?.message}
          id="platform-code"
          label={codeLabel}
          name="code"
          type="text"
        />
        <button
          className="inline-flex h-12 w-full items-center justify-center gap-2 bg-[#171714] px-4 text-sm font-bold text-white hover:bg-[#d73a2f] disabled:cursor-wait disabled:opacity-70"
          disabled={isBusy}
          type="submit"
        >
          {isBusy && <Loader2 className="size-4 animate-spin" aria-hidden />}
          {isFinalizing ? "Opening platform console" : "Verify and continue"}
        </button>
        <div className="flex items-center justify-between gap-4">
          <button
            className="inline-flex h-10 items-center gap-2 text-sm font-bold text-[#6d6b64] hover:text-[#171714]"
            disabled={isBusy}
            onClick={restart}
            type="button"
          >
            <ArrowLeft className="size-4" aria-hidden />
            Start again
          </button>
          {codeDelivery && (
            <button
              className="h-10 text-sm font-bold text-[#d73a2f] hover:text-[#b72c24]"
              disabled={isBusy}
              onClick={resendCode}
              type="button"
            >
              Send a new code
            </button>
          )}
        </div>
      </form>
    );
  }

  return (
    <form className="space-y-5" onSubmit={handleCredentials}>
      <AuthErrors messages={globalErrors} />
      <AuthField
        autoComplete="email"
        error={errors.fields.identifier?.message}
        id="platform-identifier"
        label="Platform email"
        name="identifier"
        type="email"
      />
      <AuthField
        autoComplete="current-password"
        error={errors.fields.password?.message}
        id="platform-password"
        label="Password"
        name="password"
        type="password"
      />
      <button
        className="inline-flex h-12 w-full items-center justify-center gap-2 bg-[#171714] px-4 text-sm font-bold text-white hover:bg-[#d73a2f] disabled:cursor-wait disabled:opacity-70"
        disabled={isBusy}
        type="submit"
      >
        {isBusy && <Loader2 className="size-4 animate-spin" aria-hidden />}
        Enter platform console
      </button>
    </form>
  );
}
