import { useEffect, useState } from "react";
import { Sun, Moon } from "lucide-react";
import { CellCheckLogo } from "./components/CellCheckLogo";
import QuickCheck from "@/components/QuickCheck/QuickCheck";
import STRReader from "@/components/STRReader/STRReader";
import MethodsGenerator from "@/components/MethodsGenerator/MethodsGenerator";

const TABS = [
  { id: "quick", label: "Quick Check" },
  { id: "str", label: "STR Test Reader" },
  { id: "methods", label: "Methods Generator" },
];

// Stored preference wins; otherwise follow the OS setting. Kept in sync with the
// no-flash script in index.html.
function getInitialTheme() {
  try {
    const stored = localStorage.getItem("cellcheck-theme");
    if (stored === "light" || stored === "dark") return stored;
    return window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light";
  } catch {
    return "light";
  }
}

export default function App() {
  const [tab, setTab] = useState("quick");
  const [theme, setTheme] = useState(getInitialTheme);

  useEffect(() => {
    document.documentElement.classList.toggle("dark", theme === "dark");
    try {
      localStorage.setItem("cellcheck-theme", theme);
    } catch {
      /* storage unavailable — theme still applies for this session */
    }
  }, [theme]);

  const isDark = theme === "dark";
  const toggleTheme = () => setTheme((t) => (t === "dark" ? "light" : "dark"));

  return (
    <div className="min-h-screen bg-background text-foreground">
      <header className="border-b">
        <div className="mx-auto flex max-w-3xl items-start justify-between gap-4 px-6 py-8">
          <div>
            <div className="flex items-center gap-2">
              <CellCheckLogo className="h-8 w-8" />
              <h1 className="text-2xl font-bold tracking-tight">CellCheck</h1>
            </div>
            <p className="mt-1 text-muted-foreground">
              AI-native cell line authentication.
            </p>
          </div>
          <button
            type="button"
            onClick={toggleTheme}
            aria-label={isDark ? "Switch to light mode" : "Switch to dark mode"}
            title={isDark ? "Switch to light mode" : "Switch to dark mode"}
            className="inline-flex h-9 w-9 shrink-0 items-center justify-center rounded-md border border-border text-muted-foreground transition-colors hover:bg-muted hover:text-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
          >
            {isDark ? <Sun className="h-4 w-4" aria-hidden="true" /> : <Moon className="h-4 w-4" aria-hidden="true" />}
          </button>
        </div>
      </header>

      <main className="mx-auto max-w-3xl px-6 py-8">
        <nav className="mb-8 flex gap-1 border-b">
          {TABS.map((t) => (
            <button
              key={t.id}
              onClick={() => !t.disabled && setTab(t.id)}
              disabled={t.disabled}
              className={`-mb-px border-b-2 px-4 py-2 text-sm font-medium transition-colors ${
                tab === t.id
                  ? "border-foreground text-foreground"
                  : "border-transparent text-muted-foreground hover:text-foreground"
              } ${t.disabled ? "cursor-not-allowed opacity-40 hover:text-muted-foreground" : ""}`}
            >
              {t.label}
              {t.disabled && <span className="ml-1 text-xs">(soon)</span>}
            </button>
          ))}
        </nav>

        {tab === "quick" && <QuickCheck />}
        {tab === "str" && <STRReader />}
        {tab === "methods" && <MethodsGenerator />}
      </main>
    </div>
  );
}
