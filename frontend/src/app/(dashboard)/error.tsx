"use client";

import { useEffect } from "react";
import { AlertTriangle, RotateCcw } from "lucide-react";

export default function DashboardError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  useEffect(() => {
    console.error(error);
  }, [error]);

  return (
    <div className="flex-1 flex items-center justify-center px-4 py-12">
      <div className="w-full max-w-sm rounded-xl border border-[#1e2d4a] bg-[#0f1629] p-6 space-y-4 text-center">
        <div className="mx-auto w-10 h-10 rounded-full bg-destructive/10 flex items-center justify-center">
          <AlertTriangle className="w-5 h-5 text-destructive" />
        </div>
        <div>
          <h2 className="text-sm font-semibold text-foreground">Something went wrong</h2>
          <p className="mt-1 text-xs text-muted-foreground">
            {error.message || "An unexpected error occurred while loading this module."}
          </p>
          {error.digest && (
            <p className="mt-1 text-[10px] text-slate-600">Ref: {error.digest}</p>
          )}
        </div>
        <button
          onClick={reset}
          className="inline-flex items-center gap-2 justify-center w-full bg-primary text-primary-foreground font-semibold rounded-lg py-2.5 text-sm transition-opacity hover:opacity-90"
        >
          <RotateCcw className="w-4 h-4" />
          Try again
        </button>
      </div>
    </div>
  );
}
