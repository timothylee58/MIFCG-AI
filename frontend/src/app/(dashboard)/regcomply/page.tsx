import { TopBar } from "@/components/layout/TopBar";
import { ShieldCheck, BookOpen, FileSearch, Zap } from "lucide-react";

export default function RegComplyPage() {
  return (
    <>
      <TopBar title="RegComply AI" subtitle="BNM · SC · PDPA · AMLA compliance intelligence" />
      <main className="flex-1 p-6">
        <ComingSoonShell
          icon={<ShieldCheck className="w-10 h-10 text-sky-400" />}
          title="RegComply AI"
          description="LangGraph-powered RAG over BNM/SC/PDPA guidelines. Ask compliance questions and receive streamed answers with source citations."
          features={[
            { icon: <BookOpen className="w-4 h-4" />, label: "BNM / SC / PDPA document corpus" },
            { icon: <FileSearch className="w-4 h-4" />, label: "pgvector semantic search (1536-dim)" },
            { icon: <Zap className="w-4 h-4" />, label: "Streamed answers via FastAPI SSE" },
          ]}
          phase="Phase 1 — Week 2–3"
        />
      </main>
    </>
  );
}

function ComingSoonShell({
  icon, title, description, features, phase,
}: {
  icon: React.ReactNode;
  title: string;
  description: string;
  features: { icon: React.ReactNode; label: string }[];
  phase: string;
}) {
  return (
    <div className="h-full flex items-center justify-center">
      <div className="max-w-md w-full text-center">
        <div className="flex justify-center mb-4">{icon}</div>
        <h2 className="text-xl font-bold text-foreground mb-2">{title}</h2>
        <p className="text-sm text-muted-foreground mb-6 leading-relaxed">{description}</p>
        <div className="bg-card border border-border rounded-xl p-5 text-left space-y-3 mb-6">
          {features.map((f) => (
            <div key={f.label} className="flex items-center gap-3 text-sm text-muted-foreground">
              <span className="text-primary">{f.icon}</span>
              {f.label}
            </div>
          ))}
        </div>
        <span className="inline-block px-3 py-1.5 bg-accent text-primary text-xs font-semibold rounded-full border border-border">
          {phase}
        </span>
      </div>
    </div>
  );
}
