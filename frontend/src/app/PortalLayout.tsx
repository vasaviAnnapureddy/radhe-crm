import { useQuery } from "@tanstack/react-query";
import { BadgeCheck, CalendarDays, ClipboardList, Hammer, Home, LogOut, MessageSquare, Sun, Target, UserRound, Wallet, type LucideIcon } from "lucide-react";
import { Link, NavLink, Outlet, useParams } from "react-router";
import { PageHeader } from "@/components/data/PageHeader";
import { ErrorState, SkeletonBlock } from "@/components/data/States";
import { BlockView } from "@/components/views/Blocks";
import { EntityDrawer } from "@/components/views/EntityDrawer";
import { api } from "@/lib/api";
import { cn } from "@/lib/cn";
import { EntityBase } from "@/lib/entityBase";
import { formatValue } from "@/lib/format";
import type { PortalReply } from "@/lib/types";
import { useAuthActions, useMe } from "./auth";

interface MenuItem { path: string; label: string; icon: LucideIcon }
export interface Portal { base: string; api: string; label: string; menu: MenuItem[] }

export const EMPLOYEE_PORTAL: Portal = {
  base: "/employee", api: "/portal/employee", label: "Employee portal",
  menu: [
    { path: "day", label: "My day", icon: Sun }, { path: "work", label: "My work", icon: ClipboardList },
    { path: "meetings", label: "My meetings", icon: CalendarDays }, { path: "scorecard", label: "My scorecard", icon: Target },
    { path: "profile", label: "My profile", icon: UserRound },
  ],
};
export const CUSTOMER_PORTAL: Portal = {
  base: "/my", api: "/portal/customer", label: "My Radhe home",
  menu: [
    { path: "journey", label: "My journey", icon: Home }, { path: "payments", label: "Payments", icon: Wallet },
    { path: "construction", label: "Construction", icon: Hammer }, { path: "requests", label: "Requests", icon: MessageSquare },
    { path: "profile", label: "My profile", icon: BadgeCheck },
  ],
};

/** The frame of a portal: the same calm sidebar as the console, but only this person's own pages. */
export function PortalLayout({ portal }: { portal: Portal }) {
  const { data: me } = useMe();
  const { logout } = useAuthActions();
  return (
    // Every hover card and drawer below asks the portal's own route, which checks the record is yours.
    <EntityBase.Provider value="/portal/entity">
      <div className="min-h-screen bg-bg">
        <aside className="no-print fixed inset-y-0 left-0 z-30 flex w-16 flex-col bg-sidebar text-bg lg:w-60">
          <Link to={`${portal.base}/${portal.menu[0].path}`} className="flex h-16 items-center px-5 font-display text-lg tracking-wide">
            <span className="lg:hidden">R</span><span className="hidden lg:inline">Radhe Constructions</span>
          </Link>
          <p className="hidden px-5 pb-3 text-[11px] font-semibold uppercase tracking-[0.16em] text-bg/50 lg:block">{portal.label}</p>
          <nav className="flex-1 space-y-0.5 px-2.5" aria-label="Portal pages">
            {portal.menu.map(({ path, label, icon: Icon }) => (
              <NavLink key={path} to={`${portal.base}/${path}`} title={label}
                className={({ isActive }) => cn("flex h-10 items-center gap-3 rounded-md px-3 text-[13.5px] transition-colors duration-150",
                  isActive ? "bg-bg/10 font-semibold text-white" : "text-bg/70 hover:bg-bg/5 hover:text-white")}>
                <Icon size={17} strokeWidth={1.75} className="shrink-0" /><span className="hidden truncate lg:inline">{label}</span>
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
        <div className="pl-16 lg:pl-60">
          <main className="mx-auto max-w-[1180px] px-6 py-10 lg:px-10"><Outlet /></main>
        </div>
        <EntityDrawer />
      </div>
    </EntityBase.Provider>
  );
}

/** One portal page. The server sends the title, the numbers and the blocks; this only draws them. */
export function PortalPage({ portal }: { portal: Portal }) {
  const { page = portal.menu[0].path } = useParams();
  const { data, isPending, error, refetch } = useQuery({
    queryKey: ["portal", portal.api, page],
    queryFn: () => api<PortalReply>(`${portal.api}/${page}`),
  });
  if (error) return <div className="rounded-card border border-line bg-surface"><ErrorState message={(error as Error).message} onRetry={() => refetch()} /></div>;
  if (isPending || !data) return <div className="rounded-card border border-line bg-surface p-6"><SkeletonBlock rows={10} /></div>;
  return (
    <>
      <PageHeader title={data.title} question={data.subtitle} />
      {data.kpis.length > 0 && (
        <div className="mb-6 grid grid-cols-2 gap-4 lg:grid-cols-4">
          {data.kpis.map((item) => (
            <article key={item.label} className="rounded-card border border-line bg-surface p-5">
              <h3 className="text-[13px] font-medium text-muted">{item.label}</h3>
              <p className="mt-3 whitespace-nowrap text-2xl font-semibold leading-none text-ink">{formatValue(item.value, item.kind)}</p>
              {item.note && <p className="mt-2 text-xs text-muted">{item.note}</p>}
            </article>
          ))}
        </div>
      )}
      <div className="space-y-6">{data.blocks.map((block, i) => <BlockView key={i} block={block} />)}</div>
    </>
  );
}
