import { useQuery } from "@tanstack/react-query";
import { Bell, LogOut, Search } from "lucide-react";
import { useEffect, useState } from "react";
import { Link, NavLink, Outlet, useLocation } from "react-router";
import { EntityDrawer } from "@/components/views/EntityDrawer";
import { ExplainDrawer } from "@/components/views/ExplainDrawer";
import { api } from "@/lib/api";
import { cn } from "@/lib/cn";
import { Popover } from "radix-ui";
import type { Metric, RiskCard } from "@/lib/types";
import { keepFilters, RANGES, useFilters } from "@/lib/urlState";
import { useAuthActions, useMe } from "./auth";
import { NAV } from "./nav";
import { SearchPalette } from "./SearchPalette";

const selectClass = "h-9 rounded-md border border-line bg-surface px-2.5 text-[13px] text-ink";

function Sidebar() {
  const { search } = useLocation();
  const { data: me } = useMe();
  const { logout } = useAuthActions();
  const filters = keepFilters(search); // the date range and project follow you from page to page
  return (
    <aside className="no-print fixed inset-y-0 left-0 z-30 flex w-16 flex-col bg-sidebar text-bg lg:w-60">
      <Link to="/" className="flex h-16 items-center px-5 font-display text-lg tracking-wide">
        <span className="lg:hidden">R</span><span className="hidden lg:inline">Radhe Constructions</span>
      </Link>
      <nav className="mt-2 flex-1 space-y-0.5 px-2.5" aria-label="Console pages">
        {NAV.map(({ path, label, icon: Icon }) => (
          <NavLink key={path} to={{ pathname: `/console/${path}`, search: filters }} title={label}
            className={({ isActive }) => cn("flex h-10 items-center gap-3 rounded-md px-3 text-[13.5px] transition-colors duration-150",
              isActive ? "bg-bg/10 font-semibold text-white" : "text-bg/70 hover:bg-bg/5 hover:text-white")}>
            {({ isActive }) => (<>
              <Icon size={17} strokeWidth={1.75} className={cn("shrink-0", isActive && "text-[#E0A988]")} />
              <span className="hidden truncate lg:inline">{label}</span>
            </>)}
          </NavLink>
        ))}
      </nav>
      <div className="border-t border-bg/10 p-2.5">
        <p className="hidden truncate px-3 pb-1 pt-2 text-xs text-bg/60 lg:block">{me?.name}</p>
        <button type="button" onClick={logout} title="Log out"
          className="flex h-10 w-full items-center gap-3 rounded-md px-3 text-[13.5px] text-bg/70 transition-colors duration-150 hover:bg-bg/5 hover:text-white">
          <LogOut size={17} strokeWidth={1.75} className="shrink-0" /><span className="hidden lg:inline">Log out</span>
        </button>
      </div>
    </aside>
  );
}

