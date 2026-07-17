"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import {
  BookOpenCheck,
  Check,
  ChevronRight,
  FilePenLine,
  Loader2,
  Plus,
  Save,
  Send,
  Sparkles,
  Trash2,
  TriangleAlert,
  X,
} from "lucide-react";
import { useAuth } from "@clerk/nextjs";
import {
  createTenantKnowledgeDraft,
  fetchStarterTemplates,
  fetchTenantKnowledgeBase,
  publishTenantKnowledgeDraft,
  replaceTenantKnowledgeQuestions,
  updateTenantKnowledgeDraft,
  type QuestionAnswerType,
  type StarterTemplate,
  type TenantKnowledgeBase,
  type TenantKnowledgeVersion,
} from "@/lib/api-client";

type EditableQuestion = {
  clientId: string;
  key: string;
  label: string;
  helpText: string;
  answerType: QuestionAnswerType;
  required: boolean;
  options: string;
  answer: string;
};

type KnowledgeDraft = {
  title: string;
  businessName: string;
  businessSummary: string;
  additionalNotes: string;
  questions: EditableQuestion[];
};

const answerTypes: { value: QuestionAnswerType; label: string }[] = [
  { value: "short_text", label: "Short text" },
  { value: "long_text", label: "Long text" },
  { value: "number", label: "Number" },
  { value: "boolean", label: "Yes / no" },
  { value: "single_select", label: "Choose one" },
  { value: "multi_select", label: "Choose many" },
  { value: "date", label: "Date" },
];

function blankQuestion(): EditableQuestion {
  return { clientId: crypto.randomUUID(), key: "", label: "", helpText: "", answerType: "short_text", required: false, options: "", answer: "" };
}

function isChoiceType(type: QuestionAnswerType) {
  return type === "single_select" || type === "multi_select";
}

function toDraft(version: TenantKnowledgeVersion): KnowledgeDraft {
  const profile = version.business_profile_json;
  return {
    title: version.title,
    businessName: typeof profile.business_name === "string" ? profile.business_name : "",
    businessSummary: typeof profile.business_summary === "string" ? profile.business_summary : "",
    additionalNotes: version.additional_notes ?? "",
    questions: [...version.questions].sort((a, b) => a.display_order - b.display_order).map((question) => ({
      clientId: question.id,
      key: question.key,
      label: question.label,
      helpText: question.help_text ?? "",
      answerType: question.answer_type,
      required: question.required,
      options: question.options_json?.filter((option): option is string => typeof option === "string").join(", ") ?? "",
      answer: typeof question.answer_value_json === "string" ? question.answer_value_json : question.answer_value_json == null ? "" : JSON.stringify(question.answer_value_json),
    })),
  };
}

function toPayload(questions: EditableQuestion[]) {
  return questions.map((question, displayOrder) => ({
    key: question.key.trim(),
    label: question.label.trim(),
    help_text: question.helpText.trim() || null,
    answer_type: question.answerType,
    required: question.required,
    display_order: displayOrder,
    validation_json: {},
    options_json: isChoiceType(question.answerType) ? question.options.split(",").map((option) => option.trim()).filter(Boolean) : null,
    answer_value_json: question.answer.trim() || null,
  }));
}

function friendlyError(error: unknown) {
  const value = error instanceof Error ? error.message : "We could not complete that action.";
  if (value.includes("required_answers_missing")) return "Answer all required questions before publishing.";
  return value.replaceAll("_", " ");
}

