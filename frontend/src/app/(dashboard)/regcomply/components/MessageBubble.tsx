"use client";

import { cn } from "@/lib/utils";
import type { Citation } from "@/hooks/useSSEStream";

interface MessageBubbleProps {
  role: "user" | "assistant";
  content: string;
  citations?: Citation[];
  streaming?: boolean;
}

const SOURCE_COLORS: Record<string, string> = {
  BNM:   "bg-sky-400/10 text-sky-400 border-sky-400/30",
  SC:    "bg-violet-400/10 text-violet-400 border-violet-400/30",
  PDPA:  "bg-amber-400/10 text-amber-400 border-amber-400/30",
  BURSA: "bg-emerald-400/10 text-emerald-400 border-emerald-400/30",
};

export function MessageBubble({ role, content, citations, streaming }: MessageBubbleProps) {
  if (role === "user") {
    return (
      <div className="flex justify-end mb-4">
        <div className="max-w-[75%] bg-primary/10 border border-primary/20 text-foreground rounded-2xl rounded-tr-sm px-4 py-3 text-sm leading-relaxed">
          {content}
        </div>
      </div>
    );
  }

  return (
    <div className="flex gap-3 mb-6">
      {/* Avatar */}
      <div className="w-7 h-7 rounded-lg bg-primary/10 border border-primary/20 flex items-center justify-center flex-shrink-0 mt-0.5">
        <svg className="w-3.5 h-3.5 text-primary" fill="none" stroke="currentColor" strokeWidth={2} viewBox="0 0 24 24">
          <path d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
        </svg>
      </div>

      <div className="flex-1 min-w-0">
        {/* Answer text — rendered as simple paragraphs */}
        <div className="bg-card border border-border rounded-2xl rounded-tl-sm px-4 py-3 text-sm leading-relaxed text-foreground whitespace-pre-wrap break-words">
          {content}
          {streaming && (
            <span className="inline-block w-1.5 h-4 bg-primary ml-0.5 align-text-bottom animate-pulse rounded-sm" />
          )}
        </div>

        {/* Citations */}
        {citations && citations.length > 0 && (
          <div className="mt-2 flex flex-wrap gap-1.5">
            {citations.map((c) => (
              <span
                key={c.label}
                title={`${c.title} — ${(c.similarity * 100).toFixed(0)}% match`}
                className={cn(
                  "inline-flex items-center gap-1 text-[10px] font-semibold px-2 py-0.5 rounded-full border cursor-default",
                  SOURCE_COLORS[c.source] ?? "bg-muted text-muted-foreground border-border"
                )}
              >
                {c.label} {c.title.length > 30 ? c.title.slice(0, 30) + "…" : c.title}
              </span>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
