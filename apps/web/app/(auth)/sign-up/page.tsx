import Link from "next/link";
import { auth } from "@clerk/nextjs/server";
import { redirect } from "next/navigation";
import { SignUpForm } from "@/components/auth/sign-up-form";

export default async function SignUpPage() {
  const { userId } = await auth();

  if (userId) {
    redirect("/dashboard");
  }

  return (
    <div className="w-full max-w-[29rem]">
      <div className="mb-8">
        <p className="utility-label !text-[#d73a2f]">Begin with RingIQ</p>
        <h2 className="mt-3 text-3xl font-black text-[#171714] sm:text-4xl">
          Start better conversations.
        </h2>
        <p className="mt-4 text-sm leading-6 text-[#6d6b64]">
          Create your account. We will verify your email before you continue.
        </p>
      </div>
      <SignUpForm />
      <p className="mt-7 border-t border-[#d8d5cc] pt-5 text-sm text-[#6d6b64]">
        Already have an account?{" "}
        <Link className="font-bold text-[#d73a2f] hover:text-[#b72c24]" href="/sign-in">
          Sign in
        </Link>
      </p>
    </div>
  );
}
