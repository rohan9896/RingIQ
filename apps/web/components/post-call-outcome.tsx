import type { PostCallOutcome as PostCallOutcomeData } from "@/lib/api-client";
import { callbackDisplay, outcomeDisplayState } from "@/lib/post-call-outcome";

const toneClasses = {
  neutral: "border-[#d8d5cc] bg-[#f7f6f1] text-[#4e4c46]",
  positive: "border-[#aeb6a7] bg-[#eef0ea] text-[#4d5b44]",
  warning: "border-[#d7b56d] bg-[#f7edd8] text-[#805111]",
  negative: "border-[#db9f98] bg-[#f6e9e6] text-[#8f221c]",
};

export function PostCallOutcome({
  callStatus,
  outcome,
  compact = false,
}: {
  callStatus: string;
  outcome: PostCallOutcomeData | null;
  compact?: boolean;
}) {
  const state = outcomeDisplayState(callStatus, outcome);
  const callback = outcome ? callbackDisplay(outcome) : null;
  const facts = outcome
    ? Object.entries(outcome.qualification_facts).filter(([, value]) => Boolean(value))
    : [];

  if (compact) {
    return <span className={`inline-flex border px-2 py-0.5 text-[11px] font-black capitalize ${toneClasses[state.tone]}`}>{state.label}</span>;
  }

  return (
    <section aria-label="Post-call outcome" className="space-y-4">
      <div className="flex flex-wrap items-center gap-2">
        <span className={`inline-flex border px-2.5 py-1 text-xs font-black capitalize ${toneClasses[state.tone]}`}>
          {state.label}
        </span>
        {outcome?.confidence != null && outcome.processing_status === "completed" ? (
          <span className="text-xs text-[#6d6b64]">{Math.round(outcome.confidence * 100)}% confidence</span>
        ) : null}
      </div>

      {outcome?.processing_status === "completed" ? (
        <>
          {outcome.summary ? <p className="text-sm leading-6 text-[#171714]">{outcome.summary}</p> : null}
          {outcome.rationale ? (
            <div><p className="utility-label">Reason</p><p className="mt-1 text-sm leading-6 text-[#4e4c46]">{outcome.rationale}</p></div>
          ) : null}
          {facts.length ? (
            <div>
              <p className="utility-label">Qualification facts</p>
              <dl className="mt-2 grid gap-2 sm:grid-cols-2">
                {facts.map(([key, value]) => (
                  <div className="border-l-2 border-[#d8d5cc] pl-3" key={key}>
                    <dt className="text-[11px] font-black uppercase text-[#6d6b64]">{key.replaceAll("_", " ")}</dt>
                    <dd className="mt-0.5 text-sm text-[#171714]">{value}</dd>
                  </div>
                ))}
              </dl>
            </div>
          ) : null}
          {callback ? (
            <div><p className="utility-label">Callback request</p><p className="mt-1 text-sm text-[#171714]">{callback}</p></div>
          ) : null}
          {outcome.evidence.length ? (
            <div>
              <p className="utility-label">Evidence</p>
              <div className="mt-2 space-y-2">
                {outcome.evidence.map((item, index) => (
                  <blockquote className="border-l-2 border-[#171714] pl-3 text-sm leading-6 text-[#4e4c46]" key={`${item.turn_index}-${index}`}>
                    <span className="mr-2 text-[11px] font-black uppercase text-[#6d6b64]">{item.speaker === "user" ? "Customer" : "Agent"} · turn {item.turn_index + 1}</span>
                    “{item.quote}”
                  </blockquote>
                ))}
              </div>
            </div>
          ) : null}
          {outcome.terminal_reason ? (
            <p className="text-xs text-[#6d6b64]">Call ended: {outcome.terminal_reason.replaceAll("_", " ")}</p>
          ) : null}
        </>
      ) : null}
    </section>
  );
}
