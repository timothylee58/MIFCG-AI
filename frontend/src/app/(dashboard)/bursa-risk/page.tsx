import { TopBar } from "@/components/layout/TopBar";
import { BarChart3, Cpu, GitBranch, Filter } from "lucide-react";

export default function BursaRiskPage() {
  return (
    <>
      <TopBar title="Bursa Risk" subtitle="XGBoost factor analytics · KLCI universe" />
      <main className="flex-1 p-6">
        <ComingSoonShell
          icon={<BarChart3 className="w-10 h-10 text-violet-400" />}
          title="Bursa Factor Analytics"
          description="XGBoost ML inference on KLCI stocks. Decompose returns into Value, Momentum, Quality, Low-Vol, and Dividend factors."
          features={[
            { icon: <Cpu className="w-4 h-4" />, label: "XGBoost + scikit-learn inference" },
            { icon: <GitBranch className="w-4 h-4" />, label: "5-factor risk decomposition" },
            { icon: <Filter className="w-4 h-4" />, label: "SC-compliant screener with shariah filter" },
          ]}
          phase="Phase 3 — Week 5–6"
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
              <span className="text-violet-400">{f.icon}</span>
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
