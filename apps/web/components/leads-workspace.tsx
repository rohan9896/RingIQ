"use client";

import { ChangeEvent, useCallback, useEffect, useRef, useState } from "react";
import {
  Check,
  FileSpreadsheet,
  Loader2,
  Search,
  TriangleAlert,
  Upload,
  UsersRound,
  X,
} from "lucide-react";
import { useAuth } from "@clerk/nextjs";
import {
  createLeadImport,
  fetchLeadImports,
  fetchLeads,
  type Lead,
  type LeadImport,
  type LeadImportDetail,
} from "@/lib/api-client";

type Mapping = { name: string; email: string; phone_number: string };

function normalizeHeader(value: string) {
  return value
    .trim()
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "_")
    .replace(/^_+|_+$/g, "");
}
function parseHeaders(content: string) {
  const line = content.replace(/^\uFEFF/, "").split(/\r?\n/, 1)[0] ?? "";
  const result: string[] = [];
  let value = "";
  let quoted = false;
  for (let index = 0; index < line.length; index += 1) {
    const char = line[index];
    if (char === '"') {
      if (quoted && line[index + 1] === '"') {
        value += char;
        index += 1;
      } else quoted = !quoted;
    } else if (char === "," && !quoted) {
      result.push(value.trim());
      value = "";
    } else value += char;
  }
  result.push(value.trim());
  return result.filter(Boolean);
}
function suggestedMapping(headers: string[]): Mapping {
  const pick = (aliases: string[]) =>
    headers.find((header) => aliases.includes(normalizeHeader(header))) ?? "";
  return {
    name: pick(["name", "full_name", "lead_name"]),
    email: pick(["email", "email_address", "mail"]),
    phone_number: pick([
      "phone",
      "phone_number",
      "mobile",
      "mobile_number",
      "contact_number",
    ]),
  };
}
function friendlyError(error: unknown) {
  const value =
    error instanceof Error ? error.message : "We could not process that file.";
  if (value.includes("required_columns_missing"))
    return "Map all three required columns before importing.";
  return value.replaceAll("_", " ");
}

