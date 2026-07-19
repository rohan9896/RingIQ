"use client";

import Image from "next/image";
import { useRouter } from "next/navigation";
import { ChangeEvent, FormEvent, useEffect, useMemo, useRef, useState } from "react";
import {
  ArrowRight,
  Building2,
  ImagePlus,
  Loader2,
  LogOut,
  Trash2,
} from "lucide-react";
import { useClerk, useOrganizationList } from "@clerk/nextjs";
import { BrandMark } from "@/components/brand-mark";

const MAX_LOGO_SIZE = 10 * 1024 * 1024;

function getErrorMessage(error: unknown) {
  if (error && typeof error === "object" && "errors" in error) {
    const errors = (error as { errors?: Array<{ longMessage?: string; message?: string }> }).errors;
    const clerkMessage = errors?.[0]?.longMessage ?? errors?.[0]?.message;
    if (clerkMessage) return clerkMessage;
  }

  return error instanceof Error ? error.message : "Workspace setup failed. Please try again.";
}

export function WorkspaceSetup() {
  const router = useRouter();
  const { signOut } = useClerk();
  const { isLoaded, createOrganization, setActive, userMemberships } = useOrganizationList({
    userMemberships: { pageSize: 10 },
  });
  const logoInputRef = useRef<HTMLInputElement>(null);
  const [name, setName] = useState("");
  const [logo, setLogo] = useState<File | null>(null);
  const [pendingOrganizationId, setPendingOrganizationId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const logoPreview = useMemo(() => (logo ? URL.createObjectURL(logo) : null), [logo]);

  useEffect(() => {
    return () => {
      if (logoPreview) URL.revokeObjectURL(logoPreview);
    };
  }, [logoPreview]);

  const finishSetup = async (organizationId: string) => {
    if (!setActive) throw new Error("Clerk is still loading. Please try again.");
    await setActive({ organization: organizationId });
    router.replace("/dashboard");
    router.refresh();
  };

  const handleLogoChange = (event: ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    if (!file.type.startsWith("image/")) {
      setError("Choose an image file for the organization logo.");
      event.target.value = "";
      return;
    }
    if (file.size > MAX_LOGO_SIZE) {
      setError("The organization logo must be 10MB or smaller.");
      event.target.value = "";
      return;
    }

    setError(null);
    setLogo(file);
  };

  const removeLogo = () => {
    setLogo(null);
    if (logoInputRef.current) logoInputRef.current.value = "";
  };

  const handleCreate = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const organizationName = name.trim();
    if (!organizationName) {
      setError("Enter your organization name.");
      return;
    }
    if (!createOrganization) {
      setError("Clerk is still loading. Please try again.");
      return;
    }

    setError(null);
    setPendingOrganizationId("new");
    try {
      const organization = await createOrganization({ name: organizationName });
      if (logo) {
        try {
          await organization.setLogo({ file: logo });
        } catch (logoError) {
          console.warn("Organization created, but its logo could not be uploaded.", logoError);
        }
      }
      await finishSetup(organization.id);
    } catch (caught) {
      setError(getErrorMessage(caught));
      setPendingOrganizationId(null);
    }
  };

  const handleSelect = async (organizationId: string) => {
    setError(null);
    setPendingOrganizationId(organizationId);
    try {
      await finishSetup(organizationId);
    } catch (caught) {
      setError(getErrorMessage(caught));
      setPendingOrganizationId(null);
    }
  };

  const memberships = userMemberships.data ?? [];
  const isBusy = pendingOrganizationId !== null;

  return (
    <main className="paper-grid min-h-screen bg-[#f7f6f2] px-5 py-8 sm:px-8">
      <div className="mx-auto max-w-5xl">
        <div className="flex items-center justify-between border-b border-[#171714] pb-6">
          <BrandMark />
          <button
            className="inline-flex size-10 items-center justify-center border border-[#d8d5cc] text-[#4e4c46] hover:border-[#d73a2f] hover:text-[#d73a2f]"
            onClick={() => signOut({ redirectUrl: "/sign-in" })}
            title="Sign out"
            type="button"
          >
            <LogOut className="size-4" aria-hidden />
            <span className="sr-only">Sign out</span>
          </button>
        </div>

        <div className="grid gap-10 py-12 lg:grid-cols-[0.8fr_1.2fr] lg:gap-16 lg:py-20">
          <div>
            <p className="utility-label !text-[#d73a2f]">One last step</p>
            <h1 className="mt-4 text-4xl font-black leading-tight text-[#171714] sm:text-5xl">
              Set up your workspace.
            </h1>
            <p className="mt-5 max-w-md text-base leading-7 text-[#6d6b64]">
              Create your company workspace or continue with one you have joined.
            </p>
          </div>

          <section className="min-w-0 border border-[#171714] bg-[#fffefa] p-6 sm:p-8">
            {!isLoaded || userMemberships.isLoading ? (
              <div className="flex min-h-56 items-center justify-center gap-3 text-sm font-bold text-[#6d6b64]">
                <Loader2 className="size-5 animate-spin text-[#d73a2f]" aria-hidden />
                Loading your workspaces
              </div>
            ) : (
              <>
                {memberships.length > 0 && (
                  <div className="mb-8 border-b border-[#d8d5cc] pb-8">
                    <p className="utility-label">Your workspaces</p>
                    <div className="mt-4 grid gap-2">
                      {memberships.map((membership) => {
                        const organization = membership.organization;
                        const isSelecting = pendingOrganizationId === organization.id;
                        return (
                          <button
                            className="group flex min-h-16 w-full items-center gap-3 border border-[#d8d5cc] px-4 text-left hover:border-[#171714] disabled:cursor-wait disabled:opacity-60"
                            disabled={isBusy}
                            key={membership.id}
                            onClick={() => handleSelect(organization.id)}
                            type="button"
                          >
                            {organization.imageUrl ? (
                              <Image
                                alt=""
                                className="size-9 border border-[#d8d5cc] object-cover"
                                height={36}
                                src={organization.imageUrl}
                                unoptimized
                                width={36}
                              />
                            ) : (
                              <span className="grid size-9 shrink-0 place-items-center bg-[#f0eee8] text-[#6d6b64]">
                                <Building2 className="size-4" aria-hidden />
                              </span>
                            )}
                            <span className="min-w-0 flex-1 truncate text-sm font-bold text-[#171714]">
                              {organization.name}
                            </span>
                            {isSelecting ? (
                              <Loader2 className="size-4 animate-spin text-[#d73a2f]" aria-hidden />
                            ) : (
                              <ArrowRight
                                className="size-4 text-[#8a877f] group-hover:text-[#d73a2f]"
                                aria-hidden
                              />
                            )}
                          </button>
                        );
                      })}
                    </div>
                  </div>
                )}

                <form onSubmit={handleCreate}>
                  <div>
                    <p className="utility-label">
                      {memberships.length > 0 ? "Create another workspace" : "Organization details"}
                    </p>
                    <h2 className="mt-2 text-2xl font-black text-[#171714]">
                      Name your organization
                    </h2>
                  </div>

                  <div className="mt-7">
                    <label className="text-sm font-bold text-[#171714]" htmlFor="organization-logo">
                      Logo <span className="font-normal text-[#8a877f]">(optional)</span>
                    </label>
                    <div className="mt-3 flex flex-wrap items-center gap-4">
                      <div className="grid size-20 shrink-0 place-items-center overflow-hidden border border-[#d8d5cc] bg-[#f7f6f2]">
                        {logoPreview ? (
                          <Image
                            alt="Organization logo preview"
                            className="size-full object-cover"
                            height={80}
                            src={logoPreview}
                            unoptimized
                            width={80}
                          />
                        ) : (
                          <Building2 className="size-6 text-[#8a877f]" aria-hidden />
                        )}
                      </div>
                      <div>
                        <div className="flex gap-2">
                          <label
                            className="inline-flex h-10 cursor-pointer items-center gap-2 border border-[#171714] px-3 text-sm font-bold text-[#171714] hover:bg-[#f0eee8]"
                            htmlFor="organization-logo"
                          >
                            <ImagePlus className="size-4" aria-hidden />
                            {logo ? "Change" : "Upload"}
                          </label>
                          {logo && (
                            <button
                              className="inline-flex size-10 items-center justify-center border border-[#d8d5cc] text-[#6d6b64] hover:border-[#d73a2f] hover:text-[#d73a2f]"
                              onClick={removeLogo}
                              title="Remove logo"
                              type="button"
                            >
                              <Trash2 className="size-4" aria-hidden />
                              <span className="sr-only">Remove logo</span>
                            </button>
                          )}
                        </div>
                        <p className="mt-2 text-xs text-[#8a877f]">Square image, up to 10MB.</p>
                      </div>
                    </div>
                    <input
                      accept="image/*"
                      className="sr-only"
                      id="organization-logo"
                      onChange={handleLogoChange}
                      ref={logoInputRef}
                      type="file"
                    />
                  </div>

                  <div className="mt-6">
                    <label className="text-sm font-bold text-[#171714]" htmlFor="organization-name">
                      Organization name
                    </label>
                    <input
                      autoComplete="organization"
                      autoFocus
                      className="mt-2 h-12 w-full border border-[#bdbab1] bg-white px-4 text-base text-[#171714] outline-none placeholder:text-[#aaa79f] focus:border-[#171714] focus:ring-1 focus:ring-[#171714] disabled:opacity-60"
                      disabled={isBusy}
                      id="organization-name"
                      maxLength={100}
                      onChange={(event) => setName(event.target.value)}
                      placeholder="Acme Properties"
                      required
                      value={name}
                    />
                  </div>

                  {error && (
                    <p className="mt-4 border-l-2 border-[#d73a2f] bg-[#f6e9e6] px-4 py-3 text-sm text-[#8f221c]" role="alert">
                      {error}
                    </p>
                  )}

                  <button
                    className="mt-6 inline-flex h-12 w-full items-center justify-center gap-2 bg-[#171714] px-5 text-sm font-bold text-white hover:bg-[#d73a2f] disabled:cursor-wait disabled:bg-[#74716a]"
                    disabled={isBusy || !name.trim()}
                    type="submit"
                  >
                    {pendingOrganizationId === "new" ? (
                      <Loader2 className="size-4 animate-spin" aria-hidden />
                    ) : (
                      <ArrowRight className="size-4" aria-hidden />
                    )}
                    {pendingOrganizationId === "new" ? "Creating workspace" : "Create and continue"}
                  </button>
                </form>
              </>
            )}
          </section>
        </div>
      </div>
    </main>
  );
}
