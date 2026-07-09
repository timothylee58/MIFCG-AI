"use client";

import { useState, useCallback, useRef } from "react";
import { authedFetch } from "@/lib/api";

export interface Citation {
  label: string;
  title: string;
  source: string;
  doc_id: string;
  similarity: number;
}

export interface StreamState {
  status: "idle" | "routing" | "retrieving" | "streaming" | "done" | "error";
  routedSources: string[];
  chunkCount: number;
  answer: string;
  citations: Citation[];
  cached: boolean;
  error: string | null;
}

const INITIAL: StreamState = {
  status: "idle",
  routedSources: [],
  chunkCount: 0,
  answer: "",
  citations: [],
  cached: false,
  error: null,
};

export function useSSEStream(apiUrl: string) {
  const [state, setState] = useState<StreamState>(INITIAL);
  const abortRef = useRef<AbortController | null>(null);

  const query = useCallback(
    async (q: string, sources: string[]) => {
      abortRef.current?.abort();
      const controller = new AbortController();
      abortRef.current = controller;

      setState({ ...INITIAL, status: "routing" });

      try {
        const res = await authedFetch(`${apiUrl}/api/regcomply/query`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ query: q, sources }),
          signal: controller.signal,
        });

        if (!res.ok) {
          throw new Error(`HTTP ${res.status}`);
        }

        const reader = res.body!.getReader();
        const decoder = new TextDecoder();
        let buffer = "";

        while (true) {
          const { done, value } = await reader.read();
          if (done) break;

          buffer += decoder.decode(value, { stream: true });
          const lines = buffer.split("\n");
          buffer = lines.pop() ?? "";

          for (const line of lines) {
            if (!line.startsWith("data: ")) continue;
            const raw = line.slice(6).trim();
            if (!raw) continue;
            try {
              const event = JSON.parse(raw);
              handleEvent(event);
            } catch {
              // malformed line — skip
            }
          }
        }
      } catch (err: unknown) {
        if ((err as Error).name !== "AbortError") {
          setState((s) => ({ ...s, status: "error", error: String(err) }));
        }
      }
    },
    [apiUrl]
  );

  function handleEvent(event: Record<string, unknown>) {
    switch (event.type) {
      case "routing":
        setState((s) => ({
          ...s,
          status: "routing",
          routedSources: (event.sources as string[]) ?? [],
        }));
        break;
      case "retrieving":
        setState((s) => ({
          ...s,
          status: "retrieving",
          chunkCount: (event.count as number) ?? 0,
        }));
        break;
      case "chunk":
        setState((s) => ({
          ...s,
          status: "streaming",
          answer: s.answer + (event.content as string),
        }));
        break;
      case "citations":
        setState((s) => ({
          ...s,
          citations: (event.citations as Citation[]) ?? [],
        }));
        break;
      case "done":
        setState((s) => ({
          ...s,
          status: "done",
          cached: (event.cached as boolean) ?? false,
        }));
        break;
      case "error":
        setState((s) => ({
          ...s,
          status: "error",
          error: (event.message as string) ?? "Unknown error",
        }));
        break;
    }
  }

  const reset = useCallback(() => {
    abortRef.current?.abort();
    setState(INITIAL);
  }, []);

  return { state, query, reset };
}