export function LeadsWorkspace() {
  const { getToken } = useAuth();
  const fileInput = useRef<HTMLInputElement>(null);
  const [leads, setLeads] = useState<Lead[]>([]);
  const [imports, setImports] = useState<LeadImport[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isUploading, setIsUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);
  const [query, setQuery] = useState("");
  const [upload, setUpload] = useState<{
    filename: string;
    content: string;
    headers: string[];
    mapping: Mapping;
  } | null>(null);
  const [result, setResult] = useState<LeadImportDetail | null>(null);
  const withToken = useCallback(
    async <T,>(callback: (token: string) => Promise<T>) => {
      const token = await getToken();
      if (!token) throw new Error("unauthorized");
      return callback(token);
    },
    [getToken],
  );
  const load = useCallback(
    async (search = "") => {
      const [nextLeads, nextImports] = await Promise.all([
        withToken((token) => fetchLeads(token, search)),
        withToken(fetchLeadImports),
      ]);
      setLeads(nextLeads);
      setImports(nextImports);
    },
    [withToken],
  );
  useEffect(() => {
    let cancelled = false;
    async function initialize() {
      try {
        const [nextLeads, nextImports] = await Promise.all([
          withToken((token) => fetchLeads(token)),
          withToken(fetchLeadImports),
        ]);
        if (cancelled) return;
        setLeads(nextLeads);
        setImports(nextImports);
      } catch (caught) {
        if (!cancelled) setError(friendlyError(caught));
      } finally {
        if (!cancelled) setIsLoading(false);
      }
    }
    void initialize();
    return () => {
      cancelled = true;
    };
  }, [withToken]);
  async function handleFile(event: ChangeEvent<HTMLInputElement>) {
    const file = event.target.files?.[0];
    if (!file) return;
    if (!file.name.toLowerCase().endsWith(".csv")) {
      setError("Choose a CSV file.");
      return;
    }
    const content = await file.text();
    const headers = parseHeaders(content);
    if (!headers.length) {
      setError("This CSV does not contain a header row.");
      return;
    }
    setUpload({
      filename: file.name,
      content,
      headers,
      mapping: suggestedMapping(headers),
    });
    setResult(null);
    event.target.value = "";
  }
  async function importCsv() {
    if (!upload) return;
    if (
      !upload.mapping.name ||
      !upload.mapping.email ||
      !upload.mapping.phone_number
    ) {
      setError("Map name, email, and phone number before importing.");
      return;
    }
    try {
      setIsUploading(true);
      setError(null);
      const imported = await withToken((token) =>
        createLeadImport(token, {
          filename: upload.filename,
          csv_content: upload.content,
          column_mapping: upload.mapping,
        }),
      );
      setResult(imported);
      setUpload(null);
      await load(query);
      setNotice(
        `${imported.imported_rows} leads added from ${imported.filename}.`,
      );
    } catch (caught) {
      setError(friendlyError(caught));
    } finally {
      setIsUploading(false);
    }
  }
  async function runSearch(event: React.FormEvent) {
    event.preventDefault();
    try {
      setIsLoading(true);
      await load(query);
    } catch (caught) {
      setError(friendlyError(caught));
    } finally {
      setIsLoading(false);
    }
  }
  return (
    <div className="mx-auto max-w-6xl">
      <header className="border-b border-[#171714] pb-7">
        <div className="flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
          <div>
            <p className="utility-label !text-[#d73a2f]">Leads</p>
            <h1 className="mt-3 text-3xl font-black text-[#171714] sm:text-4xl">
              Lead inventory
            </h1>
            <p className="mt-3 max-w-2xl text-sm leading-6 text-[#6d6b64]">
              Import and review the people your team may contact. Duplicate and
              invalid rows stay visible so nothing disappears without an
              explanation.
            </p>
          </div>
          <button
            className="inline-flex h-10 items-center gap-2 bg-[#171714] px-4 text-sm font-bold text-white hover:bg-[#d73a2f]"
            onClick={() => fileInput.current?.click()}
            type="button"
          >
            <Upload className="size-4" />
            Import CSV
          </button>
          <input
            accept=".csv,text/csv"
            className="hidden"
            onChange={handleFile}
            ref={fileInput}
            type="file"
          />
        </div>
      </header>
      {error ? (
        <Alert type="error" message={error} onDismiss={() => setError(null)} />
      ) : null}
      {notice ? (
        <Alert
          type="success"
          message={notice}
          onDismiss={() => setNotice(null)}
        />
      ) : null}
      {upload ? (
        <ImportMapper
          isUploading={isUploading}
          onCancel={() => setUpload(null)}
          onImport={importCsv}
          onMapping={(field, value) =>
            setUpload((current) =>
              current
                ? {
                    ...current,
                    mapping: { ...current.mapping, [field]: value },
                  }
                : current,
            )
          }
          upload={upload}
        />
      ) : null}
      {result ? <ImportResult result={result} /> : null}
      <section className="mt-7">
        <div className="flex flex-col gap-4 border border-[#171714] bg-[#fffefa] p-5 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <p className="utility-label !text-[#2f4e6f]">Current leads</p>
            <p className="mt-2 text-sm text-[#6d6b64]">
              Up to 200 matching records.
            </p>
          </div>
          <form className="flex w-full max-w-sm gap-2" onSubmit={runSearch}>
            <input
              className="field-control"
              onChange={(event) => setQuery(event.target.value)}
              placeholder="Search name, email or phone"
              value={query}
            />
            <button
              className="inline-flex size-10 shrink-0 items-center justify-center border border-[#171714] hover:bg-[#f0eee8]"
              title="Search leads"
              type="submit"
            >
              <Search className="size-4" />
            </button>
          </form>
        </div>
        {isLoading ? (
          <div className="flex min-h-48 items-center justify-center border-x border-b border-[#d8d5cc] bg-[#fffefa] text-sm font-bold text-[#6d6b64]">
            <Loader2 className="mr-3 size-5 animate-spin" />
            Loading leads
          </div>
        ) : (
          <LeadTable leads={leads} />
        )}
      </section>
      <section className="mt-7 border border-[#d8d5cc] bg-[#fffefa]">
        <div className="border-b border-[#d8d5cc] px-5 py-4">
          <p className="utility-label">Recent imports</p>
        </div>
        <div className="divide-y divide-[#e3e0d8]">
          {imports.map((item) => (
            <div
              className="grid gap-3 px-5 py-4 sm:grid-cols-[minmax(0,1fr)_repeat(3,100px)] sm:items-center"
              key={item.id}
            >
              <div>
                <p className="truncate text-sm font-black">{item.filename}</p>
                <p className="mt-1 text-xs text-[#6d6b64]">
                  {new Date(item.created_at).toLocaleString()}
                </p>
              </div>
              <ImportMetric
                label="Added"
                value={item.imported_rows}
                tone="success"
              />
              <ImportMetric
                label="Invalid"
                value={item.invalid_rows}
                tone="error"
              />
              <ImportMetric
                label="Duplicates"
                value={item.duplicate_rows}
                tone="neutral"
              />
            </div>
          ))}
          {!imports.length ? (
            <div className="p-5 text-sm text-[#6d6b64]">
              No CSV imports yet.
            </div>
          ) : null}
        </div>
      </section>
    </div>
  );
}

function Alert({
  message,
  onDismiss,
  type,
}: {
  message: string;
  onDismiss: () => void;
  type: "error" | "success";
}) {
  const success = type === "success";
  return (
    <div
      className={`mt-6 flex items-center gap-3 border-l-2 p-4 text-sm ${success ? "border-[#66735b] bg-[#eef0ea] text-[#4d5b44]" : "border-[#d73a2f] bg-[#f6e9e6] text-[#8f221c]"}`}
    >
      {success ? (
        <Check className="size-4" />
      ) : (
        <TriangleAlert className="size-4" />
      )}
      <p>{message}</p>
      <button
        className="ml-auto"
        onClick={onDismiss}
        title="Dismiss"
        type="button"
      >
        <X className="size-4" />
      </button>
    </div>
  );
}
function ImportMapper({
  isUploading,
  onCancel,
  onImport,
  onMapping,
  upload,
}: {
  isUploading: boolean;
  onCancel: () => void;
  onImport: () => void;
  onMapping: (field: keyof Mapping, value: string) => void;
  upload: { filename: string; headers: string[]; mapping: Mapping };
}) {
  const fields: { key: keyof Mapping; label: string }[] = [
    { key: "name", label: "Name" },
    { key: "email", label: "Email" },
    { key: "phone_number", label: "Phone number" },
  ];
  return (
    <section className="mt-7 border border-[#171714] bg-[#fffefa]">
      <div className="flex items-start justify-between border-b border-[#171714] p-5">
        <div>
          <p className="utility-label !text-[#d73a2f]">Ready to import</p>
          <h2 className="mt-2 text-xl font-black">Check required columns</h2>
          <p className="mt-2 text-sm text-[#6d6b64]">{upload.filename}</p>
        </div>
        <FileSpreadsheet className="size-6 text-[#2f4e6f]" />
      </div>
      <div className="grid gap-5 p-5 md:grid-cols-3">
        {fields.map((field) => (
          <label className="block" key={field.key}>
            <span className="text-sm font-bold">{field.label}</span>
            <select
              className="field-control mt-2"
              onChange={(event) => onMapping(field.key, event.target.value)}
              value={upload.mapping[field.key]}
            >
              <option value="">Choose a CSV column</option>
              {upload.headers.map((header) => (
                <option key={header} value={header}>
                  {header}
                </option>
              ))}
            </select>
          </label>
        ))}
      </div>
      <div className="flex justify-end gap-3 border-t border-[#d8d5cc] p-5">
        <button
          className="h-10 px-4 text-sm font-bold hover:bg-[#f0eee8]"
          onClick={onCancel}
          type="button"
        >
          Cancel
        </button>
        <button
          className="inline-flex h-10 items-center gap-2 bg-[#171714] px-4 text-sm font-bold text-white hover:bg-[#d73a2f] disabled:opacity-60"
          disabled={isUploading}
          onClick={onImport}
          type="button"
        >
          {isUploading ? (
            <Loader2 className="size-4 animate-spin" />
          ) : (
            <Upload className="size-4" />
          )}
          Import leads
        </button>
      </div>
    </section>
  );
}
function ImportResult({ result }: { result: LeadImportDetail }) {
  return (
    <section className="mt-7 border border-[#aeb6a7] bg-[#eef0ea]">
      <div className="flex items-start gap-3 p-5">
        <Check className="mt-0.5 size-5 text-[#4d5b44]" />
        <div>
          <p className="utility-label !text-[#4d5b44]">Import complete</p>
          <h2 className="mt-2 text-xl font-black">{result.filename}</h2>
        </div>
      </div>
      <div className="grid gap-px bg-[#aeb6a7] sm:grid-cols-3">
        <ImportMetric
          label="Added"
          value={result.imported_rows}
          tone="success"
        />
        <ImportMetric
          label="Invalid"
          value={result.invalid_rows}
          tone="error"
        />
        <ImportMetric
          label="Duplicates"
          value={result.duplicate_rows}
          tone="neutral"
        />
      </div>
      {result.rows.some((row) => row.status !== "imported") ? (
        <div className="border-t border-[#aeb6a7] bg-[#fffefa] p-5">
          <p className="text-sm font-bold">Rows needing attention</p>
          <div className="mt-3 space-y-2">
            {result.rows
              .filter((row) => row.status !== "imported")
              .slice(0, 10)
              .map((row) => (
                <div className="flex gap-3 text-sm" key={row.id}>
                  <span className="font-mono text-[#6d6b64]">
                    Row {row.row_number}
                  </span>
                  <span className="text-[#8f221c]">{row.error_message}</span>
                </div>
              ))}
          </div>
        </div>
      ) : null}
    </section>
  );
}
function ImportMetric({
  label,
  tone,
  value,
}: {
  label: string;
  tone: "success" | "error" | "neutral";
  value: number;
}) {
  const color =
    tone === "success"
      ? "text-[#4d5b44]"
      : tone === "error"
        ? "text-[#8f221c]"
        : "text-[#4e4c46]";
  return (
    <div className="bg-[#fffefa] p-4">
      <p className="utility-label">{label}</p>
      <p className={`mt-2 text-2xl font-black ${color}`}>{value}</p>
    </div>
  );
}
function LeadTable({ leads }: { leads: Lead[] }) {
  return (
    <div className="overflow-x-auto border-x border-b border-[#d8d5cc] bg-[#fffefa]">
      <table className="w-full min-w-[640px] text-left">
        <thead className="border-b border-[#d8d5cc] bg-[#f7f6f2] text-xs uppercase text-[#6d6b64]">
          <tr>
            <th className="px-5 py-3 font-bold">Lead</th>
            <th className="px-5 py-3 font-bold">Contact</th>
            <th className="px-5 py-3 font-bold">Optional details</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-[#e3e0d8]">
          {leads.map((lead) => (
            <tr key={lead.id}>
              <td className="px-5 py-4">
                <p className="font-bold">{lead.name}</p>
                <p className="mt-1 text-xs text-[#6d6b64]">
                  Added {new Date(lead.created_at).toLocaleDateString()}
                </p>
              </td>
              <td className="px-5 py-4 text-sm">
                <p>{lead.email}</p>
                <p className="mt-1 text-[#6d6b64]">
                  {lead.normalized_phone_number}
                </p>
              </td>
              <td className="px-5 py-4 text-sm text-[#6d6b64]">
                {Object.entries(lead.attributes_json).map(([key, value]) => (
                  <span className="mr-2 inline-block" key={key}>
                    {key.replaceAll("_", " ")}: {String(value)}
                  </span>
                ))}
              </td>
            </tr>
          ))}
          {!leads.length ? (
            <tr>
              <td
                className="px-5 py-10 text-center text-sm text-[#6d6b64]"
                colSpan={3}
              >
                <UsersRound className="mx-auto mb-3 size-5" />
                No leads match this view. Import a CSV to begin.
              </td>
            </tr>
          ) : null}
        </tbody>
      </table>
    </div>
  );
}
