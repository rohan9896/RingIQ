"use client";

import { FormEvent, useCallback, useEffect, useMemo, useState } from "react";
import {
  Check,
  ChevronRight,
  CirclePlus,
  FileText,
  GripVertical,
  Loader2,
  Pencil,
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
  createCategoryTemplateVersion,
  createPlatformCategory,
  fetchCategoryTemplateVersions,
  fetchPlatformCategories,
  fetchPlatformIdentity,
  publishCategoryTemplateVersion,
  replaceTemplateQuestions,
  updateCategoryTemplateVersion,
  updatePlatformCategory,
  type CategoryStatus,
  type PlatformCategory,
  type PlatformIdentity,
  type PlatformTemplateVersion,
  type QuestionAnswerType,
  type TemplateQuestionInput,
} from "@/lib/api-client";

type DraftQuestion = {
  clientId: string;
  key: string;
  label: string;
  helpText: string;
  answerType: QuestionAnswerType;
  required: boolean;
  options: string;
};

type TemplateDraft = {
  title: string;
  description: string;
  leadFields: string;
  questions: DraftQuestion[];
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

function createQuestion(): DraftQuestion {
  return {
    clientId: crypto.randomUUID(),
    key: "",
    label: "",
    helpText: "",
    answerType: "short_text",
    required: true,
    options: "",
  };
}

function emptyTemplateDraft(): TemplateDraft {
  return { title: "", description: "", leadFields: "name\nemail\nphone_number", questions: [] };
}

function toTemplateDraft(template: PlatformTemplateVersion): TemplateDraft {
  const leadFields = Array.isArray(template.lead_schema_json.fields)
    ? template.lead_schema_json.fields.filter((field): field is string => typeof field === "string").join("\n")
    : "";

  return {
    title: template.title,
    description: template.description ?? "",
    leadFields,
    questions: [...template.qna_questions]
      .sort((a, b) => a.display_order - b.display_order)
      .map((question) => ({
        clientId: question.id,
        key: question.key,
        label: question.label,
        helpText: question.help_text ?? "",
        answerType: question.answer_type,
        required: question.required,
        options: question.options_json?.filter((option): option is string => typeof option === "string").join(", ") ?? "",
      })),
  };
}

function toQuestionPayload(questions: DraftQuestion[]): TemplateQuestionInput[] {
  return questions.map((question, index) => ({
    key: question.key.trim(),
    label: question.label.trim(),
    help_text: question.helpText.trim() || null,
    answer_type: question.answerType,
    required: question.required,
    display_order: index,
    validation_json: {},
    options_json: ["single_select", "multi_select"].includes(question.answerType)
      ? question.options.split(",").map((option) => option.trim()).filter(Boolean)
      : null,
  }));
}

function isChoiceType(answerType: QuestionAnswerType) {
  return answerType === "single_select" || answerType === "multi_select";
}

function humanizeError(error: unknown) {
  const value = error instanceof Error ? error.message : "Unable to complete that request.";
  return value.replaceAll("_", " ");
}

export function TemplateStudio() {
  const { getToken } = useAuth();
  const [identity, setIdentity] = useState<PlatformIdentity | null>(null);
  const [categories, setCategories] = useState<PlatformCategory[]>([]);
  const [selectedCategoryId, setSelectedCategoryId] = useState<string | null>(null);
  const [templates, setTemplates] = useState<PlatformTemplateVersion[]>([]);
  const [selectedTemplateId, setSelectedTemplateId] = useState<string | null>(null);
  const [draft, setDraft] = useState<TemplateDraft>(emptyTemplateDraft);
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);
  const [categoryFormOpen, setCategoryFormOpen] = useState(false);
  const [templateFormOpen, setTemplateFormOpen] = useState(false);
  const [editingCategory, setEditingCategory] = useState<PlatformCategory | null>(null);

  const selectedCategory = useMemo(
    () => categories.find((category) => category.id === selectedCategoryId) ?? null,
    [categories, selectedCategoryId],
  );
  const visibleTemplates = useMemo(
    () => templates.filter((template) => template.category_id === selectedCategoryId),
    [selectedCategoryId, templates],
  );
  const selectedTemplate = useMemo(
    () => visibleTemplates.find((template) => template.id === selectedTemplateId) ?? null,
    [visibleTemplates, selectedTemplateId],
  );
  const canWrite = identity?.role === "platform_super_admin" || identity?.role === "template_manager";

  const withToken = useCallback(async <T,>(callback: (token: string) => Promise<T>) => {
    const token = await getToken();
    if (!token) throw new Error("unauthorized");
    return callback(token);
  }, [getToken]);

  const loadTemplates = useCallback(async (categoryId: string, preferredTemplateId?: string) => {
    const result = await withToken((token) => fetchCategoryTemplateVersions(token, categoryId));
    setTemplates(result);
    const nextTemplateId = preferredTemplateId ?? result[0]?.id ?? null;
    setSelectedTemplateId(nextTemplateId);
    setDraft(nextTemplateId ? toTemplateDraft(result.find((template) => template.id === nextTemplateId) ?? result[0]) : emptyTemplateDraft());
  }, [withToken]);

  const loadCategories = useCallback(async (preferredCategoryId?: string) => {
    const result = await withToken(fetchPlatformCategories);
    setCategories(result);
    const categoryId = preferredCategoryId ?? result[0]?.id ?? null;
    setSelectedCategoryId(categoryId);
    if (categoryId) await loadTemplates(categoryId);
  }, [loadTemplates, withToken]);

  useEffect(() => {
    let cancelled = false;
    async function load() {
      try {
        const platformIdentity = await withToken(fetchPlatformIdentity);
        if (cancelled) return;
        setIdentity(platformIdentity);
        await loadCategories();
      } catch (caught) {
        if (!cancelled) setError(humanizeError(caught));
      } finally {
        if (!cancelled) setIsLoading(false);
      }
    }
    void load();
    return () => { cancelled = true; };
  }, [loadCategories, withToken]);

  async function submitCategory(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const formData = new FormData(event.currentTarget);
    const payload = {
      key: String(formData.get("key") ?? "").trim(),
      name: String(formData.get("name") ?? "").trim(),
      description: String(formData.get("description") ?? "").trim() || null,
      status: String(formData.get("status") ?? "active") as CategoryStatus,
    };
    try {
      setIsSaving(true);
      setError(null);
      const category = editingCategory
        ? await withToken((token) => updatePlatformCategory(token, editingCategory.id, {
            name: payload.name,
            description: payload.description,
            status: payload.status,
          }))
        : await withToken((token) => createPlatformCategory(token, payload));
      await loadCategories(category.id);
      setCategoryFormOpen(false);
      setEditingCategory(null);
      setNotice(editingCategory ? "Category updated." : "Category created. Add its first template next.");
    } catch (caught) {
      setError(humanizeError(caught));
    } finally {
      setIsSaving(false);
    }
  }

  async function submitTemplate(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!selectedCategory) return;
    const formData = new FormData(event.currentTarget);
    try {
      setIsSaving(true);
      setError(null);
      const template = await withToken((token) => createCategoryTemplateVersion(token, selectedCategory.id, {
        title: String(formData.get("title") ?? "").trim(),
        description: String(formData.get("description") ?? "").trim() || null,
        lead_schema_json: { fields: ["name", "email", "phone_number"] },
        qna_questions: [],
      }));
      await loadTemplates(selectedCategory.id, template.id);
      setTemplateFormOpen(false);
      setNotice("Draft template created.");
    } catch (caught) {
      setError(humanizeError(caught));
    } finally {
      setIsSaving(false);
    }
  }

  async function saveTemplate() {
    if (!selectedTemplate || selectedTemplate.status !== "draft") return;
    const invalidQuestion = draft.questions.some((question) => !question.key.trim() || !question.label.trim());
    if (!draft.title.trim() || invalidQuestion) {
      setError("Add a title, and give every question both a key and label.");
      return;
    }
    try {
      setIsSaving(true);
      setError(null);
      const fields = draft.leadFields.split("\n").map((field) => field.trim()).filter(Boolean);
      const metadata = await withToken((token) => updateCategoryTemplateVersion(token, selectedTemplate.id, {
        title: draft.title.trim(),
        description: draft.description.trim() || null,
        lead_schema_json: { fields },
      }));
      const saved = await withToken((token) => replaceTemplateQuestions(token, metadata.id, toQuestionPayload(draft.questions)));
      setTemplates((current) => current.map((template) => template.id === saved.id ? saved : template));
      setNotice("Draft saved.");
    } catch (caught) {
      setError(humanizeError(caught));
    } finally {
      setIsSaving(false);
    }
  }

  async function publishTemplate() {
    if (!selectedTemplate || selectedTemplate.status !== "draft") return;
    try {
      setIsSaving(true);
      setError(null);
      const published = await withToken((token) => publishCategoryTemplateVersion(token, selectedTemplate.id));
      setTemplates((current) => current.map((template) => template.id === published.id ? published : template));
      setNotice("Template published. It will guide future organization setup.");
    } catch (caught) {
      setError(humanizeError(caught));
    } finally {
      setIsSaving(false);
    }
  }

  function updateQuestion(clientId: string, update: Partial<DraftQuestion>) {
    setDraft((current) => ({
      ...current,
      questions: current.questions.map((question) => question.clientId === clientId ? { ...question, ...update } : question),
    }));
  }

  function selectTemplate(template: PlatformTemplateVersion) {
    setSelectedTemplateId(template.id);
    setDraft(toTemplateDraft(template));
  }

  if (isLoading) {
    return <div className="flex min-h-96 items-center justify-center text-sm font-bold text-[#6d6b64]"><Loader2 className="mr-3 size-5 animate-spin" />Loading template library</div>;
  }

  return (
    <div className="mx-auto max-w-[1400px]">
      <header className="border-b border-[#171714] pb-7">
        <div className="flex flex-col gap-5 sm:flex-row sm:items-end sm:justify-between">
          <div>
            <p className="utility-label !text-[#d73a2f]">Onboarding library</p>
            <h1 className="mt-3 text-3xl font-black text-[#171714] sm:text-4xl">Starter templates</h1>
            <p className="mt-3 max-w-2xl text-sm leading-6 text-[#6d6b64]">Create category-specific prompts that give new organizations a useful first knowledge base. They remain fully editable after setup.</p>
          </div>
          {canWrite ? <button className="inline-flex h-10 items-center justify-center gap-2 bg-[#171714] px-4 text-sm font-bold text-white hover:bg-[#d73a2f]" onClick={() => { setEditingCategory(null); setCategoryFormOpen(true); }} type="button"><CirclePlus className="size-4" />New category</button> : null}
        </div>
      </header>

      {error ? <div className="mt-6 flex items-start gap-3 border-l-2 border-[#d73a2f] bg-[#f6e9e6] p-4 text-sm text-[#8f221c]"><TriangleAlert className="mt-0.5 size-4 shrink-0" /><p>{error}</p><button className="ml-auto" onClick={() => setError(null)} title="Dismiss" type="button"><X className="size-4" /></button></div> : null}
      {notice ? <div className="mt-6 flex items-center gap-3 border-l-2 border-[#66735b] bg-[#eef0ea] p-4 text-sm text-[#4d5b44]"><Check className="size-4" /><p>{notice}</p><button className="ml-auto" onClick={() => setNotice(null)} title="Dismiss" type="button"><X className="size-4" /></button></div> : null}

      <div className="mt-7 grid gap-6 xl:grid-cols-[280px_minmax(0,1fr)]">
        <aside className="border border-[#171714] bg-[#fffefa]">
          <div className="flex items-center justify-between border-b border-[#171714] px-4 py-3"><p className="utility-label !text-[#2f4e6f]">Categories</p><span className="text-xs font-bold text-[#6d6b64]">{categories.length}</span></div>
          <div className="divide-y divide-[#e3e0d8]">
            {categories.map((category) => <button className={`flex w-full items-start gap-3 px-4 py-4 text-left ${category.id === selectedCategoryId ? "bg-[#171714] text-white" : "hover:bg-[#f0eee8]"}`} key={category.id} onClick={() => { setSelectedCategoryId(category.id); setSelectedTemplateId(null); setDraft(emptyTemplateDraft()); void loadTemplates(category.id).catch((caught) => setError(humanizeError(caught))); }} type="button"><span className={`mt-1.5 size-2 shrink-0 ${category.status === "active" ? "bg-[#66735b]" : "bg-[#9a6517]"}`} /><span className="min-w-0 flex-1"><span className="block truncate text-sm font-black">{category.name}</span><span className={`mt-1 block truncate font-mono text-[11px] ${category.id === selectedCategoryId ? "text-[#d8d5cc]" : "text-[#6d6b64]"}`}>{category.key}</span></span><ChevronRight className="mt-1 size-4 shrink-0" /></button>)}
            {!categories.length ? <div className="p-5 text-sm leading-6 text-[#6d6b64]">Add a category to start composing its onboarding template.</div> : null}
          </div>
        </aside>

        <section>
          {!selectedCategory ? <EmptyCategoryState canWrite={canWrite} onCreate={() => { setEditingCategory(null); setCategoryFormOpen(true); }} /> : <>
            <div className="flex flex-col gap-4 border border-[#171714] bg-[#fffefa] p-5 sm:flex-row sm:items-start sm:justify-between">
              <div><div className="flex items-center gap-2"><p className="utility-label !text-[#2f4e6f]">{selectedCategory.key}</p><span className={`border px-2 py-0.5 text-[10px] font-bold uppercase ${selectedCategory.status === "active" ? "border-[#aeb6a7] bg-[#eef0ea] text-[#4d5b44]" : "border-[#d9bc82] bg-[#f5eddb] text-[#7c5114]"}`}>{selectedCategory.status}</span></div><h2 className="mt-3 text-2xl font-black">{selectedCategory.name}</h2><p className="mt-2 max-w-xl text-sm leading-6 text-[#6d6b64]">{selectedCategory.description || "No category description yet."}</p></div>
              {canWrite ? <div className="flex gap-2"><button className="inline-flex size-10 items-center justify-center border border-[#d8d5cc] hover:bg-[#f0eee8]" onClick={() => { setEditingCategory(selectedCategory); setCategoryFormOpen(true); }} title="Edit category" type="button"><Pencil className="size-4" /></button><button className="inline-flex h-10 items-center gap-2 bg-[#171714] px-3 text-sm font-bold text-white hover:bg-[#d73a2f]" onClick={() => setTemplateFormOpen(true)} type="button"><Plus className="size-4" />New draft</button></div> : null}
            </div>

            <div className="mt-6 grid gap-6 2xl:grid-cols-[260px_minmax(0,1fr)]">
              <div className="border border-[#d8d5cc] bg-[#fffefa]"><div className="border-b border-[#d8d5cc] px-4 py-3"><p className="utility-label">Versions</p></div><div className="divide-y divide-[#e3e0d8]">{visibleTemplates.map((template) => <button className={`w-full px-4 py-4 text-left ${template.id === selectedTemplateId ? "bg-[#eef0ea]" : "hover:bg-[#f7f6f2]"}`} key={template.id} onClick={() => selectTemplate(template)} type="button"><div className="flex items-center justify-between gap-2"><p className="truncate text-sm font-black">{template.title}</p><span className={`shrink-0 px-1.5 py-0.5 text-[10px] font-bold uppercase ${template.status === "published" ? "bg-[#66735b] text-white" : "border border-[#d8d5cc] text-[#6d6b64]"}`}>{template.status}</span></div><p className="mt-2 text-xs text-[#6d6b64]">Version {template.version} · {template.qna_questions.length} questions</p></button>)}{!visibleTemplates.length ? <div className="p-5 text-sm leading-6 text-[#6d6b64]">No template versions yet.</div> : null}</div></div>
              <TemplateEditor canWrite={Boolean(canWrite)} draft={draft} isSaving={isSaving} onAddQuestion={() => setDraft((current) => ({ ...current, questions: [...current.questions, createQuestion()] }))} onChange={(update) => setDraft((current) => ({ ...current, ...update }))} onDeleteQuestion={(clientId) => setDraft((current) => ({ ...current, questions: current.questions.filter((question) => question.clientId !== clientId) }))} onPublish={publishTemplate} onSave={saveTemplate} onUpdateQuestion={updateQuestion} template={selectedTemplate} />
            </div>
          </>}
        </section>
      </div>

      {categoryFormOpen ? <CategoryDialog category={editingCategory} isSaving={isSaving} onClose={() => { setCategoryFormOpen(false); setEditingCategory(null); }} onSubmit={submitCategory} /> : null}
      {templateFormOpen && selectedCategory ? <TemplateDialog categoryName={selectedCategory.name} isSaving={isSaving} onClose={() => setTemplateFormOpen(false)} onSubmit={submitTemplate} /> : null}
    </div>
  );
}

