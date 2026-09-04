"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { apiMe, apiUpdateProfile, type ProfileUpdate, type UserProfile } from "@/lib/api";

const platforms = ["Swiggy", "Uber", "Rapido", "Zomato", "Urban Company"];
const inputClass = "mt-1 w-full rounded-xl border border-gray-200 px-3 py-2.5 text-sm focus:border-[#087344] focus:outline-none focus:ring-1 focus:ring-[#b9e6c8]";
function initials(name: string) { return name.split(" ").filter(Boolean).slice(0, 2).map((p) => p[0]?.toUpperCase()).join("") || "FG"; }
function money(value: number) { return `₹${value.toLocaleString("en-IN")}`; }

export default function ProfilePage() {
  const [profile, setProfile] = useState<UserProfile | null>(null);
  const [form, setForm] = useState<Partial<ProfileUpdate>>({});
  const [error, setError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);
  const [copied, setCopied] = useState(false);

  useEffect(() => { apiMe().then((data) => { setProfile(data); setForm({
    name: data.name, occupation: data.occupation, monthly_income_avg: data.monthly_income_avg,
    fixed_expenses: data.fixed_expenses, variable_expenses: data.variable_expenses,
    total_debt: data.total_debt, monthly_emi: data.monthly_emi, savings_balance: data.savings_balance,
    emergency_buffer: data.emergency_buffer, dependents: data.dependents,
    avg_work_hours_per_week: data.avg_work_hours_per_week, active_platforms: data.active_platforms,
  }); }).catch((err: Error) => setError(err.message)); }, []);

  const update = <K extends keyof ProfileUpdate>(field: K, value: ProfileUpdate[K]) => { setForm((current) => ({ ...current, [field]: value })); setSaved(false); };
  const save = async (event: React.FormEvent) => { event.preventDefault(); setSaving(true); setError(null); setSaved(false); try { setProfile(await apiUpdateProfile(form)); setSaved(true); } catch (err) { setError(err instanceof Error ? err.message : "Unable to save profile."); } finally { setSaving(false); } };
  const copyId = async () => { if (!profile) return; await navigator.clipboard.writeText(profile.worker_id); setCopied(true); window.setTimeout(() => setCopied(false), 1500); };
  if (error && !profile) return <div className="panel p-8 text-sm text-red-600">Unable to load your profile.</div>;
  if (!profile) return <div className="panel p-8 text-sm text-[#718078]">Loading profile…</div>;
  const numberInput = (field: keyof ProfileUpdate, label: string) => <label className="text-sm font-bold text-[#16231a]">{label}<input className={inputClass} type="number" min="0" value={(form[field] as number | undefined) ?? ""} onChange={(e) => update(field, Number(e.target.value))} /></label>;

  return <div className="mx-auto max-w-4xl animate-fade-in">
    <div className="mb-8"><p className="eyebrow">Your account</p><h1 className="mt-2 text-3xl font-extrabold tracking-tight text-[#16231a]">Profile</h1><p className="muted mt-2">Tell FlowGuard about yourself. FlowGuard learns the rest.</p></div>
    <form onSubmit={save} className="space-y-6"><section className="panel overflow-hidden">
      <div className="bg-[#16231a] px-6 py-8 text-center text-white sm:px-10"><div className="mx-auto grid h-20 w-20 place-items-center rounded-full bg-[#dff1e5] text-2xl font-extrabold text-[#087344] ring-4 ring-white/20">{initials(profile.name)}</div><h2 className="mt-4 text-2xl font-extrabold">{profile.name || "FlowGuard worker"}</h2><p className="mt-1 text-sm text-white/70">{profile.occupation || "Occupation not set"}</p></div>
      <div className="space-y-8 px-6 py-7 sm:px-10">
        <div><h3 className="section-title">Personal details</h3><div className="mt-4 grid gap-4 sm:grid-cols-2"><label className="text-sm font-bold">Name<input className={inputClass} value={form.name ?? ""} onChange={(e) => update("name", e.target.value)} /></label><label className="text-sm font-bold">Occupation<input className={inputClass} value={form.occupation ?? ""} onChange={(e) => update("occupation", e.target.value)} /></label>{numberInput("dependents", "Dependents")}{numberInput("avg_work_hours_per_week", "Work hours / week")}</div></div>
        <div><h3 className="section-title">Platforms</h3><div className="mt-3 flex flex-wrap gap-2">{platforms.map((platform) => { const selected = form.active_platforms?.includes(platform); return <button type="button" key={platform} onClick={() => update("active_platforms", selected ? (form.active_platforms || []).filter((item) => item !== platform) : [...(form.active_platforms || []), platform])} className={`rounded-full border px-3 py-2 text-xs font-bold ${selected ? "border-[#087344] bg-[#dff1e5] text-[#087344]" : "border-gray-200 text-[#718078]"}`}>{selected ? "✓ " : ""}{platform}</button>; })}</div></div>
        <div><h3 className="section-title">Financial profile</h3><div className="mt-4 grid gap-4 sm:grid-cols-2">{numberInput("monthly_income_avg", "Average monthly income")}{numberInput("fixed_expenses", "Fixed expenses")}{numberInput("variable_expenses", "Variable expenses")}{numberInput("total_debt", "Total debt")}{numberInput("monthly_emi", "Monthly EMI")}{numberInput("savings_balance", "Savings balance")}{numberInput("emergency_buffer", "Emergency buffer")}</div></div>
        <div><h3 className="section-title">System insights <span className="normal-case font-semibold tracking-normal text-[#718078]">· calculated automatically</span></h3><div className="mt-4 grid gap-3 sm:grid-cols-2">{[["Current balance", money(profile.current_balance)], ["Income volatility", money(profile.monthly_income_std)], ["Income trend", profile.income_trend], ["Monthly expenses", money(profile.total_monthly_expenses)], ["Expense / income ratio", `${Math.round(profile.expense_to_income_ratio * 100)}%`]].map(([label, value]) => <div className="rounded-xl bg-[#f6f8f5] p-4" key={label}><p className="text-xs text-[#718078]">{label} 🔒</p><p className="mt-1 font-extrabold">{value}</p></div>)}</div></div>
        {error && <p className="rounded-lg bg-red-50 p-3 text-sm text-red-600">{error}</p>}
        <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between"><button type="submit" disabled={saving} className="rounded-xl bg-[#16231a] px-5 py-3 text-sm font-bold text-white hover:bg-black disabled:opacity-50">{saving ? "Saving…" : saved ? "Saved ✓" : "Save changes"}</button><div className="flex items-center gap-3"><span className="text-sm font-bold text-[#718078]">Worker ID: {profile.worker_id}</span><button type="button" onClick={copyId} className="text-xs font-bold text-[#087344]">{copied ? "Copied" : "Copy ID"}</button></div></div>
        <Link href="/dashboard" className="block w-full rounded-xl border border-[#16231a] px-4 py-3 text-center text-sm font-bold text-[#16231a] hover:bg-[#f6f8f5]">Go to Dashboard →</Link>
      </div>
    </section></form>
  </div>;
}
