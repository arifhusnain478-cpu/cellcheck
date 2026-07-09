import { useState } from "react";
import { Loader2, FileText, Copy, Check, CheckCircle2, AlertTriangle } from "lucide-react";
import { generateMethods } from "@/api/client";
import Skeleton from "@/components/ui/Skeleton";
import ErrorState from "@/components/ui/ErrorState";

const JOURNALS = ["Nature", "Cell", "Science", "Cancer Research", "PLOS ONE"];

const EMPTY = {
  cell_line: "",
  source: "",
  authentication_service: "",
  authentication_date: "",
  mycoplasma_test_date: "",
  passage_range: "",
  target_journal: "",
};

const EXAMPLE = {
  cell_line: "MCF-7",
  source: "ATCC (HTB-22)",
  authentication_service: "ATCC STR profiling service",
  authentication_date: "2026-05-10",
  mycoplasma_test_date: "2026-05-08",
  passage_range: "8-15",
  target_journal: "Cancer Research",
};

export default function MethodsGenerator() {
  const [form, setForm] = useState(EMPTY);
  const [status, setStatus] = useState("idle"); // idle | loading | success | error
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null); // { kind: "validation" | "failure", message }
  const [copied, setCopied] = useState(false);

  const set = (k) => (e) => setForm({ ...form, [k]: e.target.value });

  async function run() {
    if (status === "loading") return;
    if (!form.cell_line.trim()) {
      setError({ kind: "validation", message: "Enter a cell line name." });
      setResult(null);
      setStatus("error");
      return;
    }
    setStatus("loading");
    setResult(null);
    setError(null);
    setCopied(false);
    try {
      const data = await generateMethods({ ...form, cell_line: form.cell_line.trim() });
      setResult(data);
      setStatus("success");
    } catch (err) {
      setError({
        kind: "failure",
        message: err?.response?.data?.error?.message || "Something went wrong. Please try again.",
      });
      setStatus("error");
    }
  }

  function handleSubmit(e) {
    e.preventDefault();
    run();
  }

  async function copyParagraph() {
    try {
      await navigator.clipboard.writeText(result.methods_paragraph);
      setCopied(true);
      setTimeout(() => setCopied(false), 1500);
    } catch {
      /* clipboard blocked; ignore */
    }
  }

  return (
    <div className="space-y-6">
      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <div className="mb-1 flex items-center justify-between">
            <label className="text-sm font-medium">Cell line</label>
            <button
              type="button"
              onClick={() => { setForm(EXAMPLE); setResult(null); setError(null); setStatus("idle"); }}
              className="text-xs text-muted-foreground underline underline-offset-2 hover:text-foreground"
            >
              Load MCF-7 example
            </button>
          </div>
          <input value={form.cell_line} onChange={set("cell_line")}
            placeholder="e.g. MCF-7" className={inputCls} />
        </div>

        <div className="grid gap-4 sm:grid-cols-2">
          <Field label="Source / catalog">
            <input value={form.source} onChange={set("source")} placeholder="e.g. ATCC (HTB-22)" className={inputCls} />
          </Field>
          <Field label="Authentication service / method">
            <input value={form.authentication_service} onChange={set("authentication_service")}
              placeholder="e.g. ATCC STR profiling" className={inputCls} />
          </Field>
          <Field label="Authentication date">
            <input type="date" value={form.authentication_date} onChange={set("authentication_date")} className={inputCls} />
          </Field>
          <Field label="Mycoplasma test date">
            <input type="date" value={form.mycoplasma_test_date} onChange={set("mycoplasma_test_date")} className={inputCls} />
          </Field>
          <Field label="Passage range">
            <input value={form.passage_range} onChange={set("passage_range")} placeholder="e.g. 8-15" className={inputCls} />
          </Field>
          <Field label="Target journal">
            <input value={form.target_journal} onChange={set("target_journal")} list="journals"
              placeholder="e.g. Cancer Research" className={inputCls} />
            <datalist id="journals">
              {JOURNALS.map((j) => <option key={j} value={j} />)}
            </datalist>
          </Field>
        </div>

        <button type="submit" disabled={status === "loading"}
          className="inline-flex h-11 items-center gap-2 rounded-md bg-primary px-5 text-sm font-medium text-primary-foreground disabled:opacity-50">
          {status === "loading" ? <Loader2 className="h-4 w-4 animate-spin" /> : <FileText className="h-4 w-4" />}
          {status === "loading" ? "Generating…" : "Generate methods paragraph"}
        </button>
      </form>

      {status === "loading" && <MethodsSkeleton />}

      {status === "error" && error?.kind === "validation" && (
        <ErrorState title="Could not generate" message={error.message} />
      )}
      {status === "error" && error?.kind === "failure" && (
        <ErrorState title="Could not generate" message={error.message} onRetry={run} />
      )}

      {status === "success" && result && (
        <div className="space-y-4">
          <div className="rounded-xl border bg-card p-6">
            <div className="mb-3 flex items-center justify-between gap-4">
              <div className="text-xs uppercase tracking-wide text-muted-foreground">
                Methods paragraph{result.rrid_used ? ` — RRID:${result.rrid_used}` : ""}
              </div>
              <button onClick={copyParagraph}
                className="inline-flex items-center gap-1.5 rounded-md border px-2.5 py-1 text-xs hover:bg-muted">
                {copied ? <Check className="h-3.5 w-3.5" /> : <Copy className="h-3.5 w-3.5" />}
                {copied ? "Copied" : "Copy"}
              </button>
            </div>
            <p className="text-sm leading-relaxed">{result.methods_paragraph}</p>
          </div>

          <ComplianceCard status={result.compliance_status} sources={result.sources} />
        </div>
      )}
    </div>
  );
}

