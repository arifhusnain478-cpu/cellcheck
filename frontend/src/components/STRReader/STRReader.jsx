import { useState } from "react";
import { Loader2, ShieldCheck, AlertTriangle, ShieldAlert, FlaskConical } from "lucide-react";
import { analyzeSTR } from "@/api/client";
import Skeleton from "@/components/ui/Skeleton";
import ErrorState from "@/components/ui/ErrorState";

const VERDICTS = {
  green: {
    label: "Match",
    Icon: ShieldCheck,
    card: "border-emerald-300 bg-emerald-50 dark:border-emerald-900 dark:bg-emerald-950/50",
    badge: "bg-emerald-600 text-white",
    text: "text-emerald-800 dark:text-emerald-200",
  },
  yellow: {
    label: "Inconclusive",
    Icon: AlertTriangle,
    card: "border-amber-300 bg-amber-50 dark:border-amber-900 dark:bg-amber-950/50",
    badge: "bg-amber-500 text-white",
    text: "text-amber-900 dark:text-amber-200",
  },
  red: {
    label: "Mismatch",
    Icon: ShieldAlert,
    card: "border-red-300 bg-red-50 dark:border-red-900 dark:bg-red-950/50",
    badge: "bg-red-600 text-white",
    text: "text-red-800 dark:text-red-200",
  },
};

const EXAMPLE_CLAIM = "MCF-7";
const EXAMPLE_PROFILE = `Amelogenin: X
CSF1PO: 10
D13S317: 11
D16S539: 11,12
D5S818: 11,12
D7S820: 8,9
TH01: 6
TPOX: 9,12
vWA: 14,15`;

// A real HeLa profile, but claimed as MCF-7 -> should come back red (contamination).
const EXAMPLE_HELA_PROFILE = `Amelogenin: X
CSF1PO: 9,10
D13S317: 12
D16S539: 9,10
D5S818: 11,12
D7S820: 8,12
TH01: 7
TPOX: 8,12
vWA: 16,18`;

// Parse pasted "locus: alleles" lines into { locus: [alleles] }.
function parseProfile(text) {
  const profile = {};
  for (const raw of text.split(/\r?\n/)) {
    const line = raw.trim();
    if (!line) continue;
    const m = line.match(/^(\S+?)\s*[:=]\s*(.+)$/) || line.match(/^(\S+)\s+(.+)$/);
    if (!m) continue;
    const alleles = m[2].split(/[\s,]+/).map((s) => s.trim()).filter(Boolean);
    if (m[1] && alleles.length) profile[m[1]] = alleles;
  }
  return profile;
}

