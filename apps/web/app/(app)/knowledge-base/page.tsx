import { FileQuestion } from "lucide-react";

export default function KnowledgeBasePage() {
  return (
    <section className="border border-[#d8d5cc] bg-[#fffefa] p-6">
      <div className="flex items-start gap-4">
        <div className="grid size-10 place-items-center bg-[#e8ebe4] text-[#66735b]">
          <FileQuestion className="size-5" aria-hidden />
        </div>
        <div>
          <p className="utility-label !text-[#d73a2f]">Knowledge base</p>
          <h1 className="mt-3 text-2xl font-black text-[#171714]">
            Guided Q&amp;A setup
          </h1>
          <p className="mt-4 max-w-2xl text-sm leading-6 text-[#6d6b64]">
            Add product details, pricing answers, common questions, objection
            handling, and extra notes for accurate conversations.
          </p>
        </div>
      </div>
    </section>
  );
}
