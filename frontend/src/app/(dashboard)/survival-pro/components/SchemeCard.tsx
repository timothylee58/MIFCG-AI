"use client";

import { cn } from "@/lib/utils";

interface SchemeResult {
  scheme_id: string;
  scheme_name: string;
  scheme_short_name: string;
  category: string;
  eligible: boolean;
  reason: string;
  estimated_amount: string;
  how_to_apply: string;
  tags: string[];
}

const CATEGORY_COLOURS: Record<string, string> = {
  "Cash Aid":   "bg-emerald-900/40 text-emerald-300 border-emerald-700/40",
  "Employment": "bg-blue-900/40   text-blue-300   border-blue-700/40",
  "Health":     "bg-rose-900/40   text-rose-300   border-rose-700/40",
  "Education":  "bg-violet-900/40 text-violet-300 border-violet-700/40",
  "State":      "bg-amber-900/40  text-amber-300  border-amber-700/40",
};

export function SchemeCard({ result }: { result: SchemeResult }) {
  const colour = CATEGORY_COLOURS[result.category] ?? "bg-slate-800 text-slate-300 border-slate-700";

  return (
    <div
      className={cn(
        "rounded-xl border p-4 space-y-2 transition-opacity",
        result.eligible
          ? "border-[#1e2d4a] bg-[#0f1629]"
          : "border-[#1a2035] bg-[#0a0e1a] opacity-50",
      )}
    >
      {/* Header */}
      <div className="flex items-start justify-between gap-2">
        <div className="flex items-center gap-2 min-w-0">
          <span
            className={cn(
              "shrink-0 inline-flex items-center px-2 py-0.5 rounded text-[10px] font-medium border",
              colour,
            )}
          >
            {result.category}
          </span>
          <h3 className="text-sm font-semibold text-white truncate">{result.scheme_name}</h3>
        </div>
        <span
          className={cn(
            "shrink-0 text-xs font-semibold px-2 py-0.5 rounded-full",
            result.eligible
              ? "bg-emerald-500/20 text-emerald-400"
              : "bg-slate-700/40 text-slate-500",
          )}
        >
          {result.eligible ? "Eligible" : "Not eligible"}
        </span>
      </div>

      {/* Reason */}
      <p className="text-xs text-slate-400">{result.reason}</p>

      {/* Amount + apply */}
      {result.eligible && (
        <>
          <div className="flex items-center gap-1.5">
            <span className="text-[10px] text-slate-500 uppercase tracking-wide">Benefit</span>
            <span className="text-xs font-medium text-sky-400">{result.estimated_amount}</span>
          </div>
          <p className="text-[11px] text-slate-500 leading-snug">{result.how_to_apply}</p>
        </>
      )}

      {/* Tags */}
      <div className="flex flex-wrap gap-1 pt-1">
        {result.tags.map((tag) => (
          <span key={tag} className="text-[10px] px-1.5 py-0.5 rounded bg-slate-800 text-slate-500">
            #{tag}
          </span>
        ))}
      </div>
    </div>
  );
}
