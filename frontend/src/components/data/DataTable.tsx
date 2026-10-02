import { keepPreviousData, useQuery } from "@tanstack/react-query";
import { flexRender, getCoreRowModel, useReactTable, type ColumnDef, type VisibilityState } from "@tanstack/react-table";
import { ArrowDown, ArrowUp, ChevronLeft, ChevronRight, Columns3, Download, Search } from "lucide-react";
import { Popover } from "radix-ui";
import { useEffect, useMemo, useState } from "react";
import { api, type Params } from "@/lib/api";
import { cn } from "@/lib/cn";
import { num } from "@/lib/format";
import type { ListReply, Row } from "@/lib/types";
import { useDrawer } from "@/lib/urlState";
import { Button } from "../ui/button";
import { Cell, cellText, RIGHT_ALIGNED } from "./Cell";
import { EmptyState, ErrorState, Skeleton } from "./States";

interface Props {
  endpoint: string;       // for example "/customers"
  params?: Params;        // global filters and tab filters
  pageSize?: number;
  searchable?: boolean;
  exportName?: string;    // file name for the CSV export
  search?: string;        // set from outside, for example when a chart bar is clicked
}

/**
 * The one table used on every page. The backend sends the columns, so each page only names an endpoint.
 * Search, sort and paging happen on the server. Extra columns come from the column chooser.
 * Clicking a row pins its drawer; hovering a name shows its quick view.
 */