export function TenantKnowledgeBaseWorkspace() {
  const { getToken } = useAuth();
  const [workspace, setWorkspace] = useState<TenantKnowledgeBase | null>(null);
  const [starters, setStarters] = useState<StarterTemplate[]>([]);
  const [draft, setDraft] = useState<KnowledgeDraft | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);

  const withToken = useCallback(async <T,>(callback: (token: string) => Promise<T>) => {
    const token = await getToken();
    if (!token) throw new Error("unauthorized");
    return callback(token);
  }, [getToken]);

  const load = useCallback(async () => {
    const [nextWorkspace, nextStarters] = await Promise.all([
      withToken(fetchTenantKnowledgeBase),
      withToken(fetchStarterTemplates),
    ]);
    setWorkspace(nextWorkspace);
    setStarters(nextStarters);
    setDraft(nextWorkspace?.draft_version ? toDraft(nextWorkspace.draft_version) : null);
  }, [withToken]);

  useEffect(() => {
    let cancelled = false;
    async function initialize() {
      try {
        await load();
      } catch (caught) {
        if (!cancelled) setError(friendlyError(caught));
      } finally {
        if (!cancelled) setIsLoading(false);
      }
    }
    void initialize();
    return () => { cancelled = true; };
  }, [load]);

  const activeVersion = workspace?.active_version ?? null;
  const activeCategory = useMemo(
    () => starters.find((starter) => starter.category_id === activeVersion?.category_id)?.category_name ?? null,
    [activeVersion?.category_id, starters],
  );

  async function beginDraft(starterTemplateId?: string) {
    try {
      setIsSaving(true);
      setError(null);
      const nextDraft = await withToken((token) => createTenantKnowledgeDraft(token, starterTemplateId));
      await load();
      setDraft(toDraft(nextDraft));
      setNotice(starterTemplateId ? "Your private draft is ready to tailor." : "A new draft was created from your published knowledge base.");
    } catch (caught) {
      setError(friendlyError(caught));
    } finally {
      setIsSaving(false);
    }
  }

  function updateQuestion(clientId: string, update: Partial<EditableQuestion>) {
    setDraft((current) => current ? { ...current, questions: current.questions.map((question) => question.clientId === clientId ? { ...question, ...update } : question) } : current);
  }

  async function saveDraft(): Promise<boolean> {
    if (!workspace?.draft_version || !draft) return false;
    if (!draft.title.trim() || draft.questions.some((question) => !question.key.trim() || !question.label.trim())) {
      setError("Give the knowledge base a title, and each question both a field key and label.");
      return false;
    }
    try {
      setIsSaving(true);
      setError(null);
      const versionId = workspace.draft_version.id;
      await withToken((token) => updateTenantKnowledgeDraft(token, versionId, {
        title: draft.title.trim(),
        business_profile_json: { business_name: draft.businessName.trim(), business_summary: draft.businessSummary.trim() },
        additional_notes: draft.additionalNotes.trim() || null,
      }));
      await withToken((token) => replaceTenantKnowledgeQuestions(token, versionId, toPayload(draft.questions)));
      await load();
      setNotice("Draft saved.");
      return true;
    } catch (caught) {
      setError(friendlyError(caught));
      return false;
    } finally {
      setIsSaving(false);
    }
  }

  async function publishDraft() {
    if (!workspace?.draft_version) return;
    if (!(await saveDraft())) return;
    try {
      setIsSaving(true);
      setError(null);
      await withToken((token) => publishTenantKnowledgeDraft(token, workspace.draft_version!.id));
      await load();
      setNotice("Knowledge base published. Future calls will use this version.");
    } catch (caught) {
      setError(friendlyError(caught));
    } finally {
      setIsSaving(false);
    }
  }

  if (isLoading) return <div className="flex min-h-96 items-center justify-center text-sm font-bold text-[#6d6b64]"><Loader2 className="mr-3 size-5 animate-spin" />Loading your knowledge base</div>;

  return <div className="mx-auto max-w-6xl">
    <header className="border-b border-[#171714] pb-7"><p className="utility-label !text-[#d73a2f]">Knowledge base</p><div className="mt-3 flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between"><div><h1 className="text-3xl font-black text-[#171714] sm:text-4xl">What your assistant knows</h1><p className="mt-3 max-w-2xl text-sm leading-6 text-[#6d6b64]">Start with a category guide, then make it completely your own. Publish only when the details are ready for customer conversations.</p></div>{activeVersion && !workspace?.draft_version ? <button className="inline-flex h-10 items-center gap-2 bg-[#171714] px-4 text-sm font-bold text-white hover:bg-[#d73a2f]" disabled={isSaving} onClick={() => beginDraft()} type="button"><FilePenLine className="size-4" />Update knowledge</button> : null}</div></header>
    {error ? <Alert color="error" message={error} onDismiss={() => setError(null)} /> : null}
    {notice ? <Alert color="success" message={notice} onDismiss={() => setNotice(null)} /> : null}
    {workspace?.draft_version && draft ? <KnowledgeEditor draft={draft} isSaving={isSaving} onAddQuestion={() => setDraft((current) => current ? { ...current, questions: [...current.questions, blankQuestion()] } : current)} onChange={(update) => setDraft((current) => current ? { ...current, ...update } : current)} onDeleteQuestion={(clientId) => setDraft((current) => current ? { ...current, questions: current.questions.filter((question) => question.clientId !== clientId) } : current)} onPublish={publishDraft} onSave={saveDraft} onUpdateQuestion={updateQuestion} version={workspace.draft_version.version} /> : activeVersion ? <PublishedKnowledge activeCategory={activeCategory} onCreateDraft={() => beginDraft()} version={activeVersion} /> : <StarterPicker isSaving={isSaving} onStart={beginDraft} starters={starters} />}
  </div>;
}

function Alert({ color, message, onDismiss }: { color: "error" | "success"; message: string; onDismiss: () => void }) { const success = color === "success"; return <div className={`mt-6 flex items-center gap-3 border-l-2 p-4 text-sm ${success ? "border-[#66735b] bg-[#eef0ea] text-[#4d5b44]" : "border-[#d73a2f] bg-[#f6e9e6] text-[#8f221c]"}`}>{success ? <Check className="size-4" /> : <TriangleAlert className="size-4" />}<p>{message}</p><button className="ml-auto" onClick={onDismiss} title="Dismiss" type="button"><X className="size-4" /></button></div>; }

