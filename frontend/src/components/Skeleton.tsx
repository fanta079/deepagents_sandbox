"use client";

import { cn } from "@/lib/utils";

export function MessageSkeleton() {
  return (
    <div className="animate-pulse flex items-start gap-3" aria-hidden="true" role="presentation">
      <div className="w-8 h-8 rounded-full bg-gray-200 dark:bg-gray-700 flex-shrink-0" />
      <div className="flex-1 space-y-2 min-w-0">
        <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded w-3/4" />
        <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded w-1/2" />
      </div>
    </div>
  );
}

export function CardSkeleton() {
  return (
    <div className="animate-pulse rounded-xl border border-border bg-card p-4 space-y-3" aria-hidden="true" role="presentation">
      <div className="h-5 bg-gray-200 dark:bg-gray-700 rounded w-2/3" />
      <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded w-full" />
      <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded w-4/5" />
      <div className="h-8 bg-gray-200 dark:bg-gray-700 rounded w-1/3 mt-4" />
    </div>
  );
}

export function TableRowSkeleton({ cols = 5 }: { cols?: number }) {
  return (
    <tr className="animate-pulse" aria-hidden="true" role="presentation">
      {Array.from({ length: cols }).map((_, i) => (
        <td key={i} className="px-4 py-3">
          <div
            className={cn(
              "h-4 bg-gray-200 dark:bg-gray-700 rounded",
              i === 0 ? "w-3/4" : i === cols - 1 ? "w-1/2" : "w-full"
            )}
          />
        </td>
      ))}
    </tr>
  );
}
