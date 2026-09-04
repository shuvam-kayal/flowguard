"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { apiMe, type UserProfile } from "@/lib/api";

function getInitials(name: string) {
  return name.split(" ").filter(Boolean).slice(0, 2).map((part) => part[0]?.toUpperCase()).join("") || "FG";
}

export default function ProfilePage() {
  const [profile, setProfile] = useState<UserProfile | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [copied, setCopied] = useState(false);

  useEffect(() => {
    apiMe().then(setProfile).catch((err: Error) => setError(err.message));
  }, []);

  const copyWorkerId = async () => {
    if (!profile) return;
    await navigator.clipboard.writeText(profile.worker_id);
    setCopied(true);
    window.setTimeout(() => setCopied(false), 1500);
  };

  if (error) return <div className="panel p-8 text-sm text-red-600">Unable to load your profile.</div>;
  if (!profile) return <div className="panel p-8 text-sm text-[#718078]">Loading profile…</div>;

  return (
    <div className="mx-auto max-w-2xl animate-fade-in">
      <div className="mb-8">
        <p className="eyebrow">Your account</p>
        <h1 className="mt-2 text-3xl font-extrabold tracking-tight text-[#16231a]">Profile</h1>
        <p className="muted mt-2">Your FlowGuard worker identity and account details.</p>
      </div>

      <section className="panel overflow-hidden">
        <div className="bg-[#16231a] px-6 py-10 text-center text-white sm:px-10">
          <div className="mx-auto grid h-20 w-20 place-items-center rounded-full bg-[#dff1e5] text-2xl font-extrabold text-[#087344] ring-4 ring-white/20">
            {getInitials(profile.name)}
          </div>
          <h2 className="mt-4 text-2xl font-extrabold">{profile.name || "FlowGuard worker"}</h2>
          <p className="mt-1 text-sm text-white/70">{profile.occupation || "Occupation not set"}</p>
        </div>

        <div className="space-y-5 px-6 py-7 sm:px-10">
          <div className="rounded-2xl border border-[#b9e6c8] bg-[#f1faf4] p-5">
            <p className="text-[11px] font-bold uppercase tracking-[0.16em] text-[#087344]">FlowGuard Worker ID</p>
            <div className="mt-2 flex items-center justify-between gap-4">
              <p className="text-2xl font-extrabold tracking-wide text-[#16231a]">{profile.worker_id}</p>
              <button onClick={copyWorkerId} className="rounded-lg bg-white px-3 py-2 text-xs font-bold text-[#087344] shadow-sm hover:bg-[#dff1e5]">
                {copied ? "Copied" : "Copy ID"}
              </button>
            </div>
          </div>

          <dl className="grid gap-4 sm:grid-cols-2">
            <div><dt className="text-xs font-bold uppercase tracking-wide text-[#718078]">Email</dt><dd className="mt-1 font-semibold text-[#16231a]">{profile.email || "—"}</dd></div>
            <div><dt className="text-xs font-bold uppercase tracking-wide text-[#718078]">Phone</dt><dd className="mt-1 font-semibold text-[#16231a]">{profile.phone || "—"}</dd></div>
          </dl>

          <div className="border-t border-[#e4ebe5] pt-5">
            <p className="text-sm font-bold text-[#16231a]">Financial account</p>
            <p className="mt-1 text-sm text-[#718078]">Your account is connected to FlowGuard’s simulated financial data.</p>
          </div>

          <Link href="/dashboard" className="block w-full rounded-xl bg-[#16231a] px-4 py-3 text-center text-sm font-bold text-white transition-colors hover:bg-black">
            Go to Dashboard →
          </Link>
        </div>
      </section>
    </div>
  );
}