function StarterPicker({ isSaving, onStart, starters }: { isSaving: boolean; onStart: (id: string) => void; starters: StarterTemplate[] }) { return <section className="mt-7"><div className="border border-[#171714] bg-[#fffefa] p-6"><Sparkles className="size-6 text-[#d73a2f]" /><h2 className="mt-5 text-2xl font-black">Choose a useful starting point</h2><p className="mt-3 max-w-2xl text-sm leading-6 text-[#6d6b64]">This only gives you a first set of questions. You can change every detail before you publish.</p></div><div className="mt-5 grid gap-4 md:grid-cols-2">{starters.map((starter) => <article className="border border-[#d8d5cc] bg-[#fffefa] p-5" key={starter.id}><p className="utility-label !text-[#2f4e6f]">{starter.category_name}</p><h3 className="mt-3 text-lg font-black">{starter.title}</h3><p className="mt-2 min-h-10 text-sm leading-5 text-[#6d6b64]">{starter.description || "A guided starting point for your team."}</p><p className="mt-5 text-xs font-bold text-[#4e4c46]">{starter.qna_questions.length} questions included</p><button className="mt-5 inline-flex h-10 items-center gap-2 bg-[#171714] px-4 text-sm font-bold text-white hover:bg-[#d73a2f] disabled:opacity-60" disabled={isSaving} onClick={() => onStart(starter.id)} type="button">Use this guide <ChevronRight className="size-4" /></button></article>)}{!starters.length ? <div className="border border-dashed border-[#d8d5cc] bg-[#fffefa] p-6 text-sm leading-6 text-[#6d6b64]">A starter guide has not been published for your category yet. Contact the RingIQ team to add one.</div> : null}</div></section>; }

function PublishedKnowledge({ activeCategory, onCreateDraft, version }: { activeCategory: string | null; onCreateDraft: () => void; version: TenantKnowledgeVersion }) { return <section className="mt-7 border border-[#171714] bg-[#fffefa]"><div className="flex flex-col gap-5 border-b border-[#171714] p-6 sm:flex-row sm:items-start sm:justify-between"><div><p className="utility-label !text-[#66735b]">Published and active</p><h2 className="mt-3 text-2xl font-black">{version.title}</h2><p className="mt-2 text-sm text-[#6d6b64]">{activeCategory || "Your category"} · Version {version.version}</p></div><BookOpenCheck className="size-7 text-[#66735b]" /></div><div className="grid gap-px bg-[#d8d5cc] sm:grid-cols-3"><div className="bg-[#fffefa] p-5"><p className="utility-label">Questions</p><p className="mt-3 text-2xl font-black">{version.questions.length}</p></div><div className="bg-[#fffefa] p-5"><p className="utility-label">Required answered</p><p className="mt-3 text-2xl font-black">{version.questions.filter((question) => !question.required || question.answer_value_json).length}/{version.questions.length}</p></div><div className="bg-[#fffefa] p-5"><p className="utility-label">Used by</p><p className="mt-3 text-sm font-black">Future calls</p></div></div><div className="p-6"><button className="inline-flex h-10 items-center gap-2 bg-[#171714] px-4 text-sm font-bold text-white hover:bg-[#d73a2f]" onClick={onCreateDraft} type="button"><FilePenLine className="size-4" />Create an update</button></div></section>; }

