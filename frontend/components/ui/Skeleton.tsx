import { cn } from "@/lib/utils";

interface SkeletonProps {
  className?: string;
}

/** Base shimmer block. Compose with height + width classes. */
export function Skeleton({ className = "" }: SkeletonProps) {
  return (
    <div
      className={cn(
        "animate-pulse rounded-xl bg-gradient-to-r from-[#e8eeea] via-[#f2f5f3] to-[#e8eeea] bg-[length:400%_100%]",
        className
      )}
      style={{ animation: "pulse 1.8s ease-in-out infinite, shimmer 2s linear infinite" }}
    />
  );
}

/** Full dashboard loading skeleton — 2-column grid layout */
export function DashboardSkeleton() {
  return (
    <div className="animate-fade-in grid gap-5">
      <div className="grid gap-5 xl:grid-cols-[1.15fr_.85fr]">
        <Skeleton className="h-48" />
        <div className="grid gap-5 sm:grid-cols-2 xl:grid-cols-1">
          <Skeleton className="h-[90px]" />
          <Skeleton className="h-[90px]" />
        </div>
      </div>
      <div className="grid gap-5 xl:grid-cols-[1.15fr_.85fr]">
        <Skeleton className="h-72" />
        <Skeleton className="h-72" />
      </div>
      <div className="grid gap-5 lg:grid-cols-2">
        <Skeleton className="h-28" />
        <Skeleton className="h-28" />
      </div>
    </div>
  );
}

/** Forecast page skeleton */
export function ForecastSkeleton() {
  return (
    <div className="animate-fade-in grid gap-5">
      <div className="grid gap-4 sm:grid-cols-3">
        <Skeleton className="h-24" />
        <Skeleton className="h-24" />
        <Skeleton className="h-24" />
      </div>
      <Skeleton className="h-72" />
      <Skeleton className="h-28" />
    </div>
  );
}

/** Resilience page skeleton */
export function ResilienceSkeleton() {
  return (
    <div className="animate-fade-in grid gap-5 lg:grid-cols-2">
      <Skeleton className="h-80" />
      <Skeleton className="h-80" />
    </div>
  );
}

/** Generic table/list skeleton */
export function TableSkeleton({ rows = 5 }: { rows?: number }) {
  return (
    <div className="panel animate-fade-in">
      <Skeleton className="mb-5 h-5 w-40" />
      <div className="space-y-3">
        {Array.from({ length: rows }).map((_, i) => (
          <Skeleton key={i} className="h-10" />
        ))}
      </div>
    </div>
  );
}
