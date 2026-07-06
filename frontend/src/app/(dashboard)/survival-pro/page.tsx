"use client";

import { useState } from "react";
import { EligibilityForm, EligibilityFormData } from "./components/EligibilityForm";
import { SchemeCard } from "./components/SchemeCard";
import { SpendCoach } from "./components/SpendCoach";

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

interface EligibilityResponse {
  results: SchemeResult[];
  eligible_count: number;
  total_count: number;
}

type Tab = "form" | "results" | "coach";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export default function SurvivalProPage() {
  const [tab, setTab] = useState<Tab>("form");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [eligibility, setEligibility] = useState<EligibilityResponse | null>(null);
  const [profile, setProfile] = useState<EligibilityFormData | null>(null);

  const handleFormSubmit = async (data: EligibilityFormData) => {
    setLoading(true);
    setError(null);
    setProfile(data);
    try {
      const res = await fetch(`${API_URL}/api/survival-pro/eligibility`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(data),
      });
      if (!res.ok) throw new Error(`Server error ${res.status}`);
      const json: EligibilityResponse = await res.json();
      setEligibility(json);
      setTab("results");
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Unknown error");
    } finally {
      setLoading(false);
    }
  };

  const eligibleSchemes = eligibility?.results.filter((r) => r.eligible) ?? [];
  const ineligibleSchemes = eligibility?.results.filter((r) => !r.eligible) ?? [];

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="flex items-center justify-between mb-4 shrink-0">
        <div>
          <h1 className="text-xl font-semibold text-white">Survival Pro</h1>
          <p className="text-xs text-slate-500 mt-0.5">
            Malaysian welfare eligibility matcher + AI spend coach
          </p>
        </div>
        {eligibility && (
          <span className="text-xs px-2.5 py-1 rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-700/30">
            {eligibility.eligible_count} scheme{eligibility.eligible_count !== 1 ? "s" : ""} matched
          </span>
        )}
      </div>

      {/* Tabs */}
      <div className="flex gap-1 mb-4 bg-[#0a0e1a] rounded-lg p-1 shrink-0">
        {(
          [
            ["form", "Eligibility Check"],
            ["results", "Matched Schemes"],
            ["coach", "Spend Coach"],
          ] as [Tab, string][]
        ).map(([t, label]) => (
          <button
            key={t}
            onClick={() => setTab(t)}
            disabled={t !== "form" && !eligibility}
            className={
              tab === t
                ? "flex-1 py-1.5 rounded-md text-xs font-medium bg-[#0f1629] text-sky-400 border border-[#1e2d4a]"
                : "flex-1 py-1.5 rounded-md text-xs font-medium text-slate-500 hover:text-slate-300 disabled:opacity-30 disabled:cursor-not-allowed transition-colors"
            }
          >
            {label}
          </button>
        ))}
      </div>

      {/* Tab content */}
      <div className="flex-1 overflow-y-auto min-h-0">
        {/* Form tab */}
        {tab === "form" && (
          <div className="max-w-md mx-auto">
            <div className="rounded-xl border border-[#1e2d4a] bg-[#0f1629] p-5">
              <h2 className="text-sm font-semibold text-white mb-4">Your Household Profile</h2>
              {error && (
                <div className="mb-4 text-xs text-rose-400 bg-rose-900/20 border border-rose-800/40 rounded-lg px-3 py-2">
                  {error}
                </div>
              )}
              <EligibilityForm onSubmit={handleFormSubmit} loading={loading} />
            </div>
          </div>
        )}

        {/* Results tab */}
        {tab === "results" && eligibility && (
          <div className="space-y-6">
            {eligibleSchemes.length > 0 && (
              <div>
                <h2 className="text-xs font-semibold text-emerald-400 uppercase tracking-widest mb-3">
                  You may qualify for ({eligibleSchemes.length})
                </h2>
                <div className="grid gap-3 sm:grid-cols-2">
                  {eligibleSchemes.map((r) => (
                    <SchemeCard key={r.scheme_id} result={r} />
                  ))}
                </div>
              </div>
            )}

            {ineligibleSchemes.length > 0 && (
              <div>
                <h2 className="text-xs font-semibold text-slate-600 uppercase tracking-widest mb-3">
                  Not currently eligible ({ineligibleSchemes.length})
                </h2>
                <div className="grid gap-3 sm:grid-cols-2">
                  {ineligibleSchemes.map((r) => (
                    <SchemeCard key={r.scheme_id} result={r} />
                  ))}
                </div>
              </div>
            )}

            <div className="rounded-xl border border-[#1e2d4a] bg-[#0f1629] p-4 text-center">
              <p className="text-sm text-slate-400 mb-3">
                Want help stretching your RM{profile?.monthly_income_myr?.toLocaleString()} further?
              </p>
              <button
                onClick={() => setTab("coach")}
                className="px-4 py-2 rounded-lg bg-sky-600 hover:bg-sky-500 text-white text-sm font-medium transition-colors"
              >
                Open Spend Coach
              </button>
            </div>
          </div>
        )}

        {/* Spend Coach tab */}
        {tab === "coach" && profile && (
          <div className="h-[calc(100vh-14rem)]">
            <SpendCoach
              monthlyIncome={profile.monthly_income_myr}
              householdSize={profile.household_size}
              apiUrl={API_URL}
            />
          </div>
        )}
      </div>
    </div>
  );
}