function KnowledgeEditor({ draft, isSaving, onAddQuestion, onChange, onDeleteQuestion, onPublish, onSave, onUpdateQuestion, version }: { draft: KnowledgeDraft; isSaving: boolean; onAddQuestion: () => void; onChange: (update: Partial<KnowledgeDraft>) => void; onDeleteQuestion: (id: string) => void; onPublish: () => void; onSave: () => void; onUpdateQuestion: (id: string, update: Partial<EditableQuestion>) => void; version: number }) { return <section className="mt-7 border border-[#171714] bg-[#fffefa]"><div className="flex flex-col gap-4 border-b border-[#171714] p-5 sm:flex-row sm:items-center sm:justify-between"><div><p className="utility-label !text-[#d73a2f]">Draft version {version}</p><h2 className="mt-2 text-xl font-black">Build your conversation knowledge</h2></div><div className="flex gap-2"><button className="inline-flex h-10 items-center gap-2 border border-[#171714] px-3 text-sm font-bold hover:bg-[#f0eee8] disabled:opacity-60" disabled={isSaving} onClick={onSave} type="button"><Save className="size-4" />Save</button><button className="inline-flex h-10 items-center gap-2 bg-[#d73a2f] px-3 text-sm font-bold text-white hover:bg-[#b72c24] disabled:opacity-60" disabled={isSaving} onClick={onPublish} type="button">{isSaving ? <Loader2 className="size-4 animate-spin" /> : <Send className="size-4" />}Publish</button></div></div><div className="space-y-8 p-5"><div className="grid gap-5 md:grid-cols-2"><Field label="Knowledge base title"><input className="field-control" onChange={(event) => onChange({ title: event.target.value })} value={draft.title} /></Field><Field label="Business name"><input className="field-control" onChange={(event) => onChange({ businessName: event.target.value })} placeholder="Your company name" value={draft.businessName} /></Field></div><Field label="What does your business offer?"><textarea className="field-control min-h-24 resize-y" onChange={(event) => onChange({ businessSummary: event.target.value })} placeholder="Describe your core offering, audience, and any important positioning." value={draft.businessSummary} /></Field><Field hint="Anything your assistant should know that does not fit a question below." label="Additional guidance"><textarea className="field-control min-h-28 resize-y" onChange={(event) => onChange({ additionalNotes: event.target.value })} placeholder="Tone, prohibited claims, common objections, or other useful context." value={draft.additionalNotes} /></Field><div className="border-t border-[#d8d5cc] pt-6"><div className="flex items-end justify-between gap-4"><div><p className="utility-label !text-[#2f4e6f]">Guided answers</p><h3 className="mt-2 text-lg font-black">What the assistant can say</h3></div><button className="inline-flex size-10 items-center justify-center border border-[#171714] hover:bg-[#f0eee8]" onClick={onAddQuestion} title="Add a question" type="button"><Plus className="size-4" /></button></div><div className="mt-5 space-y-4">{draft.questions.map((question, index) => <QuestionEditor index={index} key={question.clientId} onDelete={() => onDeleteQuestion(question.clientId)} onUpdate={(update) => onUpdateQuestion(question.clientId, update)} question={question} />)}{!draft.questions.length ? <div className="border border-dashed border-[#d8d5cc] p-5 text-sm text-[#6d6b64]">Add a question to define what your assistant should know.</div> : null}</div></div></div></section>; }

function QuestionEditor({ index, onDelete, onUpdate, question }: { index: number; onDelete: () => void; onUpdate: (update: Partial<EditableQuestion>) => void; question: EditableQuestion }) { return <article className="border border-[#d8d5cc] bg-[#fdfcf8] p-4"><div className="flex items-center justify-between"><p className="text-sm font-black">Question {index + 1}</p><button className="inline-flex size-8 items-center justify-center text-[#8f221c] hover:bg-[#f6e9e6]" onClick={onDelete} title="Remove question" type="button"><Trash2 className="size-4" /></button></div><div className="mt-4 grid gap-4 md:grid-cols-[minmax(0,1fr)_160px]"><Field label="Question"><input className="field-control" onChange={(event) => onUpdate({ label: event.target.value })} placeholder="What should your assistant know?" value={question.label} /></Field><Field label="Answer type"><select className="field-control" onChange={(event) => onUpdate({ answerType: event.target.value as QuestionAnswerType })} value={question.answerType}>{answerTypes.map((type) => <option key={type.value} value={type.value}>{type.label}</option>)}</select></Field></div><div className="mt-4 grid gap-4 md:grid-cols-2"><Field label="Field key"><input className="field-control font-mono" onChange={(event) => onUpdate({ key: event.target.value.replace(/[^a-z0-9_]/g, "_") })} placeholder="project_name" value={question.key} /></Field><Field label="Optional guidance"><input className="field-control" onChange={(event) => onUpdate({ helpText: event.target.value })} placeholder="Clarify what belongs in this answer" value={question.helpText} /></Field></div>{isChoiceType(question.answerType) ? <div className="mt-4"><Field hint="Separate choices with commas." label="Allowed choices"><input className="field-control" onChange={(event) => onUpdate({ options: event.target.value })} placeholder="Apartments, Villas, Plots" value={question.options} /></Field></div> : null}<div className="mt-4"><Field label="Your answer"><textarea className="field-control min-h-24 resize-y" onChange={(event) => onUpdate({ answer: event.target.value })} placeholder="Write the approved information your assistant can use." value={question.answer} /></Field></div><label className="mt-4 flex items-center gap-2 text-sm font-bold text-[#4e4c46]"><input checked={question.required} onChange={(event) => onUpdate({ required: event.target.checked })} type="checkbox" />Required before publishing</label></article>; }

function Field({ children, hint, label }: { children: React.ReactNode; hint?: string; label: string }) { return <label className="block"><span className="block text-sm font-bold text-[#4e4c46]">{label}</span>{hint ? <span className="mt-1 block text-xs leading-5 text-[#6d6b64]">{hint}</span> : null}<span className="mt-2 block">{children}</span></label>; }