export default function STRReader() {
  const [claimed, setClaimed] = useState("");
  const [profileText, setProfileText] = useState("");
  const [status, setStatus] = useState("idle"); // idle | loading | success | error
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null); // { kind: "validation" | "failure", message }

  function applyExample(claim, profile) {
    setClaimed(claim);
    setProfileText(profile);
    setResult(null);
    setError(null);
    setStatus("idle");
  }

  async function run() {
    if (status === "loading") return;
    const strProfile = parseProfile(profileText);
    if (!claimed.trim() || Object.keys(strProfile).length === 0) {
      setError({
        kind: "validation",
        message: "Enter a claimed identity and at least a few locus:allele lines.",
      });
      setResult(null);
      setStatus("error");
      return;
    }
    setStatus("loading");
    setResult(null);
    setError(null);
    try {
      const data = await analyzeSTR({ claimedIdentity: claimed.trim(), strProfile });
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

  return (
    <div className="space-y-6">
      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label className="mb-1 block text-sm font-medium">Claimed identity</label>
          <input
            value={claimed}
            onChange={(e) => setClaimed(e.target.value)}
            placeholder="What line do you think this is? e.g. MCF-7"
            className="h-11 w-full rounded-md border border-input bg-background px-3 text-sm outline-none placeholder:text-muted-foreground focus-visible:ring-2 focus-visible:ring-ring"
          />
        </div>
        <div>
          <div className="mb-1 flex items-center justify-between">
            <label className="text-sm font-medium">STR profile</label>
            <div className="flex gap-3">
              <button
                type="button"
                onClick={() => applyExample(EXAMPLE_CLAIM, EXAMPLE_PROFILE)}
                className="text-xs text-muted-foreground underline underline-offset-2 hover:text-foreground"
              >
                Load MCF-7 example
              </button>
              <button
                type="button"
                onClick={() => applyExample("MCF-7", EXAMPLE_HELA_PROFILE)}
                className="text-xs text-muted-foreground underline underline-offset-2 hover:text-foreground"
              >
                Load HeLa-as-MCF-7 example
              </button>
            </div>
          </div>
          <textarea
            value={profileText}
            onChange={(e) => setProfileText(e.target.value)}
            rows={9}
            placeholder={"One locus per line, e.g.\nD5S818: 11,12\nTH01: 6\nvWA: 14,15"}
            className="w-full rounded-md border border-input bg-background p-3 font-mono text-sm outline-none placeholder:text-muted-foreground focus-visible:ring-2 focus-visible:ring-ring"
          />
        </div>
        <button
          type="submit"
          disabled={status === "loading"}
          className="inline-flex h-11 items-center gap-2 rounded-md bg-primary px-5 text-sm font-medium text-primary-foreground disabled:opacity-50"
        >
          {status === "loading" ? <Loader2 className="h-4 w-4 animate-spin" /> : <FlaskConical className="h-4 w-4" />}
          {status === "loading" ? "Analyzing…" : "Analyze STR profile"}
        </button>
      </form>

      {status === "loading" && <STRSkeleton />}

      {status === "error" && error?.kind === "validation" && (
        <ErrorState title="Could not analyze" message={error.message} />
      )}
      {status === "error" && error?.kind === "failure" && (
        <ErrorState title="Could not analyze" message={error.message} onRetry={run} />
      )}

      {status === "success" && result && <STRResultCard result={result} />}
    </div>
  );
}

function STRSkeleton() {
  return (
    <div className="rounded-xl border p-6">
      <div className="flex items-center justify-between gap-4">
        <div className="space-y-2">
          <Skeleton className="h-3 w-20" />
          <Skeleton className="h-8 w-44" />
        </div>
        <Skeleton className="h-9 w-28 rounded-full" />
      </div>
      <Skeleton className="mt-5 h-4 w-48" />
      <div className="mt-6 space-y-2">
        <Skeleton className="h-3 w-24" />
        <Skeleton className="h-4 w-full" />
        <Skeleton className="h-4 w-5/6" />
      </div>
      <div className="mt-4 space-y-2">
        <Skeleton className="h-3 w-28" />
        <Skeleton className="h-4 w-3/4" />
      </div>
    </div>
  );
}

function STRResultCard({ result }) {
  const v = VERDICTS[result.match_verdict] ?? VERDICTS.yellow;
  const { Icon } = v;
  const loci = result.loci_analysis ?? {};
  const matched = result.matched_line ?? {};

  return (
    <div className={`rounded-xl border p-6 ${v.card}`}>
      <div className="flex items-center justify-between gap-4">
        <div>
          <div className="text-xs uppercase tracking-wide text-muted-foreground">STR match</div>
          <div className="mt-1 flex items-baseline gap-2">
            <span className={`text-3xl font-bold ${v.text}`}>{Math.round(result.match_percentage)}%</span>
            <span className="text-sm text-muted-foreground">
              to {matched.name}
              {matched.rrid ? ` (${matched.rrid})` : ""}
            </span>
          </div>
        </div>
        <span className={`inline-flex items-center gap-2 rounded-full px-4 py-2 text-sm font-semibold ${v.badge}`}>
          <Icon className="h-4 w-4" aria-hidden="true" />
          {v.label}
        </span>
      </div>

      <div className="mt-5 text-sm">
        <span className="text-muted-foreground">Loci: </span>
        {loci.matching_loci}/{loci.total_loci} matching
        {loci.anomalous_loci?.length > 0 && (
          <span className="ml-2">
            — differ at{" "}
            {loci.anomalous_loci.map((l) => (
              <span key={l} className="mx-0.5 rounded bg-black/5 px-1.5 py-0.5 font-mono text-xs dark:bg-white/10">
                {l}
              </span>
            ))}
          </span>
        )}
      </div>

      {result.interpretation && (
        <div className="mt-6">
          <div className="text-xs uppercase tracking-wide text-muted-foreground">Interpretation</div>
          <p className="mt-1 text-sm leading-relaxed">{result.interpretation}</p>
        </div>
      )}

      {result.recommendation && (
        <div className="mt-4">
          <div className="text-xs uppercase tracking-wide text-muted-foreground">Recommendation</div>
          <p className="mt-1 text-sm leading-relaxed">{result.recommendation}</p>
        </div>
      )}

      {result.sources?.length > 0 && (
        <p className="mt-5 text-xs text-muted-foreground">via {result.sources.join(", ")}</p>
      )}
    </div>
  );
}
