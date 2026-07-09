import { AlertCircle, RotateCw } from "lucide-react";

// Shared error/not-found card. Pass onRetry to show a "Try again" button.
export default function ErrorState({ title = "Something went wrong", message, onRetry }) {
  return (
    <div className="rounded-lg border border-border bg-muted/40 p-5">
      <div className="flex items-start gap-3">
        <AlertCircle className="mt-0.5 h-5 w-5 shrink-0 text-muted-foreground" aria-hidden="true" />
        <div className="flex-1">
          <p className="font-medium">{title}</p>
          {message && <p className="mt-0.5 text-sm text-muted-foreground">{message}</p>}
          {onRetry && (
            <button
              onClick={onRetry}
              className="mt-3 inline-flex items-center gap-1.5 rounded-md border px-3 py-1.5 text-sm hover:bg-muted"
            >
              <RotateCw className="h-3.5 w-3.5" aria-hidden="true" />
              Try again
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
