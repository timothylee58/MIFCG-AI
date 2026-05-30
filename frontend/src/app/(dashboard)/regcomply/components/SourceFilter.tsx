"use client";

import { cn } from "@/lib/utils";

const SOURCES = [
  { id: "BNM",   label: "BNM",   description: "Bank Negara Malaysia",         color: "text-sky-400",    bg: "bg-sky-400/10 border-sky-400/30" },
  { id: "SC",    label: "SC",    description: "Securities Commission",         color: "text-violet-400", bg: "bg-violet-400/10 border-violet-400/30" },
  { id: "PDPA",  label: "PDPA",  description: "Personal Data Protection Act", color: "text-amber-400",  bg: "bg-amber-400/10 border-amber-400/30" },
  { id: "BURSA", label: "Bursa", description: "Bursa Malaysia",               color: "text-emerald-400",bg: "bg-emerald-400/10 border-emerald-400/30" },
];

interface SourceFilterProps {
  selected: string[];
  onChange: (sources: string[]) => void;
  disabled?: boolean;
}

export function SourceFilter({ selected, onChange, disabled }: SourceFilterProps) {
  function toggle(id: string) {
    if (disabled) return;
    onChange(
      selected.includes(id) ? selected.filter((s) => s !== id) : [...selected, id]
    );
  }

  return (
    <div className="space-y-1.5">
      <p className="text-[10px] font-semibold uppercase tracking-wider text-muted-foreground px-1">
        Document Sources
      </p>
      {SOURCES.map((s) => {
        const active = selected.includes(s.id);
        return (
          <button
            key={s.id}
            onClick={() => toggle(s.id)}
            disabled={disabled}
            className={cn(
              "w-full flex items-center gap-2.5 px-3 py-2 rounded-lg border text-left transition-colors text-sm",
              active ? s.bg : "border-border bg-transparent hover:bg-accent/40",
              disabled && "opacity-50 cursor-not-allowed"
            )}
          >
            <div
              className={cn(
                "w-3.5 h-3.5 rounded border-2 flex items-center justify-center flex-shrink-0 transition-colors",
                active ? `border-current ${s.color}` : "border-muted-foreground"
              )}
            >
              {active && (
                <svg viewBox="0 0 10 10" className="w-2 h-2 fill-current">
                  <path d="M1.5 5L4 7.5 8.5 2.5" stroke="currentColor" strokeWidth="1.5" fill="none" strokeLinecap="round" strokeLinejoin="round"/>
                </svg>
              )}
            </div>
            <div className="min-w-0">
              <div className={cn("font-semibold leading-none", active ? s.color : "text-foreground")}>
                {s.label}
              </div>
              <div className="text-[10px] text-muted-foreground mt-0.5 truncate">{s.description}</div>
            </div>
          </button>
        );
      })}
      {selected.length === 0 && (
        <p className="text-[10px] text-muted-foreground px-1 pt-1">
          No filters = auto-detect sources
        </p>
      )}
    </div>
  );
}
