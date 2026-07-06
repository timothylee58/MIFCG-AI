"use client";

import { useRef, KeyboardEvent } from "react";
import { cn } from "@/lib/utils";
import { SendHorizonal, Square } from "lucide-react";

interface ChatInputProps {
  value: string;
  onChange: (v: string) => void;
  onSubmit: () => void;
  onStop: () => void;
  streaming: boolean;
  disabled?: boolean;
}

const EXAMPLE_QUERIES = [
  "What are BNM's AML requirements for e-wallet operators?",
  "How should a licensed fund manager handle client personal data under PDPA?",
  "What are the disclosure obligations for a Bursa-listed company issuing new shares?",
  "Explain the SC's fit-and-proper criteria for investment advisers.",
];

export function ChatInput({ value, onChange, onSubmit, onStop, streaming, disabled }: ChatInputProps) {
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  function handleKeyDown(e: KeyboardEvent<HTMLTextAreaElement>) {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      if (!streaming && value.trim()) onSubmit();
    }
  }

  return (
    <div className="space-y-3">
      {/* Example chips — only show when idle */}
      {!value && !streaming && (
        <div className="flex flex-wrap gap-2">
          {EXAMPLE_QUERIES.map((q) => (
            <button
              key={q}
              onClick={() => { onChange(q); textareaRef.current?.focus(); }}
              className="text-xs text-muted-foreground bg-card border border-border rounded-full px-3 py-1 hover:bg-accent hover:text-foreground transition-colors truncate max-w-xs"
            >
              {q}
            </button>
          ))}
        </div>
      )}

      {/* Input row */}
      <div className="flex gap-2 items-end bg-card border border-border rounded-xl p-2">
        <textarea
          ref={textareaRef}
          value={value}
          onChange={(e) => onChange(e.target.value)}
          onKeyDown={handleKeyDown}
          disabled={disabled || streaming}
          rows={1}
          placeholder="Ask a compliance question… (Shift+Enter for newline)"
          className={cn(
            "flex-1 bg-transparent text-sm text-foreground placeholder:text-muted-foreground resize-none outline-none min-h-[36px] max-h-40 py-1.5 px-2 leading-relaxed",
            (disabled || streaming) && "opacity-50"
          )}
          style={{ fieldSizing: "content" } as React.CSSProperties}
        />
        {streaming ? (
          <button
            onClick={onStop}
            className="w-8 h-8 flex items-center justify-center rounded-lg bg-destructive/10 text-destructive hover:bg-destructive/20 transition-colors flex-shrink-0"
          >
            <Square className="w-3.5 h-3.5 fill-current" />
          </button>
        ) : (
          <button
            onClick={onSubmit}
            disabled={!value.trim() || disabled}
            className={cn(
              "w-8 h-8 flex items-center justify-center rounded-lg transition-colors flex-shrink-0",
              value.trim() && !disabled
                ? "bg-primary text-primary-foreground hover:opacity-90"
                : "bg-muted text-muted-foreground cursor-not-allowed"
            )}
          >
            <SendHorizonal className="w-3.5 h-3.5" />
          </button>
        )}
      </div>

      <p className="text-[10px] text-muted-foreground text-center">
        Answers reference BNM, SC, PDPA, and Bursa Malaysia documents. Always verify with primary sources.
      </p>
    </div>
  );
}