function EmptyCategoryState({ canWrite, onCreate }: { canWrite: boolean; onCreate: () => void }) {
  return <div className="border border-dashed border-[#aeb6a7] bg-[#eef0ea] p-8 text-center"><Sparkles className="mx-auto size-6 text-[#66735b]" /><h2 className="mt-4 text-xl font-black">Build the first starting point</h2><p className="mx-auto mt-3 max-w-md text-sm leading-6 text-[#4d5b44]">Categories hold reusable guidance. Each one can have draft and published template versions.</p>{canWrite ? <button className="mt-6 inline-flex h-10 items-center gap-2 bg-[#171714] px-4 text-sm font-bold text-white hover:bg-[#d73a2f]" onClick={onCreate} type="button"><Plus className="size-4" />Create category</button> : null}</div>;
}

function TemplateEditor({ canWrite, draft, isSaving, onAddQuestion, onChange, onDeleteQuestion, onPublish, onSave, onUpdateQuestion, template }: { canWrite: boolean; draft: TemplateDraft; isSaving: boolean; onAddQuestion: () => void; onChange: (update: Partial<TemplateDraft>) => void; onDeleteQuestion: (clientId: string) => void; onPublish: () => void; onSave: () => void; onUpdateQuestion: (clientId: string, update: Partial<DraftQuestion>) => void; template: PlatformTemplateVersion | null }) {
  if (!template) return <div className="border border-dashed border-[#d8d5cc] bg-[#fffefa] p-8 text-center text-sm leading-6 text-[#6d6b64]"><FileText className="mx-auto size-6" /> <p className="mt-3">Select a template version, or create a new draft.</p></div>;
  const isDraft = template.status === "draft";
  return <div className="border border-[#171714] bg-[#fffefa]"><div className="flex flex-col gap-4 border-b border-[#171714] p-5 sm:flex-row sm:items-center sm:justify-between"><div><p className="utility-label !text-[#d73a2f]">Template editor</p><p className="mt-2 text-sm text-[#6d6b64]">Version {template.version} · {isDraft ? "Changes are not live yet" : "Published templates are read-only"}</p></div>{canWrite && isDraft ? <div className="flex gap-2"><button className="inline-flex h-10 items-center gap-2 border border-[#171714] px-3 text-sm font-bold hover:bg-[#f0eee8] disabled:opacity-60" disabled={isSaving} onClick={onSave} type="button"><Save className="size-4" />Save</button><button className="inline-flex h-10 items-center gap-2 bg-[#d73a2f] px-3 text-sm font-bold text-white hover:bg-[#b72c24] disabled:opacity-60" disabled={isSaving} onClick={onPublish} type="button">{isSaving ? <Loader2 className="size-4 animate-spin" /> : <Send className="size-4" />}Publish</button></div> : null}</div>
    <div className="space-y-7 p-5"><div className="grid gap-5 md:grid-cols-2"><Field label="Template title"><input className="field-control" disabled={!isDraft || !canWrite} onChange={(event) => onChange({ title: event.target.value })} value={draft.title} /></Field><Field label="Description"><input className="field-control" disabled={!isDraft || !canWrite} onChange={(event) => onChange({ description: event.target.value })} value={draft.description} /></Field></div><Field hint="One lead field per line. Name, email and phone number are included by default." label="Lead fields"><textarea className="field-control min-h-24 resize-y" disabled={!isDraft || !canWrite} onChange={(event) => onChange({ leadFields: event.target.value })} value={draft.leadFields} /></Field>
      <div className="border-t border-[#d8d5cc] pt-6"><div className="flex items-end justify-between gap-4"><div><p className="utility-label !text-[#2f4e6f]">Knowledge-base questionnaire</p><h3 className="mt-2 text-lg font-black">Questions organizations answer</h3></div>{canWrite && isDraft ? <button className="inline-flex size-10 items-center justify-center border border-[#171714] hover:bg-[#f0eee8]" onClick={onAddQuestion} title="Add question" type="button"><Plus className="size-4" /></button> : null}</div><div className="mt-5 space-y-4">{draft.questions.map((question, index) => <QuestionCard canWrite={Boolean(canWrite && isDraft)} index={index} key={question.clientId} onDelete={() => onDeleteQuestion(question.clientId)} onUpdate={(update) => onUpdateQuestion(question.clientId, update)} question={question} />)}{!draft.questions.length ? <div className="border border-dashed border-[#d8d5cc] p-5 text-sm text-[#6d6b64]">Add the first question to give organizations a structured place to describe their business.</div> : null}</div></div></div></div>;
}

