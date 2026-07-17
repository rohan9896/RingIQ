import { Activity, Building2, FileQuestion, ShieldCheck, Users } from "lucide-react";

const capabilities = [
  { label: "Organizations", detail: "Lifecycle and access status", icon: Building2 },
  { label: "Organization users", detail: "Membership and account status", icon: Users },
  { label: "Starter templates", detail: "Category onboarding guidance", icon: FileQuestion },
  { label: "Operational health", detail: "Calls, queues, providers and cost", icon: Activity },
];

export default function PlatformHomePage() {
  return (
    <div className="mx-auto max-w-6xl">
      <div className="border-b border-[#171714] pb-7">
        <p className="utility-label !text-[#d73a2f]">Platform overview</p>
        <div className="mt-3 flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
          <div>
            <h1 className="text-3xl font-black text-[#171714] sm:text-4xl">
              Operations workspace
            </h1>
            <p className="mt-3 max-w-2xl text-sm leading-6 text-[#6d6b64]">
              Platform controls and aggregate service visibility for the RingIQ team.
            </p>
          </div>
          <div className="inline-flex h-10 items-center gap-2 border border-[#aeb6a7] bg-[#eef0ea] px-3 text-sm font-bold text-[#4d5b44]">
            <ShieldCheck className="size-4" aria-hidden />
            Privacy boundary active
          </div>
        </div>
      </div>

      <section className="grid gap-px border border-[#171714] bg-[#171714] sm:grid-cols-2 lg:grid-cols-4">
        {capabilities.map((item) => (
          <article className="min-h-44 bg-[#fffefa] p-5" key={item.label}>
            <item.icon className="size-5 text-[#2f4e6f]" aria-hidden />
            <h2 className="mt-8 text-base font-black text-[#171714]">{item.label}</h2>
            <p className="mt-2 text-sm leading-5 text-[#6d6b64]">{item.detail}</p>
          </article>
        ))}
      </section>

      <section className="mt-8 grid gap-6 lg:grid-cols-[1.35fr_0.65fr]">
        <div className="border border-[#d8d5cc] bg-[#fffefa] p-6">
          <p className="utility-label !text-[#2f4e6f]">Service pulse</p>
          <div className="mt-6 grid gap-5 sm:grid-cols-3">
            {["Call activity", "Queue state", "Provider health"].map((label) => (
              <div className="border-l-2 border-[#d8d5cc] pl-4" key={label}>
                <p className="text-sm text-[#6d6b64]">{label}</p>
                <p className="mt-2 text-xl font-black text-[#171714]">No data yet</p>
              </div>
            ))}
          </div>
        </div>
        <div className="border border-[#d8d5cc] bg-[#fffefa] p-6">
          <p className="utility-label !text-[#9a6517]">Data boundary</p>
          <p className="mt-4 text-sm leading-6 text-[#4e4c46]">
            Lead records, private knowledge bases, transcripts and recordings remain unavailable in this console.
          </p>
        </div>
      </section>
    </div>
  );
}
