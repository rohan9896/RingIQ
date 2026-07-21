import { BrandMark } from "@/components/brand-mark";
import { PlatformInvitationForm } from "@/components/auth/platform-invitation-form";

type PlatformInvitationPageProps = {
  searchParams: Promise<{ __clerk_ticket?: string | string[] }>;
};

export default async function PlatformInvitationPage({
  searchParams,
}: PlatformInvitationPageProps) {
  const params = await searchParams;
  const ticket = Array.isArray(params.__clerk_ticket)
    ? params.__clerk_ticket[0] ?? null
    : params.__clerk_ticket ?? null;

  return (
    <main className="paper-grid min-h-screen bg-[#171714] px-5 py-8 text-white sm:px-10">
      <div className="mx-auto flex min-h-[calc(100vh-4rem)] max-w-6xl flex-col">
        <BrandMark inverse />
        <div className="grid flex-1 items-center gap-12 py-12 lg:grid-cols-[1fr_29rem]">
          <section className="max-w-xl">
            <p className="utility-label !text-[#e15a50]">Invitation only</p>
            <h1 className="mt-5 text-4xl font-black leading-tight sm:text-6xl">
              Join the RingIQ platform team.
            </h1>
            <p className="mt-6 max-w-lg text-base leading-7 text-white/60">
              Create a dedicated account for internal operations. Your access
              level comes from the invitation and cannot be changed here.
            </p>
          </section>

          <section className="border border-white/20 bg-[#fffefa] p-6 text-[#171714] sm:p-8">
            <p className="utility-label !text-[#d73a2f]">Platform account</p>
            <h2 className="mt-3 text-2xl font-black">Accept your invitation</h2>
            <p className="mb-7 mt-3 text-sm leading-6 text-[#6d6b64]">
              The invitation verifies your email. Add your name and choose a
              password to finish.
            </p>
            <PlatformInvitationForm ticket={ticket} />
          </section>
        </div>
        <p className="utility-label !text-white/35">
          Dedicated platform identity · No organization required
        </p>
      </div>
    </main>
  );
}
