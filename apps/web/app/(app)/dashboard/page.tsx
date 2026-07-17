import { Activity, Database, PhoneCall, UsersRound } from "lucide-react";
import { BackendContextPanel } from "@/components/backend-context-panel";

const metrics = [
  { label: "Leads uploaded", value: "0", icon: UsersRound },
  { label: "Calls placed", value: "0", icon: PhoneCall },
  { label: "Interested leads", value: "0", icon: Activity },
  { label: "KB entries", value: "0", icon: Database },
];

export default function DashboardPage() {
  return (
    <div className="space-y-7">
      <div className="border-b border-[#171714] pb-6">
        <p className="utility-label !text-[#d73a2f]">Overview</p>
        <h1 className="mt-3 text-3xl font-black text-[#171714]">
          Today at a glance
        </h1>
      </div>

      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        {metrics.map((metric) => (
          <div
            key={metric.label}
            className="border border-[#d8d5cc] bg-[#fffefa] p-5"
          >
            <div className="flex items-center justify-between">
              <p className="utility-label">{metric.label}</p>
              <metric.icon className="size-4 text-[#d73a2f]" aria-hidden />
            </div>
            <p className="mt-5 text-4xl font-black text-[#171714]">
              {metric.value}
            </p>
          </div>
        ))}
      </div>

      <BackendContextPanel />
    </div>
  );
}