function QuestionCard({ canWrite, index, onDelete, onUpdate, question }: { canWrite: boolean; index: number; onDelete: () => void; onUpdate: (update: Partial<DraftQuestion>) => void; question: DraftQuestion }) {
  return <article className="border border-[#d8d5cc] bg-[#fdfcf8] p-4"><div className="flex items-center justify-between"><div className="flex items-center gap-2 text-sm font-black"><GripVertical className="size-4 text-[#a6a39b]" />Question {index + 1}</div>{canWrite ? <button className="inline-flex size-8 items-center justify-center text-[#8f221c] hover:bg-[#f6e9e6]" onClick={onDelete} title="Remove question" type="button"><Trash2 className="size-4" /></button> : null}</div><div className="mt-4 grid gap-4 md:grid-cols-[minmax(0,1fr)_160px]"><Field label="Question"><input className="field-control" disabled={!canWrite} onChange={(event) => onUpdate({ label: event.target.value })} placeholder="What should we know?" value={question.label} /></Field><Field label="Answer type"><select className="field-control" disabled={!canWrite} onChange={(event) => onUpdate({ answerType: event.target.value as QuestionAnswerType })} value={question.answerType}>{answerTypes.map((type) => <option key={type.value} value={type.value}>{type.label}</option>)}</select></Field></div><div className="mt-4 grid gap-4 md:grid-cols-[minmax(0,1fr)_minmax(0,1.6fr)]"><Field label="Field key"><input className="field-control font-mono" disabled={!canWrite} onChange={(event) => onUpdate({ key: event.target.value.replace(/[^a-z0-9_]/g, "_") })} placeholder="project_locations" value={question.key} /></Field><Field label="Guidance"><input className="field-control" disabled={!canWrite} onChange={(event) => onUpdate({ helpText: event.target.value })} placeholder="Optional context shown to the organization" value={question.helpText} /></Field></div>{isChoiceType(question.answerType) ? <div className="mt-4"><Field hint="Separate choices with commas." label="Choices"><input className="field-control" disabled={!canWrite} onChange={(event) => onUpdate({ options: event.target.value })} placeholder="Apartments, Villas, Plots" value={question.options} /></Field></div> : null}<label className="mt-4 flex items-center gap-2 text-sm font-bold text-[#4e4c46]"><input checked={question.required} disabled={!canWrite} onChange={(event) => onUpdate({ required: event.target.checked })} type="checkbox" />Required answer</label></article>;
}

