import { Settings } from "lucide-react";

export default function SettingsPage() {
  return (
    <section className="border border-[#d8d5cc] bg-[#fffefa] p-6">
      <div className="flex items-start gap-4">
        <div className="grid size-10 place-items-center bg-[#f2e9d7] text-[#9a6517]">
          <Settings className="size-5" aria-hidden />
        </div>
        <div>
          <p className="utility-label !text-[#d73a2f]">Settings</p>
          <h1 className="mt-3 text-2xl font-black text-[#171714]">
            Workspace settings
          </h1>
          <p className="mt-4 max-w-2xl text-sm leading-6 text-[#6d6b64]">
            Organization details, call defaults, user access, and compliance
            controls will be configured here as the SaaS surface grows.
          </p>
        </div>
      </div>
    </section>
  );
}
