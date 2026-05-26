import { TopBar } from "@/components/layout/TopBar";
import { HeartHandshake, Users, MessageSquare, RefreshCw } from "lucide-react";

export default function SurvivalProPage() {
  return (
    <>
      <TopBar title="Survival Pro" subtitle="B40 aid finder · Spend Coach · Malaysian welfare schemes" />
      <main className="flex-1 p-6">
        <ComingSoonShell
          icon={<HeartHandshake className="w-10 h-10 text-amber-400" />}
          title="Survival Pro"
          description="Matches B40 households to eligible SOCSO, EPF, BSH, and state aid schemes. Claude-powered Spend Coach for MYR budget advice."
          features={[
            { icon: <Users className="w-4 h-4" />, label: "Eligibility matcher: SOCSO, EPF, BSH, BRIM" },
            { icon: <MessageSquare className="w-4 h-4" />, label: "Claude Spend Coach (MYR context)" },
            { icon: <RefreshCw className="w-4 h-4" />, label: "Daily aid dataset refresh via Redis" },
          ]}
          phase="Phase 2 — Week 4"
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
              <span className="text-amber-400">{f.icon}</span>
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