function Field({ children, hint, label }: { children: React.ReactNode; hint?: string; label: string }) { return <label className="block"><span className="block text-sm font-bold text-[#4e4c46]">{label}</span>{hint ? <span className="mt-1 block text-xs leading-5 text-[#6d6b64]">{hint}</span> : null}<span className="mt-2 block">{children}</span></label>; }

function CategoryDialog({ category, isSaving, onClose, onSubmit }: { category: PlatformCategory | null; isSaving: boolean; onClose: () => void; onSubmit: (event: FormEvent<HTMLFormElement>) => void }) { return <div className="fixed inset-0 z-30 flex items-center justify-center bg-[#171714]/40 p-5"><form className="w-full max-w-lg border border-[#171714] bg-[#fffefa] shadow-2xl" onSubmit={onSubmit}><div className="flex items-center justify-between border-b border-[#171714] p-5"><div><p className="utility-label !text-[#d73a2f]">Category</p><h2 className="mt-2 text-xl font-black">{category ? "Edit category" : "New category"}</h2></div><button className="inline-flex size-10 items-center justify-center hover:bg-[#f0eee8]" onClick={onClose} title="Close" type="button"><X className="size-5" /></button></div><div className="space-y-5 p-5"><Field label="Name"><input autoFocus className="field-control" defaultValue={category?.name} name="name" required /></Field><Field hint="Lowercase letters, numbers and underscores only." label="Key"><input className="field-control font-mono" defaultValue={category?.key} disabled={Boolean(category)} name="key" pattern="[a-z0-9][a-z0-9_]*" required /></Field><Field label="Description"><textarea className="field-control min-h-24 resize-y" defaultValue={category?.description ?? ""} name="description" /></Field><Field label="Status"><select className="field-control" defaultValue={category?.status ?? "active"} name="status"><option value="active">Active</option><option value="inactive">Inactive</option></select></Field></div><div className="flex justify-end gap-3 border-t border-[#d8d5cc] p-5"><button className="h-10 px-4 text-sm font-bold hover:bg-[#f0eee8]" onClick={onClose} type="button">Cancel</button><button className="inline-flex h-10 items-center gap-2 bg-[#171714] px-4 text-sm font-bold text-white hover:bg-[#d73a2f] disabled:opacity-60" disabled={isSaving} type="submit">{isSaving ? <Loader2 className="size-4 animate-spin" /> : null}{category ? "Save category" : "Create category"}</button></div></form></div>; }

