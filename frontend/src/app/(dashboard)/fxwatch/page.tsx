"use client";

import { useEffect, useState, useCallback } from "react";
import { TopBar } from "@/components/layout/TopBar";
import { authedFetch } from "@/lib/api";
import { TrendingUp, TrendingDown, RefreshCw, AlertCircle } from "lucide-react";
import { cn } from "@/lib/utils";

interface FXRateSnapshot {
  pair: string;
  rate: number;
  buying_rate: number | null;
  selling_rate: number | null;
  rate_date: string | null;
  session: string | null;
  fetched_at: number | null;
}

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";
const POLL_INTERVAL_MS = 30_000;

export default function FXWatchPage() {
  const [rates, setRates] = useState<FXRateSnapshot[]>([]);
  const [previousRates, setPreviousRates] = useState<Record<string, number>>({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [lastRefreshed, setLastRefreshed] = useState<Date | null>(null);

  const fetchRates = useCallback(async () => {
    try {
      const res = await authedFetch(`${API_URL}/api/fxwatch/rates`);
      if (!res.ok) throw new Error(`Server error ${res.status}`);
      const json: { rates: FXRateSnapshot[] } = await res.json();

      setRates((prevRates) => {
        const prevByPair: Record<string, number> = {};
        for (const r of prevRates) prevByPair[r.pair] = r.rate;
        setPreviousRates(prevByPair);
        return json.rates;
      });
      setLastRefreshed(new Date());
      setError(null);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Failed to load FX rates");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchRates();
    const interval = setInterval(fetchRates, POLL_INTERVAL_MS);
    return () => clearInterval(interval);
  }, [fetchRates]);

  return (
    <>
      <TopBar title="FXWatch" subtitle="MYR corridor monitor · BNM Open API · Claude Haiku alerts" />
      <main className="flex-1 p-6">
        <div className="max-w-2xl mx-auto space-y-4">
          <div className="flex items-center justify-between">
            <p className="text-xs text-slate-500">
              {lastRefreshed
                ? `Last refreshed ${lastRefreshed.toLocaleTimeString()}`
                : "Loading…"}
            </p>
            <button
              onClick={fetchRates}
              className="flex items-center gap-1.5 text-xs text-slate-400 hover:text-sky-400 transition-colors"
            >
              <RefreshCw className="w-3.5 h-3.5" />
              Refresh
            </button>
          </div>

          {error && (
            <div className="flex items-center gap-2 text-xs text-rose-400 bg-rose-900/20 border border-rose-800/40 rounded-lg px-3 py-2">
              <AlertCircle className="w-4 h-4 shrink-0" />
              {error}
            </div>
          )}

          {loading && rates.length === 0 && (
            <div className="text-center py-12 text-sm text-slate-500">Loading rates…</div>
          )}

          <div className="grid gap-3 sm:grid-cols-2">
            {rates.map((r) => {
              const previous = previousRates[r.pair];
              const delta = previous ? r.rate - previous : 0;
              const pctChange = previous ? (delta / previous) * 100 : 0;
              const isUp = delta > 0;
              const isDown = delta < 0;

              return (
                <div
                  key={r.pair}
                  className="rounded-xl border border-[#1e2d4a] bg-[#0f1629] p-5 space-y-2"
                >
                  <div className="flex items-center justify-between">
                    <h3 className="text-sm font-semibold text-white">{r.pair}</h3>
                    {(isUp || isDown) && (
                      <span
                        className={cn(
                          "flex items-center gap-1 text-xs font-medium",
                          isUp ? "text-emerald-400" : "text-rose-400"
                        )}
                      >
                        {isUp ? (
                          <TrendingUp className="w-3.5 h-3.5" />
                        ) : (
                          <TrendingDown className="w-3.5 h-3.5" />
                        )}
                        {pctChange >= 0 ? "+" : ""}
                        {pctChange.toFixed(2)}%
                      </span>
                    )}
                  </div>
                  <p className="text-2xl font-semibold text-sky-400">
                    {r.rate.toFixed(4)}
                  </p>
                  <div className="flex gap-3 text-[11px] text-slate-500">
                    {r.buying_rate !== null && <span>Buy: {r.buying_rate.toFixed(4)}</span>}
                    {r.selling_rate !== null && <span>Sell: {r.selling_rate.toFixed(4)}</span>}
                  </div>
                  {r.rate_date && (
                    <p className="text-[10px] text-slate-600">
                      BNM session {r.session ?? "—"} · {r.rate_date}
                    </p>
                  )}
                </div>
              );
            })}
          </div>

          <p className="text-[11px] text-slate-600 text-center pt-2">
            Rates refresh every 5 minutes from Bank Negara Malaysia. A breach of the
            configured threshold triggers a Claude Haiku narrative alert to Slack and
            Telegram automatically — no action needed here.
          </p>
        </div>
      </main>
    </>
  );
}
