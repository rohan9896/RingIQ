import Link from "next/link";
import { ArrowUpRight, Check, PhoneCall } from "lucide-react";
import { BrandMark } from "@/components/brand-mark";

export default function HomePage() {
  const bars = [18, 34, 54, 30, 68, 42, 78, 50, 88, 46, 70, 34, 58, 26, 44, 18];

  return (
    <main className="min-h-screen bg-[#f7f6f2] text-[#171714]">
      <header className="border-b border-[#171714]">
        <div className="mx-auto flex h-20 max-w-[90rem] items-center justify-between px-5 sm:px-8 lg:px-12">
          <BrandMark />
          <nav className="flex items-center gap-2 sm:gap-5" aria-label="Main navigation">
            <Link className="hidden text-sm font-semibold hover:text-[#d73a2f] sm:block" href="/sign-in">
              Sign in
            </Link>
            <Link className="inline-flex h-10 items-center gap-2 bg-[#171714] px-4 text-sm font-bold text-white transition hover:bg-[#d73a2f]" href="/sign-up">
              Get started <ArrowUpRight className="size-4" aria-hidden />
            </Link>
          </nav>
        </div>
      </header>

      <section className="paper-grid overflow-hidden border-b border-[#171714]">
        <div className="mx-auto grid min-h-[calc(100vh-8rem)] max-w-[90rem] lg:grid-cols-[1.08fr_0.92fr]">
          <div className="flex flex-col justify-between border-[#171714] px-5 py-10 sm:px-8 sm:py-14 lg:border-r lg:px-12 lg:py-16">
            <div className="flex items-center gap-3">
              <span className="h-px w-10 bg-[#d73a2f]" />
              <span className="utility-label !text-[#d73a2f]">AI conversations, made clear</span>
            </div>
            <div className="my-16 max-w-4xl lg:my-10">
              <h1 className="max-w-3xl text-[clamp(3.5rem,8vw,7.5rem)] font-black leading-[0.9]">
                Every lead,
                <span className="block text-[#d73a2f]">heard.</span>
              </h1>
              <p className="mt-8 max-w-xl text-lg leading-8 text-[#55534d] sm:text-xl">
                RingIQ speaks with your leads in multilingual Indian languages,
                understands intent, and gives your team a focused follow-up list.
              </p>
            </div>
            <div className="flex flex-col gap-5 border-t border-[#171714] pt-6 sm:flex-row sm:items-center sm:justify-between">
              <Link className="inline-flex h-12 w-fit items-center gap-3 bg-[#d73a2f] px-5 text-sm font-bold text-white transition hover:bg-[#b72c24]" href="/sign-up">
                Start with RingIQ <ArrowUpRight className="size-4" aria-hidden />
              </Link>
              <p className="utility-label max-w-[15rem] leading-5">Upload leads · Start calls · Follow up</p>
            </div>
          </div>

          <div className="relative flex min-h-[32rem] items-center justify-center bg-[#171714] px-5 py-16 text-white sm:px-10">
            <div className="absolute right-6 top-6 text-right">
              <p className="text-5xl font-black text-[#d73a2f]">声</p>
              <p className="utility-label !text-white/45">Voice / intent</p>
            </div>
            <div className="w-full max-w-lg">
              <div className="mb-5 flex items-center justify-between border-b border-white/20 pb-4">
                <div className="flex items-center gap-3">
                  <span className="grid size-10 place-items-center bg-[#d73a2f]"><PhoneCall className="size-5" aria-hidden /></span>
                  <div><p className="text-sm font-bold">Conversation in progress</p><p className="utility-label !text-white/45">Indian languages</p></div>
                </div>
                <span className="size-2 bg-[#d73a2f]" aria-label="Live" />
              </div>
              <div className="flex h-40 items-center justify-center gap-2 border-y border-white/15" aria-hidden>
                {bars.map((height, index) => (
                  <span key={`${height}-${index}`} className="voice-line w-2 bg-[#d73a2f]" style={{ height }} />
                ))}
              </div>
              <div className="mt-6 grid grid-cols-2 border border-white/20">
                <div className="border-r border-white/20 p-4"><p className="utility-label !text-white/45">Intent</p><p className="mt-2 text-lg font-bold">Interested</p></div>
                <div className="p-4"><p className="utility-label !text-white/45">Next step</p><p className="mt-2 text-lg font-bold">Follow up</p></div>
              </div>
              <div className="mt-8 space-y-3 text-sm text-white/75">
                {["Natural multilingual calls", "Answers grounded in your knowledge", "Clear outcomes for your team"].map((item) => (
                  <div className="flex items-center gap-3" key={item}><Check className="size-4 text-[#d73a2f]" aria-hidden />{item}</div>
                ))}
              </div>
            </div>
          </div>
        </div>
      </section>

      <section className="border-b border-[#171714] bg-[#fffefa]">
        <div className="mx-auto grid max-w-[90rem] lg:grid-cols-[0.45fr_1.55fr]">
          <div className="border-b border-[#171714] p-6 sm:p-8 lg:border-b-0 lg:border-r lg:p-12">
            <p className="utility-label !text-[#d73a2f]">One clear flow</p>
            <h2 className="mt-3 text-3xl font-black">From list to next step.</h2>
          </div>
          <div className="grid sm:grid-cols-3">
            {[
              ["01", "Add leads", "Bring in the people your team needs to reach."],
              ["02", "Start conversations", "RingIQ calls naturally in multilingual Indian languages."],
              ["03", "Focus follow-up", "See who is interested and what they need next."],
            ].map(([number, title, copy]) => (
              <div className="border-b border-[#d8d5cc] p-6 last:border-b-0 sm:border-b-0 sm:border-r sm:last:border-r-0 sm:p-8" key={number}>
                <p className="utility-label !text-[#d73a2f]">{number}</p>
                <h3 className="mt-8 text-lg font-black">{title}</h3>
                <p className="mt-3 text-sm leading-6 text-[#6d6b64]">{copy}</p>
              </div>
            ))}
          </div>
        </div>
      </section>
    </main>
  );
}
