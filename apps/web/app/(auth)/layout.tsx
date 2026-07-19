import { BrandMark } from "@/components/brand-mark";

export default function AuthLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <main className="grid min-h-screen grid-cols-1 bg-[#f7f6f2] lg:grid-cols-[0.92fr_1.08fr]">
      <section className="paper-grid relative flex min-h-[23rem] flex-col justify-between overflow-hidden border-b border-[#171714] bg-[#171714] px-6 py-6 text-white sm:px-10 lg:min-h-screen lg:border-b-0 lg:border-r">
        <BrandMark inverse />
        <div className="relative max-w-xl py-14">
          <p className="utility-label mb-5 !text-[#e15a50]">Conversation intelligence</p>
          <h1 className="text-4xl font-black leading-[1.05] sm:text-6xl">
            Turn every call into a clear next step.
          </h1>
          <div className="mt-10 flex h-20 items-center gap-2 border-y border-white/20" aria-hidden>
            {[24, 46, 32, 62, 40, 72, 36, 56, 28, 44].map((height, index) => (
              <span key={`${height}-${index}`} className="voice-line w-2 bg-[#d73a2f]" style={{ height }} />
            ))}
          </div>
          <p className="mt-8 max-w-lg text-base leading-7 text-white/65">
            Natural AI conversations in multilingual Indian languages, with the outcomes your team needs to follow up well.
          </p>
        </div>
        <p className="utility-label !text-white/40">RingIQ / Voice that listens</p>
      </section>
      <section className="flex min-h-[42rem] items-center justify-center px-5 py-12 sm:px-10 lg:min-h-screen">
        {children}
      </section>
    </main>
  );
}
