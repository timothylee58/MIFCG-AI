import { TopBar } from "@/components/layout/TopBar";
import { TrendingUp, Radio, AlertTriangle, Clock } from "lucide-react";

export default function FXWatchPage() {
  return (
    <>
      <TopBar title="FXWatch" subtitle="Live BNM FX limits · MYR pair monitoring" />
      <main className="flex-1 p-6">
        <ComingSoonShell
          icon={<TrendingUp className="w-10 h-10 text-emerald-400" />}
          title="FXWatch Live Monitor"
          description="Real-time MYR pair streaming via SSE. Monitors BNM foreign currency purchase limits, breach alerts, and order book data."
          features={[
            { icon: <Radio className="w-4 h-4" />, label: "SSE-streamed FX tick data" },
            { icon: <AlertTriangle className="w-4 h-4" />, label: "BNM limit breach detection + alerts" },
            { icon: <Clock className="w-4 h-4" />, label: "Redis TTL cache (1-min rate refresh)" },
          ]}
          phase="Phase 0 Feature — Week 1"
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
              <span className="text-emerald-400">{f.icon}</span>
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
