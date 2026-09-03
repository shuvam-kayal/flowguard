"use client";

import { AlertTriangle, RefreshCw } from "lucide-react";

interface ErrorStateProps {
  message: string;
  onRetry?: () => void;
}

export function ErrorState({ message, onRetry }: ErrorStateProps) {
  const handleRetry = () => {
    if (onRetry) {
      onRetry();
    } else {
      window.location.reload();
    }
  };

  return (
    <div className="panel animate-fade-in max-w-lg">
      <div className="flex items-start gap-4">
        <div className="grid h-10 w-10 shrink-0 place-items-center rounded-full bg-[#fde8e8]">
          <AlertTriangle size={18} className="text-[#b93a3a]" />
        </div>
        <div className="min-w-0">
          <h2 className="text-base font-bold text-[#16231a]">
            Unable to load your financial data
          </h2>
          <p className="muted mt-1 break-words">{message}</p>
        </div>
      </div>
      <button
        onClick={handleRetry}
        className="btn-primary mt-5 text-sm"
      >
        <RefreshCw size={14} />
        Try again
      </button>
    </div>
  );
}
