import { useState } from "react";
import { Search, Loader2, ShieldCheck, AlertTriangle, ShieldAlert } from "lucide-react";
import { quickCheck } from "@/api/client";
import Skeleton from "@/components/ui/Skeleton";
import ErrorState from "@/components/ui/ErrorState";

const VERDICTS = {
  green: {
    label: "Safe",
    Icon: ShieldCheck,
    card: "border-emerald-300 bg-emerald-50 dark:border-emerald-900 dark:bg-emerald-950/50",
    badge: "bg-emerald-600 text-white",
    text: "text-emerald-800 dark:text-emerald-200",
  },
  yellow: {
    label: "Caution",
    Icon: AlertTriangle,
    card: "border-amber-300 bg-amber-50 dark:border-amber-900 dark:bg-amber-950/50",
    badge: "bg-amber-500 text-white",
    text: "text-amber-900 dark:text-amber-200",
  },
  red: {
    label: "Danger",
    Icon: ShieldAlert,
    card: "border-red-300 bg-red-50 dark:border-red-900 dark:bg-red-950/50",
    badge: "bg-red-600 text-white",
    text: "text-red-800 dark:text-red-200",
  },
};

export default function QuickCheck() {
  const [query, setQuery] = useState("");
  const [status, setStatus] = useState("idle"); // idle | loading | success | error
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null); // { kind: "notfound" | "failure", message }
  const [slow, setSlow] = useState(false);

  async function run() {
    const q = query.trim();
    if (!q || status === "loading") return;
    setStatus("loading");
    setResult(null);
    setError(null);
    setSlow(false);
    const slowTimer = setTimeout(() => setSlow(true), 10000);
    try {
      const data = await quickCheck(q);
      setResult(data);
      setStatus("success");
    } catch (err) {
      const apiMsg = err?.response?.data?.error?.message;
      if (err?.response?.status === 404) {
        setError({
          kind: "notfound",
          message: apiMsg || "Cell line not found — check the spelling, catalog number, or RRID.",
        });
      } else {
        setError({ kind: "failure", message: apiMsg || "Something went wrong. Please try again." });
      }
      setStatus("error");
    } finally {
      clearTimeout(slowTimer);
    }
  }

  function handleSubmit(e) {
    e.preventDefault();
    run();
  }

  return (
    <div className="space-y-6">
      <form onSubmit={handleSubmit} className="flex gap-2">
        <div className="relative flex-1">
          <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
          <input
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Cell line name, catalog #, or RRID — e.g. MDA-MB-435"
            className="h-11 w-full rounded-md border border-input bg-background pl-9 pr-3 text-sm outline-none ring-offset-background placeholder:text-muted-foreground focus-visible:ring-2 focus-visible:ring-ring"
            aria-label="Cell line query"
          />
        </div>
        <button
          type="submit"
          disabled={status === "loading" || !query.trim()}
          className="inline-flex h-11 items-center gap-2 rounded-md bg-primary px-5 text-sm font-medium text-primary-foreground disabled:opacity-50"
        >
          {status === "loading" ? <Loader2 className="h-4 w-4 animate-spin" /> : <Search className="h-4 w-4" />}
          {status === "loading" ? "Checking…" : "Check"}
        </button>
      </form>

      {status === "loading" && (
        <div className="space-y-3">
          <VerdictSkeleton />
          {slow && (
            <p className="text-sm text-muted-foreground">
              Still searching… Cellosaurus can be slow sometimes.
            </p>
          )}
        </div>
      )}

      {status === "error" && error?.kind === "notfound" && (
        <ErrorState title="Not found" message={error.message} />
      )}
      {status === "error" && error?.kind === "failure" && (
        <ErrorState message={error.message} onRetry={run} />
      )}

      {status === "success" && result && <VerdictCard result={result} />}
    </div>
  );
}

function VerdictSkeleton() {
  return (
    <div className="rounded-xl border p-6">
      <div className="flex items-center justify-between gap-4">
        <div className="space-y-2">
          <Skeleton className="h-3 w-16" />
          <Skeleton className="h-7 w-40" />
        </div>
        <Skeleton className="h-9 w-24 rounded-full" />
      </div>
      <div className="mt-6 grid gap-x-6 gap-y-4 sm:grid-cols-2">
        <SkelField />
        <SkelField />
        <div className="space-y-1.5 sm:col-span-2">
          <Skeleton className="h-3 w-16" />
          <Skeleton className="h-4 w-3/4" />
        </div>
      </div>
      <div className="mt-6 space-y-2">
        <Skeleton className="h-3 w-10" />
        <Skeleton className="h-4 w-full" />
        <Skeleton className="h-4 w-full" />
        <Skeleton className="h-4 w-2/3" />
      </div>
    </div>
  );
}

