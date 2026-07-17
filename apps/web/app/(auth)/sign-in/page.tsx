import Link from "next/link";
import { auth } from "@clerk/nextjs/server";
import { redirect } from "next/navigation";
import { SignInForm } from "@/components/auth/sign-in-form";

export default async function SignInPage() {
  const { userId } = await auth();

  if (userId) {
    redirect("/dashboard");
  }

  return (
    <div className="w-full max-w-[27rem]">
      <div className="mb-8">
        <p className="utility-label !text-[#d73a2f]">Welcome back</p>
        <h2 className="mt-3 text-3xl font-black text-[#171714] sm:text-4xl">
          Continue your conversations.
        </h2>
        <p className="mt-4 text-sm leading-6 text-[#6d6b64]">
          Use your work email and password to continue.
        </p>
      </div>
      <SignInForm />
      <p className="mt-7 border-t border-[#d8d5cc] pt-5 text-sm text-[#6d6b64]">
        New to RingIQ?{" "}
        <Link className="font-bold text-[#d73a2f] hover:text-[#b72c24]" href="/sign-up">
          Create an account
        </Link>
      </p>
    </div>
  );
}