function TemplateDialog({ categoryName, isSaving, onClose, onSubmit }: { categoryName: string; isSaving: boolean; onClose: () => void; onSubmit: (event: FormEvent<HTMLFormElement>) => void }) { return <div className="fixed inset-0 z-30 flex items-center justify-center bg-[#171714]/40 p-5"><form className="w-full max-w-lg border border-[#171714] bg-[#fffefa] shadow-2xl" onSubmit={onSubmit}><div className="flex items-center justify-between border-b border-[#171714] p-5"><div><p className="utility-label !text-[#d73a2f]">{categoryName}</p><h2 className="mt-2 text-xl font-black">New draft template</h2></div><button className="inline-flex size-10 items-center justify-center hover:bg-[#f0eee8]" onClick={onClose} title="Close" type="button"><X className="size-5" /></button></div><div className="space-y-5 p-5"><Field label="Template title"><input autoFocus className="field-control" name="title" placeholder="Real estate discovery" required /></Field><Field label="Description"><textarea className="field-control min-h-24 resize-y" name="description" placeholder="A short description for the platform team." /></Field></div><div className="flex justify-end gap-3 border-t border-[#d8d5cc] p-5"><button className="h-10 px-4 text-sm font-bold hover:bg-[#f0eee8]" onClick={onClose} type="button">Cancel</button><button className="inline-flex h-10 items-center gap-2 bg-[#171714] px-4 text-sm font-bold text-white hover:bg-[#d73a2f] disabled:opacity-60" disabled={isSaving} type="submit">{isSaving ? <Loader2 className="size-4 animate-spin" /> : null}Create draft</button></div></form></div>; }