function MethodsSkeleton() {
  return (
    <div className="space-y-4">
      <div className="rounded-xl border bg-card p-6">
        <div className="mb-3 flex items-center justify-between">
          <Skeleton className="h-3 w-40" />
          <Skeleton className="h-6 w-16" />
        </div>
        <div className="space-y-2">
          <Skeleton className="h-4 w-full" />
          <Skeleton className="h-4 w-full" />
          <Skeleton className="h-4 w-full" />
          <Skeleton className="h-4 w-2/3" />
        </div>
      </div>
      <div className="rounded-xl border bg-card p-6">
        <div className="flex items-center justify-between">
          <Skeleton className="h-3 w-32" />
          <Skeleton className="h-6 w-24 rounded-full" />
        </div>
        <Skeleton className="mt-3 h-4 w-1/2" />
      </div>
    </div>
  );
}

function ComplianceCard({ status, sources }) {
  if (!status) return null;
  const ok = status.compliant;
  return (
    <div className="rounded-xl border bg-card p-6">
      <div className="flex items-center justify-between gap-4">
        <div className="text-xs uppercase tracking-wide text-muted-foreground">Journal compliance</div>
        <span className={`inline-flex items-center gap-1.5 rounded-full px-3 py-1 text-xs font-semibold ${
          ok ? "bg-emerald-600 text-white" : "bg-amber-500 text-white"}`}>
          {ok ? <CheckCircle2 className="h-3.5 w-3.5" /> : <AlertTriangle className="h-3.5 w-3.5" />}
          {ok ? "Compliant" : "Incomplete"}
        </span>
      </div>
      <p className="mt-2 text-sm">Policy applied: <span className="font-medium">{status.journal}</span></p>
      {status.missing_fields?.length > 0 && (
        <div className="mt-3">
          <div className="text-xs uppercase tracking-wide text-muted-foreground">Missing for full compliance</div>
          <ul className="mt-1 space-y-1 text-sm">
            {status.missing_fields.map((f) => (
              <li key={f} className="flex gap-2">
                <AlertTriangle className="mt-0.5 h-3.5 w-3.5 shrink-0 text-amber-500" />
                <span>{f}</span>
              </li>
            ))}
          </ul>
        </div>
      )}
      {sources?.length > 0 && (
        <p className="mt-4 text-xs text-muted-foreground">via {sources.join(", ")}</p>
      )}
    </div>
  );
}

const inputCls =
  "h-11 w-full rounded-md border border-input bg-background px-3 text-sm outline-none placeholder:text-muted-foreground focus-visible:ring-2 focus-visible:ring-ring";

function Field({ label, children }) {
  return (
    <div>
      <label className="mb-1 block text-sm font-medium">{label}</label>
      {children}
    </div>
  );
}
