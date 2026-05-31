"use client";

import { useState, useEffect, useRef } from "react";
import { TopBar } from "@/components/layout/TopBar";
import { useSSEStream } from "@/hooks/useSSEStream";
import { SourceFilter } from "./components/SourceFilter";
import { MessageBubble } from "./components/MessageBubble";
import { ChatInput } from "./components/ChatInput";
import type { Citation } from "@/hooks/useSSEStream";
import { cn } from "@/lib/utils";

interface Message {
  id: string;
  role: "user" | "assistant";
  content: string;
  citations?: Citation[];
}

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export default function RegComplyPage() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [selectedSources, setSelectedSources] = useState<string[]>([]);
  const { state, query, reset } = useSSEStream(API_URL);
  const bottomRef = useRef<HTMLDivElement>(null);
  const assistantIdRef = useRef<string | null>(null);

  const isStreaming = ["routing", "retrieving", "streaming"].includes(state.status);

  // Start a new assistant message bubble when routing begins
  useEffect(() => {
    if (state.status === "routing" && assistantIdRef.current === null) {
      const id = crypto.randomUUID();
      assistantIdRef.current = id;
      setMessages((prev) => [...prev, { id, role: "assistant", content: "" }]);
    }
  }, [state.status]);

  // Update the in-progress assistant bubble with streaming content
  useEffect(() => {
    if (!assistantIdRef.current) return;
    const id = assistantIdRef.current;
    setMessages((prev) =>
      prev.map((m) =>
        m.id === id
          ? { ...m, content: state.answer, citations: state.citations }
          : m
      )
    );
  }, [state.answer, state.citations]);

  // Clear the in-progress ref when done or errored
  useEffect(() => {
    if (state.status === "done" || state.status === "error") {
      assistantIdRef.current = null;
    }
  }, [state.status]);

  // Auto-scroll to bottom
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, state.answer]);

  function handleSubmit() {
    if (!input.trim() || isStreaming) return;
    const userMsg: Message = { id: crypto.randomUUID(), role: "user", content: input.trim() };
    setMessages((prev) => [...prev, userMsg]);
    assistantIdRef.current = null;
    query(input.trim(), selectedSources);
    setInput("");
  }

  function handleStop() {
    reset();
    assistantIdRef.current = null;
  }

  function handleNewChat() {
    reset();
    setMessages([]);
    assistantIdRef.current = null;
    setInput("");
  }

  return (
    <>
      <TopBar title="RegComply AI" subtitle="BNM · SC · PDPA · Bursa compliance intelligence" />

      <div className="flex flex-1 min-h-0 overflow-hidden">
        {/* ── Left sidebar ────────────────────────────────── */}
        <aside className="w-56 bg-card border-r border-border flex flex-col gap-5 p-4 flex-shrink-0 overflow-y-auto">
          <SourceFilter
            selected={selectedSources}
            onChange={setSelectedSources}
            disabled={isStreaming}
          />

          {/* Status indicator */}
          {state.status !== "idle" && state.status !== "done" && (
            <div className="space-y-1.5">
              <p className="text-[10px] font-semibold uppercase tracking-wider text-muted-foreground">
                Pipeline
              </p>
              <PipelineStatus status={state.status} routed={state.routedSources} chunks={state.chunkCount} cached={state.cached} />
            </div>
          )}

          <div className="mt-auto">
            <button
              onClick={handleNewChat}
              disabled={isStreaming}
              className="w-full text-xs text-muted-foreground hover:text-foreground bg-transparent hover:bg-accent border border-border rounded-lg px-3 py-2 transition-colors"
            >
              New conversation
            </button>
          </div>
        </aside>

        {/* ── Chat area ──────────────────────────────────── */}
        <div className="flex flex-col flex-1 min-w-0 min-h-0">
          {/* Messages */}
          <div className="flex-1 overflow-y-auto px-6 py-6">
            {messages.length === 0 ? (
              <EmptyState />
            ) : (
              <>
                {messages.map((m) => (
                  <MessageBubble
                    key={m.id}
                    role={m.role}
                    content={m.content}
                    citations={m.citations}
                    streaming={m.role === "assistant" && isStreaming && m.id === assistantIdRef.current}
                  />
                ))}
                {state.status === "error" && (
                  <div className="flex gap-3 mb-4">
                    <div className="flex-1 bg-destructive/10 border border-destructive/30 text-destructive rounded-xl px-4 py-3 text-sm">
                      {state.error}
                    </div>
                  </div>
                )}
              </>
            )}
            <div ref={bottomRef} />
          </div>

          {/* Input */}
          <div className="border-t border-border px-6 py-4">
            <ChatInput
              value={input}
              onChange={setInput}
              onSubmit={handleSubmit}
              onStop={handleStop}
              streaming={isStreaming}
            />
          </div>
        </div>
      </div>
    </>
  );
}

function PipelineStatus({
  status, routed, chunks, cached,
}: {
  status: string;
  routed: string[];
  chunks: number;
  cached: boolean;
}) {
  const steps = [
    { key: "routing",    label: "Router",     detail: routed.length ? routed.join(", ") : "…" },
    { key: "retrieving", label: "Retriever",  detail: chunks ? `${chunks} chunks` : "…" },
    { key: "streaming",  label: "Synthesizer",detail: "Generating…" },
  ];
  const order = ["routing", "retrieving", "streaming"];
  const currentIdx = order.indexOf(status);

  return (
    <div className="space-y-1">
      {steps.map((step, i) => {
        const done = i < currentIdx;
        const active = i === currentIdx;
        return (
          <div key={step.key} className={cn("flex items-center gap-2 text-xs", done ? "text-muted-foreground" : active ? "text-primary" : "text-muted-foreground/40")}>
            <div className={cn("w-1.5 h-1.5 rounded-full flex-shrink-0", done ? "bg-muted-foreground" : active ? "bg-primary animate-pulse" : "bg-muted-foreground/20")} />
            <span className="font-medium">{step.label}</span>
            {(done || active) && <span className="text-[10px] truncate">{step.detail}</span>}
          </div>
        );
      })}
      {cached && <p className="text-[10px] text-muted-foreground pl-3.5">from cache</p>}
    </div>
  );
}

function EmptyState() {
  return (
    <div className="h-full flex items-center justify-center">
      <div className="text-center max-w-sm">
        <div className="w-12 h-12 rounded-xl bg-primary/10 border border-primary/20 flex items-center justify-center mx-auto mb-4">
          <svg className="w-6 h-6 text-primary" fill="none" stroke="currentColor" strokeWidth={1.5} viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
          </svg>
        </div>
        <h2 className="text-base font-semibold text-foreground mb-1.5">RegComply AI</h2>
        <p className="text-sm text-muted-foreground leading-relaxed mb-4">
          Ask any compliance question about BNM guidelines, SC regulations, PDPA obligations, or Bursa Malaysia rules.
        </p>
        <div className="flex flex-wrap justify-center gap-1.5">
          {["BNM", "SC", "PDPA", "Bursa"].map((s) => (
            <span key={s} className="text-xs bg-card border border-border text-muted-foreground px-2.5 py-1 rounded-full">
              {s}
            </span>
          ))}
        </div>
      </div>
    </div>
  );
}
