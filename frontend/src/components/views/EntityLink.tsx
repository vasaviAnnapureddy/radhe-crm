import { HoverCard } from "radix-ui";
import { useEffect, useState, type ReactNode } from "react";
import { cn } from "@/lib/cn";
import { ENTITY_PATH, type Ref } from "@/lib/types";
import { useDrawer } from "@/lib/urlState";
import { QuickViewLoader } from "./QuickView";

/**
 * Hover to peek, click to pin. Wrap any name, unit, deal or tower in this:
 * hovering (or keyboard focus) shows the quick view after 300 ms; clicking pins it as a drawer.
 * On touch screens a tap opens the drawer.
 */
export function EntityLink({ entity, children, className, plain }: {
  entity: Ref; children?: ReactNode; className?: string;
  plain?: boolean; // no underline style: the caller styles it (used by the unit grid cells)
}) {
  const drawer = useDrawer();
  const [open, setOpen] = useState(false);
  const pinned = drawer.stack.length;
  useEffect(() => setOpen(false), [pinned]); // a drawer opened or closed: put the hover card away
  if (!(entity.type in ENTITY_PATH)) return <span>{children ?? entity.label}</span>;
  return (
    <HoverCard.Root openDelay={300} closeDelay={80} open={open} onOpenChange={setOpen}>
      <HoverCard.Trigger asChild>
        <button
          type="button"
          onClick={(event) => { event.stopPropagation(); setOpen(false); drawer.open(entity.type, entity.id); }}
          className={plain ? className : cn("max-w-full truncate text-left font-medium text-ink underline decoration-line decoration-1 underline-offset-4 transition-colors duration-150 hover:decoration-primary", className)}
        >
          {children ?? entity.label}
        </button>
      </HoverCard.Trigger>
      {open && (
        <HoverCard.Portal>
          <HoverCard.Content
            side="right" align="start" sideOffset={10} collisionPadding={16}
            className="z-50 w-[340px] rounded-card border border-line bg-surface p-4 shadow-float animate-fade-in"
          >
            <QuickViewLoader entity={entity} />
          </HoverCard.Content>
        </HoverCard.Portal>
      )}
    </HoverCard.Root>
  );
}