/** The bell. Clicking it opens the list of high-priority alerts; each one, and "See all", leads to the Risks page. */
function Alerts({ count, risksLink }: { count: number; risksLink: { pathname: string; search: string } }) {
  const [open, setOpen] = useState(false);
  const { data, isPending } = useQuery({
    queryKey: ["risks"], queryFn: () => api<{ items: RiskCard[] }>("/risks"), enabled: open,
  });
  const urgent = (data?.items ?? []).filter((risk) => risk.severity === "high" && risk.status !== "resolved");
  return (
    <Popover.Root open={open} onOpenChange={setOpen}>
      <Popover.Trigger aria-label={`${count} high risks`} title="High-priority alerts"
        className="relative flex h-9 w-9 items-center justify-center rounded-md text-muted transition-colors duration-150 hover:bg-subtle hover:text-ink data-[state=open]:bg-subtle data-[state=open]:text-ink">
        <Bell size={17} strokeWidth={1.75} />
        {count > 0 && <span className="absolute -right-0.5 -top-0.5 flex h-[18px] min-w-[18px] items-center justify-center rounded-full bg-risk px-1 text-[10px] font-semibold text-white">{count}</span>}
      </Popover.Trigger>
      <Popover.Portal>
        <Popover.Content align="end" sideOffset={8} className="z-50 w-[380px] rounded-card border border-line bg-surface shadow-float animate-fade-in">
          <p className="border-b border-line px-4 py-3 text-sm font-semibold text-ink">
            {count} high-priority {count === 1 ? "alert" : "alerts"}
          </p>
          <ul className="max-h-[360px] overflow-y-auto">
            {isPending && <li className="px-4 py-4 text-sm text-muted">Loading alerts</li>}
            {!isPending && !urgent.length && <li className="px-4 py-6 text-center text-sm text-muted">Nothing urgent right now.</li>}
            {urgent.map((risk) => (
              <li key={risk.id} className="border-b border-line last:border-0">
                <Link to={risksLink} onClick={() => setOpen(false)} className="block px-4 py-3 transition-colors duration-150 hover:bg-bg">
                  <span className="block text-[13px] font-medium leading-snug text-ink">{risk.title}</span>
                  <span className="mt-0.5 block text-xs text-muted">{risk.category} · {risk.status === "acknowledged" ? "Acknowledged" : "Open"}</span>
                </Link>
              </li>
            ))}
          </ul>
          <Link to={risksLink} onClick={() => setOpen(false)} className="block border-t border-line px-4 py-3 text-center text-[13px] font-medium text-primary hover:bg-bg">
            See all risks and alerts
          </Link>
        </Popover.Content>
      </Popover.Portal>
    </Popover.Root>
  );
}

function TopBar({ onSearch }: { onSearch: () => void }) {
  const { range, projectId, setRange, setProject, params } = useFilters();
  const { search } = useLocation();
  const { data: projects } = useQuery({ queryKey: ["projects"], queryFn: () => api<{ id: string; name: string }[]>("/projects"), staleTime: Infinity });
  const { data: alerts } = useQuery({ queryKey: ["metric", "open_high_risks", params], queryFn: () => api<Metric>("/metrics/open_high_risks", { params }) });
  return (
    <header className="no-print sticky top-0 z-20 flex h-16 items-center gap-3 border-b border-line bg-bg/95 px-6 backdrop-blur lg:px-10">
      <button type="button" onClick={onSearch}
        className="flex h-9 w-full max-w-sm items-center gap-2.5 rounded-md border border-line bg-surface px-3 text-[13px] text-neutral transition-colors duration-150 hover:border-neutral">
        <Search size={15} strokeWidth={1.75} /><span className="flex-1 truncate text-left">Search buyers, units, people</span>
        <kbd className="rounded border border-line px-1.5 text-[11px] text-muted">Ctrl K</kbd>
      </button>
      <div className="ml-auto flex items-center gap-2.5">
        <select aria-label="Date range" className={selectClass} value={range.key} onChange={(e) => setRange(e.target.value)}>
          {RANGES.map((r) => <option key={r.key} value={r.key}>{r.label}</option>)}
        </select>
        <select aria-label="Project" className={cn(selectClass, "max-w-[180px]")} value={projectId ?? ""} onChange={(e) => setProject(e.target.value || null)}>
          <option value="">All projects</option>
          {projects?.map((p) => <option key={p.id} value={p.id}>{p.name}</option>)}
        </select>
        <Alerts count={alerts?.value ?? 0} risksLink={{ pathname: "/console/risks", search: keepFilters(search) }} />
      </div>
    </header>
  );
}

/** The frame around every console page: sidebar, top bar, the page itself, and the two drawers. */
export function ConsoleLayout() {
  const [searchOpen, setSearchOpen] = useState(false);
  useEffect(() => {
    const onKey = (event: KeyboardEvent) => {
      if ((event.ctrlKey || event.metaKey) && event.key.toLowerCase() === "k") { event.preventDefault(); setSearchOpen((open) => !open); }
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, []);
  return (
    <div className="min-h-screen bg-bg">
      <Sidebar />
      <div className="pl-16 lg:pl-60">
        <TopBar onSearch={() => setSearchOpen(true)} />
        <main className="mx-auto max-w-[1440px] px-6 py-8 lg:px-10"><Outlet /></main>
      </div>
      <SearchPalette open={searchOpen} onOpenChange={setSearchOpen} />
      <EntityDrawer />
      <ExplainDrawer />
    </div>
  );
}
