import { auth } from "@clerk/nextjs/server";
import { redirect } from "next/navigation";
import { BrandMark } from "@/components/brand-mark";
import { SignInForm } from "@/components/auth/sign-in-form";

export default async function PlatformSignInPage() {
  const { userId, orgId } = await auth();

  if (userId) {
    if (orgId) redirect("/dashboard");
    redirect("/platform");
  }

  return (
    <main className="paper-grid min-h-screen bg-[#171714] px-5 py-8 text-white sm:px-10">
      <div className="mx-auto flex min-h-[calc(100vh-4rem)] max-w-6xl flex-col">
        <BrandMark inverse />
        <div className="grid flex-1 items-center gap-12 py-12 lg:grid-cols-[1fr_28rem]">
          <section className="max-w-xl">
            <p className="utility-label !text-[#e15a50]">RingIQ internal</p>
            <h1 className="mt-5 text-4xl font-black leading-tight sm:text-6xl">
              Platform operations console
            </h1>
            <p className="mt-6 max-w-lg text-base leading-7 text-white/60">
              Authorized RingIQ team members can manage platform operations from this private workspace.
            </p>
          </section>

          <section className="border border-white/20 bg-[#fffefa] p-6 text-[#171714] sm:p-8">
            <p className="utility-label !text-[#d73a2f]">Restricted access</p>
            <h2 className="mt-3 text-2xl font-black">Sign in to the platform</h2>
            <p className="mb-7 mt-3 text-sm leading-6 text-[#6d6b64]">
              Use your dedicated RingIQ platform account.
            </p>
            <SignInForm
              destination="/platform"
              organizationTaskDestination="/workspace/setup"
              submitLabel="Enter platform console"
            />
          </section>
        </div>
        <p className="utility-label !text-white/35">Access is invitation only</p>
      </div>
    </main>
  );
}