function SkelField() {
  return (
    <div className="space-y-1.5">
      <Skeleton className="h-3 w-14" />
      <Skeleton className="h-4 w-28" />
    </div>
  );
}

function VerdictCard({ result }) {
  const v = VERDICTS[result.verdict] ?? VERDICTS.yellow;
  const { Icon } = v;
  const id = result.identity ?? {};

  return (
    <div className={`rounded-xl border p-6 ${v.card}`}>
      <div className="flex items-center justify-between gap-4">
        <div>
          <div className="text-xs uppercase tracking-wide text-muted-foreground">Verdict</div>
          <h2 className={`mt-1 text-2xl font-bold ${v.text}`}>{id.correct_name || result.query}</h2>
        </div>
        <span className={`inline-flex items-center gap-2 rounded-full px-4 py-2 text-sm font-semibold ${v.badge}`}>
          <Icon className="h-4 w-4" aria-hidden="true" />
          {v.label}
        </span>
      </div>

      <dl className="mt-6 grid gap-x-6 gap-y-3 sm:grid-cols-2">
        <Field label="RRID" value={id.rrid} mono />
        <Field label="Species" value={id.species} />
        <Field label="Originating lab" value={id.source_lab} />
        <Field label="True origin" value={id.true_origin} full />
        {id.synonyms?.length > 0 && (
          <Field label="Also known as" value={id.synonyms.join(", ")} full />
        )}
      </dl>

      {result.explanation && (
        <div className="mt-6">
          <div className="text-xs uppercase tracking-wide text-muted-foreground">Why</div>
          <p className="mt-1 text-sm leading-relaxed">{result.explanation}</p>
        </div>
      )}

      {result.retractions?.length > 0 && (
        <div className="mt-6">
          <div className="text-xs uppercase tracking-wide text-muted-foreground">Related publications</div>
          <ul className="mt-2 space-y-2">
            {result.retractions.map((p, i) => (
              <li key={i} className="flex items-start gap-2 text-sm">
                <span
                  className={`mt-0.5 shrink-0 rounded px-1.5 py-0.5 text-[10px] font-semibold ${
                    p.reason === "Retracted"
                      ? "bg-red-600 text-white"
                      : "bg-black/5 text-muted-foreground dark:bg-white/10"
                  }`}
                >
                  {p.reason === "Retracted" ? "Retracted" : "Related"}
                </span>
                <span>
                  {p.url ? (
                    <a href={p.url} target="_blank" rel="noreferrer"
                       className="underline underline-offset-2 hover:opacity-80">
                      {p.title}
                    </a>
                  ) : (
                    p.title
                  )}
                  {(p.journal || p.year) && (
                    <span className="text-muted-foreground">
                      {" — "}
                      {[p.journal, p.year].filter(Boolean).join(", ")}
                    </span>
                  )}
                </span>
              </li>
            ))}
          </ul>
        </div>
      )}

      {result.next_steps?.length > 0 && (
        <div className="mt-6">
          <div className="text-xs uppercase tracking-wide text-muted-foreground">Next steps</div>
          <ul className="mt-2 space-y-1.5 text-sm">
            {result.next_steps.map((step, i) => (
              <li key={i} className="flex gap-2">
                <span className={`mt-2 h-1.5 w-1.5 shrink-0 rounded-full ${v.badge}`} />
                <span>{step}</span>
              </li>
            ))}
          </ul>
        </div>
      )}

      {result.sources?.length > 0 && (
        <p className="mt-5 text-xs text-muted-foreground">via {result.sources.join(", ")}</p>
      )}
    </div>
  );
}

function Field({ label, value, mono, full }) {
  if (!value) return null;
  return (
    <div className={full ? "sm:col-span-2" : ""}>
      <dt className="text-xs uppercase tracking-wide text-muted-foreground">{label}</dt>
      <dd className={`mt-0.5 text-sm ${mono ? "font-mono" : ""}`}>{value}</dd>
    </div>
  );
}
