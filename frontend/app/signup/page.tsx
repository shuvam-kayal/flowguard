"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { apiSignup } from "@/lib/api";
import Link from "next/link";

export default function SignupPage() {
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [phone, setPhone] = useState("");
  const [occupation, setOccupation] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const router = useRouter();

  const handleSignup = async (e: React.FormEvent) => {
    e.preventDefault();
    if (password !== confirmPassword) {
      setError("Passwords do not match.");
      return;
    }
    setLoading(true);
    setError(null);

    try {
      const data = await apiSignup(email, phone, name, occupation, password);
      localStorage.setItem("flowguard_token", data.access_token);
      router.push("/profile");
    } catch (err: any) {
      setError(err.message || "Failed to sign up. Try again.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex min-h-screen items-center justify-center p-4">
      <div className="panel w-full max-w-md p-8 animate-fade-in shadow-xl">
        <div className="mb-8 text-center">
          <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-xl bg-black">
            <svg
              className="h-6 w-6 text-white"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M18 9v3m0 0v3m0-3h3m-3 0h-3m-2-5a4 4 0 11-8 0 4 4 0 018 0zM3 20a6 6 0 0112 0v1H3v-1z"
              />
            </svg>
          </div>
          <h1 className="mt-4 text-2xl font-extrabold text-[#16231a]">Create Account</h1>
          <p className="muted mt-2 text-sm">Join FlowGuard and manage your gig finances</p>
        </div>

        <form onSubmit={handleSignup} className="space-y-4">
          {error && (
            <div className="rounded-lg bg-red-50 p-3 text-sm text-red-600 border border-red-200">
              {error}
            </div>
          )}
          
          <div>
            <label className="mb-1 block text-sm font-bold text-[#16231a]">
              Full Name
            </label>
            <input
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              className="w-full rounded-xl border border-gray-200 px-4 py-3 text-sm focus:border-black focus:outline-none focus:ring-1 focus:ring-black"
              placeholder="e.g. Rahul Kumar"
              required
            />
          </div>

          <div>
            <label className="mb-1 block text-sm font-bold text-[#16231a]">Email</label>
            <input type="email" value={email} onChange={(e) => setEmail(e.target.value)}
              className="w-full rounded-xl border border-gray-200 px-4 py-3 text-sm focus:border-black focus:outline-none focus:ring-1 focus:ring-black"
              placeholder="you@example.com" required />
          </div>

          <div>
            <label className="mb-1 block text-sm font-bold text-[#16231a]">Phone number</label>
            <input type="tel" value={phone} onChange={(e) => setPhone(e.target.value)}
              className="w-full rounded-xl border border-gray-200 px-4 py-3 text-sm focus:border-black focus:outline-none focus:ring-1 focus:ring-black"
              placeholder="e.g. 9876543210" required />
          </div>

          <div>
            <label className="mb-1 block text-sm font-bold text-[#16231a]">
              Occupation
            </label>
            <input
              type="text"
              value={occupation}
              onChange={(e) => setOccupation(e.target.value)}
              className="w-full rounded-xl border border-gray-200 px-4 py-3 text-sm focus:border-black focus:outline-none focus:ring-1 focus:ring-black"
              placeholder="e.g. Delivery Partner"
              required
            />
          </div>

          <div>
            <label className="mb-1 block text-sm font-bold text-[#16231a]">Confirm password</label>
            <input type="password" value={confirmPassword} onChange={(e) => setConfirmPassword(e.target.value)}
              className="w-full rounded-xl border border-gray-200 px-4 py-3 text-sm focus:border-black focus:outline-none focus:ring-1 focus:ring-black"
              required />
          </div>

          <div>
            <label className="mb-1 block text-sm font-bold text-[#16231a]">
              Password
            </label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="w-full rounded-xl border border-gray-200 px-4 py-3 text-sm focus:border-black focus:outline-none focus:ring-1 focus:ring-black"
              required
            />
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full rounded-xl bg-[#16231a] px-4 py-3 font-bold text-white transition-colors hover:bg-black disabled:opacity-50 mt-4"
          >
            {loading ? "Simulating Bank Sync..." : "Sign Up & Sync Bank"}
          </button>
        </form>

        <div className="mt-6 text-center text-sm">
          <span className="text-gray-500">Already have an account? </span>
          <Link href="/login" className="font-bold text-black hover:underline">
            Sign in
          </Link>
        </div>
      </div>
    </div>
  );
}
