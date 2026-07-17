import { Upload } from "lucide-react";

export default function LeadsPage() {
  return (
    <section className="border border-[#d8d5cc] bg-[#fffefa] p-6">
      <div className="flex items-start justify-between gap-4">
        <div>
          <p className="utility-label !text-[#d73a2f]">Leads</p>
          <h1 className="mt-3 text-2xl font-black text-[#171714]">
            Lead imports
          </h1>
        </div>
        <button className="inline-flex size-10 items-center justify-center border border-[#171714] text-[#171714] transition hover:bg-[#171714] hover:text-white" title="Upload leads">
          <Upload className="size-4" aria-hidden />
          <span className="sr-only">Upload leads</span>
        </button>
      </div>
      <p className="mt-6 max-w-2xl text-sm leading-6 text-[#6d6b64]">
        CSV upload, category-specific lead fields, retry settings, and import
        validation will land here after the backend lead models are added.
      </p>
    </section>
  );
}
