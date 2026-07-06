"use client";

import { useEffect } from "react";
import { AlertTriangle, RotateCcw } from "lucide-react";

export default function GlobalError({
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
    <html lang="en">
      <body
        style={{
          margin: 0,
          minHeight: "100vh",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          background: "#0a0e1a",
          color: "#e2e8f0",
          fontFamily:
            "ui-sans-serif, system-ui, -apple-system, Segoe UI, Roboto, sans-serif",
          padding: "1rem",
        }}
      >
        <div
          style={{
            width: "100%",
            maxWidth: "24rem",
            borderRadius: "0.75rem",
            border: "1px solid #1e2d4a",
            background: "#0f1629",
            padding: "1.5rem",
            textAlign: "center",
          }}
        >
          <div
            style={{
              margin: "0 auto",
              width: "2.5rem",
              height: "2.5rem",
              borderRadius: "9999px",
              background: "rgba(239, 68, 68, 0.1)",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
            }}
          >
            <AlertTriangle style={{ width: "1.25rem", height: "1.25rem", color: "#ef4444" }} />
          </div>
          <h2 style={{ marginTop: "1rem", fontSize: "0.875rem", fontWeight: 600, color: "#e2e8f0" }}>
            Something went wrong
          </h2>
          <p style={{ marginTop: "0.25rem", fontSize: "0.75rem", color: "#64748b" }}>
            {error.message || "A critical error occurred. Please reload the application."}
          </p>
          {error.digest && (
            <p style={{ marginTop: "0.25rem", fontSize: "0.625rem", color: "#475569" }}>
              Ref: {error.digest}
            </p>
          )}
          <button
            onClick={() => reset()}
            style={{
              marginTop: "1rem",
              display: "inline-flex",
              alignItems: "center",
              justifyContent: "center",
              gap: "0.5rem",
              width: "100%",
              background: "#38bdf8",
              color: "#0a0e1a",
              fontWeight: 600,
              borderRadius: "0.5rem",
              padding: "0.625rem",
              fontSize: "0.875rem",
              border: "none",
              cursor: "pointer",
            }}
          >
            <RotateCcw style={{ width: "1rem", height: "1rem" }} />
            Reload
          </button>
        </div>
      </body>
    </html>
  );
}
