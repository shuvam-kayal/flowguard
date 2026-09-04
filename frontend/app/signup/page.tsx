"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { apiSignup } from "@/lib/api";
import Link from "next/link";

export default function SignupPage() {
  const [workerId,    setWorkerId]    = useState("");
  const [name,        setName]        = useState("");
  const [occupation,  setOccupation]  = useState("");
  const [password,    setPassword]    = useState("");
  const [error,       setError]       = useState<string | null>(null);
  const [loading,     setLoading]     = useState(false);
  const router = useRouter();

  const handleSignup = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    try {
      const data = await apiSignup(workerId, name, occupation, password);
      localStorage.setItem("flowguard_token", data.access_token);
      router.push("/dashboard");
    } catch (err: any) {
      const isConflict = err.message?.includes("400") || err.message?.includes("already registered");
      setError(
        isConflict
          ? "This Worker ID is already taken. Please choose a different one."
          : "Something went wrong. Please try again."
      );
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex min-h-screen items-center justify-center p-4 bg-[#f9fafb]">
      <div className="w-full max-w-sm">
        {/* Logo */}
        <div className="mb-8 text-center">
          <div className="mx-auto flex h-11 w-11 items-center justify-center rounded-xl bg-[#0f3726]">
            <span className="text-lg font-black text-white">F</span>
          </div>
          <h1 className="mt-4 text-xl font-bold text-[#111827]">Create your account</h1>
          <p className="mt-1 text-sm text-[#6b7280]">
            Join FlowGuard and take control of your gig finances
          </p>
        </div>

        <div className="rounded-xl border border-[#e5e7eb] bg-white p-6 shadow-sm">
          <form onSubmit={handleSignup} className="space-y-4">
            {error && (
              <div className="rounded-lg border border-[#f5c6c2] bg-[#fef5f4] px-3.5 py-3 text-sm text-[#c0392b]">
                {error}
              </div>
            )}

            <div>
              <label className="mb-1.5 block text-sm font-semibold text-[#374151]">
                Worker ID
              </label>
              <input
                type="text"
                value={workerId}
                onChange={(e) => setWorkerId(e.target.value)}
                className="input"
                placeholder="e.g. W123"
                required
                autoComplete="username"
              />
              <p className="mt-1 text-xs text-[#9ca3af]">Choose a unique ID. You'll use this to log in.</p>
            </div>

            <div>
              <label className="mb-1.5 block text-sm font-semibold text-[#374151]">
                Full name
              </label>
              <input
                type="text"
                value={name}
                onChange={(e) => setName(e.target.value)}
                className="input"
                placeholder="e.g. Rahul Kumar"
                required
                autoComplete="name"
              />
            </div>

            <div>
              <label className="mb-1.5 block text-sm font-semibold text-[#374151]">
                Your work
              </label>
              <input
                type="text"
                value={occupation}
                onChange={(e) => setOccupation(e.target.value)}
                className="input"
                placeholder="e.g. Delivery Partner, Driver"
                required
              />
            </div>

            <div>
              <label className="mb-1.5 block text-sm font-semibold text-[#374151]">
                Password
              </label>
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="input"
                required
                autoComplete="new-password"
              />
            </div>

            <button
              type="submit"
              disabled={loading}
              className="btn-primary mt-1 w-full justify-center"
            >
              {loading ? "Setting up your account…" : "Create account"}
            </button>
          </form>

          <p className="mt-4 text-center text-xs text-[#9ca3af]">
            Your account comes with a simulated financial profile so you can explore all features.
          </p>

          <div className="mt-4 text-center text-sm">
            <span className="text-[#9ca3af]">Already have an account? </span>
            <Link href="/login" className="font-semibold text-[#087344] hover:underline">
              Sign in
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
}