export function DataTable({ endpoint, params, pageSize = 10, searchable = true, exportName, search }: Props) {
  const drawer = useDrawer();
  const [page, setPage] = useState(1);
  const [sort, setSort] = useState<{ key: string; order: "asc" | "desc" } | null>(null);
  const [typed, setTyped] = useState("");
  const [q, setQ] = useState("");
  const [visibility, setVisibility] = useState<VisibilityState | null>(null);

  useEffect(() => {  // wait 300 ms after typing stops before searching
    const timer = setTimeout(() => { setQ(typed); setPage(1); }, 300);
    return () => clearTimeout(timer);
  }, [typed]);
  useEffect(() => { if (search !== undefined) setTyped(search); }, [search]);
  const filterKey = JSON.stringify(params ?? {});
  useEffect(() => setPage(1), [filterKey]);

  // A page may pass a starting sort in `params`; clicking a column header overrides it.
  const query = { ...params, page, page_size: pageSize, ...(sort ? { sort: sort.key, order: sort.order } : {}), q };
  const { data, isError, error, refetch, isFetching } = useQuery({
    queryKey: ["list", endpoint, query],
    queryFn: () => api<ListReply>(endpoint, { params: query }),
    placeholderData: keepPreviousData,
  });

  const columns = useMemo<ColumnDef<Row>[]>(() => (data?.columns ?? []).map((column) => ({
    id: column.key,
    header: column.label,
    accessorFn: (row: Row) => row[column.key],
    cell: (info) => <Cell value={info.getValue()} kind={column.kind} />,
    meta: { kind: column.kind },
  })), [data?.columns]);

  const defaults = useMemo(() => Object.fromEntries((data?.columns ?? []).map((c) => [c.key, c.default])), [data?.columns]);
  const table = useReactTable({
    data: data?.items ?? [],
    columns,
    getCoreRowModel: getCoreRowModel(),
    manualSorting: true,
    manualPagination: true,
    state: { columnVisibility: visibility ?? defaults },
    onColumnVisibilityChange: (updater) => setVisibility((old) => (typeof updater === "function" ? updater(old ?? defaults) : updater)),
  });

  function toggleSort(key: string) {
    setSort((old) => (old?.key !== key ? { key, order: "asc" } : old.order === "asc" ? { key, order: "desc" } : null));
    setPage(1);
  }

  async function exportCsv() {
    const all = await api<ListReply>(endpoint, { params: { ...query, page: 1, page_size: 5000 } });
    const shown = all.columns.filter((c) => table.getColumn(c.key)?.getIsVisible());
    const quote = (text: string) => `"${text.replace(/"/g, '""')}"`;
    const lines = [shown.map((c) => quote(c.label)).join(","),
      ...all.items.map((row) => shown.map((c) => quote(cellText(row[c.key]))).join(","))];
    const link = document.createElement("a");
    link.href = URL.createObjectURL(new Blob(["﻿" + lines.join("\n")], { type: "text/csv;charset=utf-8" }));
    link.download = `${exportName ?? endpoint.replace(/\W+/g, "-").replace(/^-/, "")}.csv`;
    link.click();
    URL.revokeObjectURL(link.href);
  }

  if (isError) return <ErrorState message={(error as Error).message} onRetry={() => refetch()} />;
  const total = data?.total ?? 0;
  const first = total ? (page - 1) * pageSize + 1 : 0;
  const last = Math.min(page * pageSize, total);

  return (
    <div>
      <div className="no-print mb-3 flex flex-wrap items-center justify-between gap-3">
        {searchable ? (
          <label className="relative block w-full max-w-xs">
            <Search size={15} strokeWidth={1.75} className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-neutral" />
            <input
              value={typed} onChange={(event) => setTyped(event.target.value)} placeholder="Search this table"
              className="h-9 w-full rounded-md border border-line bg-surface pl-9 pr-3 text-sm placeholder:text-neutral"
            />
          </label>
        ) : <span />}
        <div className="flex items-center gap-2">
          <Popover.Root>
            <Popover.Trigger asChild>
              <Button size="sm" variant="ghost"><Columns3 size={15} strokeWidth={1.75} />Columns</Button>
            </Popover.Trigger>
            <Popover.Portal>
              <Popover.Content align="end" sideOffset={6} className="z-50 w-56 rounded-card border border-line bg-surface p-2 shadow-float">
                {table.getAllLeafColumns().map((column) => (
                  <label key={column.id} className="flex items-center gap-2 rounded px-2 py-1.5 text-sm hover:bg-subtle">
                    <input type="checkbox" checked={column.getIsVisible()} onChange={column.getToggleVisibilityHandler()} className="accent-primary" />
                    {String(column.columnDef.header)}
                  </label>
                ))}
              </Popover.Content>
            </Popover.Portal>
          </Popover.Root>
          <Button size="sm" variant="ghost" onClick={exportCsv} disabled={!total}><Download size={15} strokeWidth={1.75} />CSV</Button>
        </div>
      </div>

      <div className={cn("overflow-x-auto rounded-card border border-line bg-surface transition-opacity duration-150", isFetching && data && "opacity-70")}>
        <table className="w-full text-sm">
          <thead>
            {table.getHeaderGroups().map((group) => (
              <tr key={group.id} className="border-b border-line">
                {group.headers.map((header) => {
                  const right = RIGHT_ALIGNED.has((header.column.columnDef.meta as { kind: string }).kind);
                  const active = sort?.key === header.column.id;
                  return (
                    <th key={header.id} className={cn("whitespace-nowrap px-4 py-3 text-xs font-semibold text-muted", right ? "text-right" : "text-left")}>
                      <button type="button" onClick={() => toggleSort(header.column.id)} className="inline-flex items-center gap-1 hover:text-ink">
                        {flexRender(header.column.columnDef.header, header.getContext())}
                        {active && (sort.order === "asc" ? <ArrowUp size={12} /> : <ArrowDown size={12} />)}
                      </button>
                    </th>
                  );
                })}
              </tr>
            ))}
          </thead>
          <tbody>
            {!data && Array.from({ length: 6 }, (_, i) => (
              <tr key={i} className="border-b border-line last:border-0">
                <td colSpan={99} className="px-4 py-3.5"><Skeleton className="h-4 w-full" /></td>
              </tr>
            ))}
            {table.getRowModel().rows.map((row) => {
              const item = row.original;
              const opens = Boolean(item.type);
              return (
                <tr
                  key={row.id}
                  onClick={opens ? () => drawer.open(item.type!, item.target_id ?? item.id) : undefined}
                  className={cn("border-b border-line transition-colors duration-150 last:border-0", opens && "cursor-pointer hover:bg-bg")}
                >
                  {row.getVisibleCells().map((cell) => (
                    <td key={cell.id} className={cn("max-w-[260px] truncate px-4 py-3",
                      RIGHT_ALIGNED.has((cell.column.columnDef.meta as { kind: string }).kind) && "text-right")}>
                      {flexRender(cell.column.columnDef.cell, cell.getContext())}
                    </td>
                  ))}
                </tr>
              );
            })}
          </tbody>
        </table>
        {data && total === 0 && <EmptyState text={q ? `No rows match "${q}".` : "There are no rows for these filters."} />}
      </div>

      {total > pageSize && (
        <div className="no-print mt-3 flex items-center justify-end gap-3 text-xs text-muted">
          <span>{num(first)} to {num(last)} of {num(total)}</span>
          <Button size="icon" variant="ghost" aria-label="Previous page" disabled={page === 1} onClick={() => setPage(page - 1)}><ChevronLeft size={16} /></Button>
          <Button size="icon" variant="ghost" aria-label="Next page" disabled={last >= total} onClick={() => setPage(page + 1)}><ChevronRight size={16} /></Button>
        </div>
      )}
    </div>
  );
}
