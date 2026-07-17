import { PhoneIncoming } from "lucide-react";

export default function CallsPage() {
  return (
    <section className="border border-[#d8d5cc] bg-[#fffefa] p-6">
      <div className="flex items-start gap-4">
        <div className="grid size-10 place-items-center bg-[#e4e9ee] text-[#2f4e6f]">
          <PhoneIncoming className="size-5" aria-hidden />
        </div>
        <div>
          <p className="utility-label !text-[#d73a2f]">Calls</p>
          <h1 className="mt-3 text-2xl font-black text-[#171714]">
            Call activity
          </h1>
          <p className="mt-4 max-w-2xl text-sm leading-6 text-[#6d6b64]">
            Call attempts, transcripts, recordings, lead interest labels, and
            knowledge gaps will appear here once call persistence is connected.
          </p>
        </div>
      </div>
    </section>
  );
}
