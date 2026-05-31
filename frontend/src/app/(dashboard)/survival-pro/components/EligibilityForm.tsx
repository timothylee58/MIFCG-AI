"use client";

import { useState } from "react";
import { cn } from "@/lib/utils";

export interface EligibilityFormData {
  monthly_income_myr: number;
  household_size: number;
  state: string;
  age: number;
  has_epf: boolean;
  is_disabled: boolean;
  is_single_mother: boolean;
  has_ptptn_loan: boolean;
  has_children_under_18: boolean;
  employment_status: "employed" | "self-employed" | "unemployed";
}

const MALAYSIAN_STATES = [
  "Johor", "Kedah", "Kelantan", "Kuala Lumpur", "Labuan", "Melaka",
  "Negeri Sembilan", "Pahang", "Penang", "Perak", "Perlis", "Putrajaya",
  "Sabah", "Sarawak", "Selangor", "Terengganu",
];

interface Props {
  onSubmit: (data: EligibilityFormData) => void;
  loading: boolean;
}

const FIELD_CLASS =
  "w-full bg-[#0f1629] border border-[#1e2d4a] rounded-lg px-3 py-2 text-sm text-white placeholder-slate-500 focus:outline-none focus:border-sky-500";

export function EligibilityForm({ onSubmit, loading }: Props) {
  const [form, setForm] = useState<EligibilityFormData>({
    monthly_income_myr: 0,
    household_size: 1,
    state: "Selangor",
    age: 35,
    has_epf: true,
    is_disabled: false,
    is_single_mother: false,
    has_ptptn_loan: false,
    has_children_under_18: false,
    employment_status: "employed",
  });

  const set = <K extends keyof EligibilityFormData>(k: K, v: EligibilityFormData[K]) =>
    setForm((f) => ({ ...f, [k]: v }));

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (form.monthly_income_myr <= 0) return;
    onSubmit(form);
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-5">
      {/* Income */}
      <div>
        <label className="block text-xs text-slate-400 mb-1">Monthly Household Income (RM)</label>
        <input
          type="number"
          min={0}
          step={50}
          placeholder="e.g. 3500"
          className={FIELD_CLASS}
          value={form.monthly_income_myr || ""}
          onChange={(e) => set("monthly_income_myr", parseFloat(e.target.value) || 0)}
          required
        />
      </div>

      {/* Household size + age */}
      <div className="grid grid-cols-2 gap-3">
        <div>
          <label className="block text-xs text-slate-400 mb-1">Household Size</label>
          <input
            type="number"
            min={1}
            max={15}
            className={FIELD_CLASS}
            value={form.household_size}
            onChange={(e) => set("household_size", parseInt(e.target.value) || 1)}
          />
        </div>
        <div>
          <label className="block text-xs text-slate-400 mb-1">Your Age</label>
          <input
            type="number"
            min={18}
            max={100}
            className={FIELD_CLASS}
            value={form.age}
            onChange={(e) => set("age", parseInt(e.target.value) || 18)}
          />
        </div>
      </div>

      {/* State */}
      <div>
        <label className="block text-xs text-slate-400 mb-1">State / Federal Territory</label>
        <select
          className={FIELD_CLASS}
          value={form.state}
          onChange={(e) => set("state", e.target.value)}
        >
          {MALAYSIAN_STATES.map((s) => (
            <option key={s} value={s}>{s}</option>
          ))}
        </select>
      </div>

      {/* Employment */}
      <div>
        <label className="block text-xs text-slate-400 mb-1">Employment Status</label>
        <select
          className={FIELD_CLASS}
          value={form.employment_status}
          onChange={(e) => set("employment_status", e.target.value as EligibilityFormData["employment_status"])}
        >
          <option value="employed">Employed (private sector)</option>
          <option value="self-employed">Self-employed / Gig</option>
          <option value="unemployed">Unemployed</option>
        </select>
      </div>

      {/* Checkboxes */}
      <div className="space-y-2">
        <p className="text-xs text-slate-400">Additional details (affects eligibility)</p>
        {(
          [
            ["has_epf", "Active EPF contributor"],
            ["has_children_under_18", "Have children under 18"],
            ["is_single_mother", "Single mother"],
            ["is_disabled", "Person with disability (OKU)"],
            ["has_ptptn_loan", "Have outstanding PTPTN loan"],
          ] as [keyof EligibilityFormData, string][]
        ).map(([key, label]) => (
          <label key={key} className="flex items-center gap-2 cursor-pointer">
            <input
              type="checkbox"
              checked={form[key] as boolean}
              onChange={(e) => set(key, e.target.checked as EligibilityFormData[typeof key])}
              className="w-4 h-4 rounded border-slate-600 bg-[#0f1629] accent-sky-500"
            />
            <span className="text-sm text-slate-300">{label}</span>
          </label>
        ))}
      </div>

      <button
        type="submit"
        disabled={loading || form.monthly_income_myr <= 0}
        className={cn(
          "w-full py-2.5 rounded-lg text-sm font-medium transition-colors",
          "bg-sky-600 hover:bg-sky-500 text-white",
          "disabled:opacity-50 disabled:cursor-not-allowed",
        )}
      >
        {loading ? "Checking eligibility…" : "Check My Eligibility"}
      </button>
    </form>
  );
}
