import { X } from "lucide-react";
import { Dialog } from "radix-ui";
import type { ReactNode } from "react";
import { cn } from "@/lib/cn";

/** A panel that slides in from the right. Used for the entity drawer and the Explain drawer. */
export function Sheet({ open, onClose, title, description, header, children, wide }: {
  open: boolean; onClose: () => void; title: string; description?: string; header?: ReactNode; children: ReactNode;
  wide?: boolean;
}) {
  return (
    <Dialog.Root open={open} onOpenChange={(next) => !next && onClose()}>
      <Dialog.Portal>
        <Dialog.Overlay className="fixed inset-0 z-40 bg-ink/25 animate-fade-in" />
        <Dialog.Content
          className={cn("fixed inset-y-0 right-0 z-40 flex w-full flex-col border-l border-line bg-bg shadow-float",
            "animate-sheet-in focus:outline-none", wide ? "max-w-[860px]" : "max-w-[680px]")}
        >
          <div className="flex items-start justify-between gap-4 border-b border-line bg-surface px-6 py-4">
            <div className="min-w-0 flex-1">
              {header}
              <Dialog.Title className="truncate font-display text-[22px] leading-tight text-ink">{title}</Dialog.Title>
              <Dialog.Description className="mt-0.5 truncate text-sm text-muted">{description ?? " "}</Dialog.Description>
            </div>
            <Dialog.Close className="rounded-md p-1.5 text-muted hover:bg-subtle hover:text-ink" aria-label="Close">
              <X size={18} strokeWidth={1.75} />
            </Dialog.Close>
          </div>
          <div className="flex-1 overflow-y-auto px-6 py-5">{children}</div>
        </Dialog.Content>
      </Dialog.Portal>
    </Dialog.Root>
  );
}
