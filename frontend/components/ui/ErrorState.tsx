"use client";

import { AlertCircle, RefreshCw } from "lucide-react";

interface ErrorStateProps {
  message: string;
  onRetry?: () => void;
}

export function ErrorState({ message, onRetry }: ErrorStateProps) {
  const isAuth = message.includes("401") || message.includes("Unauthorized");

  return (
    <div className="rounded-xl border border-[#f5c6c2] bg-[#fef5f4] p-6 animate-fade-in max-w-lg">
      <div className="flex items-start gap-3">
        <div className="grid h-9 w-9 shrink-0 place-items-center rounded-full bg-[#fde8e4]">
          <AlertCircle size={17} className="text-[#c0392b]" />
        </div>
        <div>
          <h2 className="text-sm font-bold text-[#111827]">
            {isAuth ? "Please sign in again" : "Something went wrong"}
          </h2>
          <p className="mt-1 text-sm text-[#6b7280]">
            {isAuth
              ? "Your session has expired or you need to log in to view this page."
              : "We couldn't load your financial data. This might be a temporary issue."}
          </p>
        </div>
      </div>
      <div className="mt-4 flex gap-3">
        <button
          onClick={() => {
            if (onRetry) onRetry();
            else window.location.reload();
          }}
          className="btn-ghost text-sm"
        >
          <RefreshCw size={13} />
          Try again
        </button>
        {isAuth && (
          <a href="/login" className="btn-primary text-sm">
            Sign in
          </a>
        )}
      </div>
    </div>
  );
}
