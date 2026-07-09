import { FlaskConical, FileSearch, FileText } from "lucide-react";

const MODES = [
  {
    icon: FlaskConical,
    title: "Quick Check",
    desc: "Search a cell line by name, catalog #, or RRID and get a traffic-light verdict.",
  },
  {
    icon: FileSearch,
    title: "STR Test Reader",
    desc: "Paste or upload an STR profile for a plain-language match interpretation.",
  },
  {
    icon: FileText,
    title: "Methods Section Generator",
    desc: "Fill a short form and get a publication-ready methods paragraph with the correct RRID.",
  },
];

export default function App() {
  return (
    <div className="min-h-screen bg-background text-foreground">
      <header className="border-b">
        <div className="mx-auto max-w-3xl px-6 py-8">
          <h1 className="text-2xl font-bold tracking-tight">CellCheck</h1>
          <p className="mt-1 text-muted-foreground">
            AI-native cell line authentication.
          </p>
        </div>
      </header>

      <main className="mx-auto max-w-3xl px-6 py-10">
        <div className="grid gap-4 sm:grid-cols-3">
          {MODES.map(({ icon: Icon, title, desc }) => (
            <div key={title} className="rounded-lg border p-5">
              <Icon className="mb-3 h-6 w-6" aria-hidden="true" />
              <h2 className="font-semibold">{title}</h2>
              <p className="mt-1 text-sm text-muted-foreground">{desc}</p>
            </div>
          ))}
        </div>

        <p className="mt-8 text-sm text-muted-foreground">
          Scaffold ready. Wire up each mode against <code>src/api/client.js</code>.
        </p>
      </main>
    </div>
  );
}
