import { useQuery } from "@tanstack/react-query";
import { Command } from "cmdk";
import { Search } from "lucide-react";
import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import type { Ref } from "@/lib/types";
import { useDrawer } from "@/lib/urlState";

interface Group { label: string; items: (Ref & { subtitle: string })[] }

/** Global search (Ctrl+K). Finds customers, units, projects, employees, leads and channel partners. */
export function SearchPalette({ open, onOpenChange }: { open: boolean; onOpenChange: (open: boolean) => void }) {
  const drawer = useDrawer();
  const [typed, setTyped] = useState("");
  const [q, setQ] = useState("");

  useEffect(() => {
    const timer = setTimeout(() => setQ(typed.trim()), 200);
    return () => clearTimeout(timer);
  }, [typed]);
  useEffect(() => { if (!open) setTyped(""); }, [open]);

  const { data, isFetching } = useQuery({
    queryKey: ["search", q],
    queryFn: () => api<Group[]>("/search", { params: { q } }),
    enabled: open && q.length >= 2,
  });

  return (
    <Command.Dialog open={open} onOpenChange={onOpenChange} shouldFilter={false} label="Search"
      overlayClassName="fixed inset-0 z-50 bg-ink/25 animate-fade-in"
      contentClassName="fixed left-1/2 top-[14vh] z-50 w-[92vw] max-w-xl -translate-x-1/2 overflow-hidden rounded-card border border-line bg-surface shadow-float">
      <div className="flex items-center gap-3 border-b border-line px-4">
        <Search size={17} strokeWidth={1.75} className="text-neutral" />
        <Command.Input value={typed} onValueChange={setTyped} placeholder="Search a buyer, unit, project, employee or partner"
          className="h-12 w-full bg-transparent text-sm outline-none placeholder:text-neutral" />
      </div>
      <Command.List className="max-h-[52vh] overflow-y-auto p-2">
        {q.length < 2 && <p className="px-3 py-6 text-center text-sm text-muted">Type at least two letters.</p>}
        {q.length >= 2 && !isFetching && !data?.length && <Command.Empty className="px-3 py-6 text-center text-sm text-muted">Nothing found for "{q}".</Command.Empty>}
        {data?.map((group) => (
          <Command.Group key={group.label} heading={group.label}
            className="[&_[cmdk-group-heading]]:px-3 [&_[cmdk-group-heading]]:py-1.5 [&_[cmdk-group-heading]]:text-xs [&_[cmdk-group-heading]]:font-semibold [&_[cmdk-group-heading]]:text-muted">
            {group.items.map((item) => (
              <Command.Item key={`${item.type}:${item.id}`} value={`${item.type}:${item.id}`}
                onSelect={() => { onOpenChange(false); drawer.open(item.type, item.id); }}
                className="flex cursor-pointer items-center justify-between gap-3 rounded-md px-3 py-2 text-sm data-[selected=true]:bg-subtle">
                <span className="truncate font-medium text-ink">{item.label}</span>
                <span className="shrink-0 truncate text-xs text-muted">{item.subtitle}</span>
              </Command.Item>
            ))}
          </Command.Group>
        ))}
      </Command.List>
    </Command.Dialog>
  );
}
