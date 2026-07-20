import type { PostCallOutcome } from "@/lib/api-client";

const terminalStatuses = new Set([
  "completed",
  "unanswered",
  "busy",
  "invalid_number",
  "failed",
  "cancelled",
]);

export type OutcomeDisplayState = {
  label: string;
  tone: "neutral" | "positive" | "warning" | "negative";
};

export function outcomeDisplayState(
  callStatus: string,
  outcome: PostCallOutcome | null,
): OutcomeDisplayState {
  if (!outcome) {
    return terminalStatuses.has(callStatus)
      ? { label: "Outcome not available", tone: "neutral" }
      : { label: "Awaiting call completion", tone: "neutral" };
  }
  if (outcome.processing_status === "pending" || outcome.processing_status === "processing") {
    return { label: "Analyzing call", tone: "neutral" };
  }
  if (outcome.processing_status === "failed") {
    return { label: "Outcome unavailable", tone: "negative" };
  }
  if (outcome.label === "needs_review") {
    return { label: "Needs review", tone: "warning" };
  }
  if (outcome.label) {
    return {
      label: outcome.label.replaceAll("_", " "),
      tone: ["hot", "warm", "callback_requested"].includes(outcome.label)
        ? "positive"
        : "neutral",
    };
  }
  return { label: "Outcome not available", tone: "neutral" };
}

export function callbackDisplay(outcome: PostCallOutcome): string | null {
  if (!outcome.callback_original_phrase) return null;
  if (!outcome.callback_at) {
    return `${outcome.callback_original_phrase} · Time not specified${
      outcome.callback_timezone ? ` · ${outcome.callback_timezone}` : ""
    }`;
  }
  const callbackDate = new Date(outcome.callback_at);
  let formattedCallback = callbackDate.toLocaleString();
  if (outcome.callback_timezone) {
    try {
      formattedCallback = new Intl.DateTimeFormat(undefined, {
        dateStyle: "medium",
        timeStyle: "short",
        timeZone: outcome.callback_timezone,
      }).format(callbackDate);
    } catch {
      // Fall back to the browser locale if a legacy timezone value is invalid.
    }
  }
  return `${outcome.callback_original_phrase} · ${formattedCallback}${
    outcome.callback_timezone ? ` · ${outcome.callback_timezone}` : ""
  }`;
}
