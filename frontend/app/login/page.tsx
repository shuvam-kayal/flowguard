"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { apiLogin } from "@/lib/api";
import Link from "next/link";

export default function LoginPage() {
  const [workerId, setWorkerId] = useState("W001");
  const [password, setPassword] = useState("password123");
  const [error, setError]       = useState<string | null>(null);
  const [loading, setLoading]   = useState(false);
  const router = useRouter();

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    try {
      const data = await apiLogin(workerId, password);
      localStorage.setItem("flowguard_token", data.access_token);
      router.push("/dashboard");
    } catch {
      setError("Incorrect Worker ID or password. Please try again.");
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
          <h1 className="mt-4 text-xl font-bold text-[#111827]">Sign in to FlowGuard</h1>
          <p className="mt-1 text-sm text-[#6b7280]">Your gig worker financial dashboard</p>
        </div>

        <div className="rounded-xl border border-[#e5e7eb] bg-white p-6 shadow-sm">
          <form onSubmit={handleLogin} className="space-y-4">
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
                placeholder="e.g. W001"
                required
                autoComplete="username"
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
                autoComplete="current-password"
              />
            </div>

            <button
              type="submit"
              disabled={loading}
              className="btn-primary mt-1 w-full justify-center"
            >
              {loading ? "Signing in…" : "Sign in"}
            </button>
          </form>

          <div className="mt-5 text-center text-sm">
            <span className="text-[#9ca3af]">New to FlowGuard? </span>
            <Link href="/signup" className="font-semibold text-[#087344] hover:underline">
              Create an account
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
}
