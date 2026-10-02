import { CircleAlert, Inbox } from "lucide-react";
import { cn } from "@/lib/cn";
import { Button } from "../ui/button";

/** A grey pulsing bar shown while data loads. */
export function Skeleton({ className }: { className?: string }) {
  return <div className={cn("animate-pulse rounded-md bg-subtle", className)} />;
}

export function SkeletonBlock({ rows = 4 }: { rows?: number }) {
  return (
    <div className="space-y-3" aria-busy="true" aria-label="Loading">
      {Array.from({ length: rows }, (_, i) => <Skeleton key={i} className={cn("h-4", i % 3 === 2 ? "w-2/3" : "w-full")} />)}
    </div>
  );
}

export function EmptyState({ title = "Nothing to show", text }: { title?: string; text?: string }) {
  return (
    <div className="flex flex-col items-center gap-2 px-6 py-10 text-center">
      <Inbox size={22} strokeWidth={1.5} className="text-neutral" />
      <p className="text-sm font-medium text-ink">{title}</p>
      {text && <p className="max-w-sm text-sm text-muted">{text}</p>}
    </div>
  );
}

export function ErrorState({ message, onRetry }: { message?: string; onRetry?: () => void }) {
  return (
    <div className="flex flex-col items-center gap-2 px-6 py-10 text-center" role="alert">
      <CircleAlert size={22} strokeWidth={1.5} className="text-risk" />
      <p className="text-sm font-medium text-ink">This could not be loaded</p>
      <p className="max-w-sm text-sm text-muted">{message ?? "Please try again."}</p>
      {onRetry && <Button size="sm" onClick={onRetry} className="mt-2">Try again</Button>}
    </div>
  );
}
