"use client";

import { FormEvent, useCallback, useEffect, useState } from "react";
import {
  ArrowRight,
  Loader2,
  MailPlus,
  RefreshCw,
  ShieldAlert,
  UserRoundCheck,
  X,
} from "lucide-react";
import { useAuth } from "@clerk/nextjs";
import {
  createPlatformUserInvitation,
  fetchPlatformIdentity,
  fetchPlatformUserInvitations,
  fetchPlatformUsers,
  revokePlatformUserInvitation,
  type PlatformManagedUser,
  type PlatformRole,
  type PlatformUserInvitation,
} from "@/lib/api-client";

const roleLabels: Record<PlatformRole, string> = {
  platform_super_admin: "Super admin",
  platform_operations: "Operations",
  template_manager: "Template manager",
};

const revocableInvitationStatuses = new Set(["pending"]);

function formatDate(value: string) {
  return new Intl.DateTimeFormat("en", {
    day: "numeric",
    month: "short",
    year: "numeric",
  }).format(new Date(value));
}

function humanizeStatus(value: string) {
  return value.replaceAll("_", " ");
}

export function PlatformUsers() {
  const { getToken } = useAuth();
  const [users, setUsers] = useState<PlatformManagedUser[]>([]);
  const [invitations, setInvitations] = useState<PlatformUserInvitation[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [revokingId, setRevokingId] = useState<string | null>(null);
  const [accessDenied, setAccessDenied] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);

  const withToken = useCallback(
    async <T,>(operation: (token: string) => Promise<T>) => {
      const token = await getToken();
      if (!token) throw new Error("No active session token is available.");
      return operation(token);
    },
    [getToken],
  );

  const loadDirectory = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const identity = await withToken(fetchPlatformIdentity);
      if (identity.role !== "platform_super_admin") {
        setAccessDenied(true);
        return;
      }
      const [userRows, invitationRows] = await Promise.all([
        withToken(fetchPlatformUsers),
        withToken(fetchPlatformUserInvitations),
      ]);
      setUsers(userRows);
      setInvitations(invitationRows);
    } catch (caught) {
      setError(
        caught instanceof Error ? caught.message : "Platform users could not be loaded.",
      );
    } finally {
      setIsLoading(false);
    }
  }, [withToken]);

  useEffect(() => {
    const initialLoad = window.setTimeout(() => void loadDirectory(), 0);
    return () => window.clearTimeout(initialLoad);
  }, [loadDirectory]);

  async function handleInvite(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setIsSaving(true);
    setError(null);
    setNotice(null);
    const form = event.currentTarget;
    const formData = new FormData(form);
    const email = String(formData.get("email") ?? "").trim();
    const displayName = String(formData.get("displayName") ?? "").trim();
    const role = String(formData.get("role") ?? "") as PlatformRole;

    try {
      await withToken((token) =>
        createPlatformUserInvitation(token, {
          email,
          role,
          ...(displayName ? { display_name: displayName } : {}),
        }),
      );
      form.reset();
      setNotice(`Invitation sent to ${email}.`);
      await loadDirectory();
    } catch (caught) {
      setError(
        caught instanceof Error ? caught.message : "The invitation could not be sent.",
      );
    } finally {
      setIsSaving(false);
    }
  }

  async function handleRevoke(invitation: PlatformUserInvitation) {
    if (!window.confirm(`Revoke the invitation for ${invitation.email}?`)) return;
    setRevokingId(invitation.id);
    setError(null);
    setNotice(null);
    try {
      await withToken((token) =>
        revokePlatformUserInvitation(token, invitation.id),
      );
      setNotice(`Invitation revoked for ${invitation.email}.`);
      await loadDirectory();
    } catch (caught) {
      setError(
        caught instanceof Error ? caught.message : "The invitation could not be revoked.",
      );
    } finally {
      setRevokingId(null);
    }
  }

  if (isLoading) {
    return (
      <div className="flex min-h-[28rem] items-center justify-center gap-3 text-sm font-bold text-[#6d6b64]">
        <Loader2 className="size-5 animate-spin text-[#d73a2f]" aria-hidden />
        Loading platform directory
      </div>
    );
  }

  if (accessDenied) {
    return (
      <section className="max-w-xl border border-[#171714] bg-[#fffefa] p-7">
        <ShieldAlert className="size-6 text-[#d73a2f]" aria-hidden />
        <h1 className="mt-5 text-2xl font-black">Super admin access required</h1>
        <p className="mt-3 text-sm leading-6 text-[#6d6b64]">
          Only platform super admins can invite or review platform users.
        </p>
      </section>
    );
  }

  return (
    <div className="mx-auto max-w-7xl">
      <div className="flex flex-col gap-5 border-b border-[#171714] pb-7 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <p className="utility-label !text-[#d73a2f]">Identity directory</p>
          <h1 className="mt-3 text-3xl font-black sm:text-4xl">Platform users</h1>
          <p className="mt-3 max-w-2xl text-sm leading-6 text-[#6d6b64]">
            Invite dedicated internal accounts and track access separately from
            customer organizations.
          </p>
        </div>
        <button
          className="inline-flex h-10 items-center gap-2 border border-[#171714] px-3 text-sm font-bold hover:bg-[#f0eee8]"
          onClick={() => void loadDirectory()}
          type="button"
        >
          <RefreshCw className="size-4" aria-hidden /> Refresh
        </button>
      </div>

      {(error || notice) && (
        <div
          className={`mt-6 border-l-2 px-4 py-3 text-sm ${
            error
              ? "border-[#d73a2f] bg-[#f6e9e6] text-[#8f221c]"
              : "border-[#34785f] bg-[#e8f2ed] text-[#245441]"
          }`}
          role={error ? "alert" : "status"}
        >
          {error ?? notice}
        </div>
      )}

      <div className="grid gap-7 py-7 xl:grid-cols-[22rem_1fr]">
        <section className="h-fit border border-[#171714] bg-[#fffefa] p-6">
          <div className="flex items-center gap-3">
            <span className="grid size-10 place-items-center bg-[#171714] text-white">
              <MailPlus className="size-5" aria-hidden />
            </span>
            <div>
              <p className="utility-label !text-[#d73a2f]">New access</p>
              <h2 className="mt-1 text-xl font-black">Invite a user</h2>
            </div>
          </div>
          <form className="mt-7 space-y-5" onSubmit={handleInvite}>
            <div>
              <label className="text-sm font-bold" htmlFor="invite-display-name">
                Display name <span className="font-normal text-[#8a877f]">(optional)</span>
              </label>
              <input
                autoComplete="name"
                className="mt-2 h-11 w-full border border-[#bdbab1] bg-white px-3 text-sm outline-none focus:border-[#171714] focus:ring-1 focus:ring-[#171714]"
                id="invite-display-name"
                name="displayName"
                type="text"
              />
            </div>
            <div>
              <label className="text-sm font-bold" htmlFor="invite-email">Email</label>
              <input
                autoComplete="email"
                className="mt-2 h-11 w-full border border-[#bdbab1] bg-white px-3 text-sm outline-none focus:border-[#171714] focus:ring-1 focus:ring-[#171714]"
                id="invite-email"
                name="email"
                required
                type="email"
              />
            </div>
            <div>
              <label className="text-sm font-bold" htmlFor="invite-role">Access level</label>
              <select
                className="mt-2 h-11 w-full border border-[#bdbab1] bg-white px-3 text-sm outline-none focus:border-[#171714] focus:ring-1 focus:ring-[#171714]"
                defaultValue="platform_operations"
                id="invite-role"
                name="role"
              >
                {Object.entries(roleLabels).map(([value, label]) => (
                  <option key={value} value={value}>{label}</option>
                ))}
              </select>
            </div>
            <button
              className="inline-flex h-11 w-full items-center justify-center gap-2 bg-[#171714] px-4 text-sm font-bold text-white hover:bg-[#d73a2f] disabled:cursor-wait disabled:opacity-70"
              disabled={isSaving}
              type="submit"
            >
              {isSaving ? <Loader2 className="size-4 animate-spin" aria-hidden /> : <ArrowRight className="size-4" aria-hidden />}
              {isSaving ? "Sending invitation" : "Send invitation"}
            </button>
          </form>
        </section>

        <div className="space-y-7">
          <section className="border border-[#171714] bg-[#fffefa]">
            <div className="flex items-center justify-between border-b border-[#171714] px-5 py-4">
              <div className="flex items-center gap-3">
                <UserRoundCheck className="size-5 text-[#d73a2f]" aria-hidden />
                <h2 className="text-lg font-black">Current users</h2>
              </div>
              <span className="utility-label">{users.length} total</span>
            </div>
            <div className="divide-y divide-[#d8d5cc]">
              {users.length === 0 ? (
                <p className="p-6 text-sm text-[#6d6b64]">No platform users found.</p>
              ) : users.map((user) => (
                <article className="grid gap-3 p-5 sm:grid-cols-[1fr_auto] sm:items-center" key={user.id}>
                  <div className="min-w-0">
                    <p className="truncate text-sm font-black">{user.display_name ?? user.primary_email ?? "Unnamed user"}</p>
                    <p className="mt-1 truncate text-sm text-[#6d6b64]">{user.primary_email ?? user.clerk_user_id}</p>
                  </div>
                  <div className="flex flex-wrap items-center gap-2 sm:justify-end">
                    <span className="border border-[#bdbab1] px-2 py-1 text-xs font-bold">{roleLabels[user.platform_role]}</span>
                    <span className={`px-2 py-1 text-xs font-bold capitalize ${user.status === "active" ? "bg-[#e8f2ed] text-[#245441]" : "bg-[#f0eee8] text-[#6d6b64]"}`}>{humanizeStatus(user.status)}</span>
                  </div>
                </article>
              ))}
            </div>
          </section>

          <section className="border border-[#171714] bg-[#fffefa]">
            <div className="flex items-center justify-between border-b border-[#171714] px-5 py-4">
              <h2 className="text-lg font-black">Invitation ledger</h2>
              <span className="utility-label">{invitations.length} records</span>
            </div>
            <div className="divide-y divide-[#d8d5cc]">
              {invitations.length === 0 ? (
                <p className="p-6 text-sm text-[#6d6b64]">
                  No invitations yet. Send the first one from this page.
                </p>
              ) : invitations.map((invitation) => (
                <article className="grid gap-4 p-5 md:grid-cols-[1fr_auto] md:items-center" key={invitation.id}>
                  <div className="min-w-0">
                    <p className="truncate text-sm font-black">{invitation.display_name ?? invitation.email}</p>
                    <p className="mt-1 truncate text-sm text-[#6d6b64]">{invitation.email}</p>
                    <p className="mt-2 text-xs text-[#8a877f]">
                      {roleLabels[invitation.platform_role]} · Expires {formatDate(invitation.expires_at)}
                    </p>
                  </div>
                  <div className="flex items-center gap-2 md:justify-end">
                    <span className="bg-[#f0eee8] px-2 py-1 text-xs font-bold capitalize">{humanizeStatus(invitation.status)}</span>
                    {revocableInvitationStatuses.has(invitation.status) && (
                      <button
                        className="inline-flex size-9 items-center justify-center border border-[#bdbab1] text-[#6d6b64] hover:border-[#d73a2f] hover:text-[#d73a2f] disabled:cursor-wait disabled:opacity-50"
                        disabled={revokingId === invitation.id}
                        onClick={() => void handleRevoke(invitation)}
                        title="Revoke invitation"
                        type="button"
                      >
                        {revokingId === invitation.id ? <Loader2 className="size-4 animate-spin" aria-hidden /> : <X className="size-4" aria-hidden />}
                        <span className="sr-only">Revoke invitation for {invitation.email}</span>
                      </button>
                    )}
                  </div>
                </article>
              ))}
            </div>
          </section>
        </div>
      </div>
    </div>
  );
}
