import { useQueries } from "@tanstack/react-query";
import { ChevronRight, CircleAlert } from "lucide-react";
import { api } from "@/lib/api";
import { useEntityBase } from "@/lib/entityBase";
import { entityUrl, type EntityView } from "@/lib/types";
import { useDrawer } from "@/lib/urlState";
import { ErrorState, SkeletonBlock } from "../data/States";
import { StatusPill } from "../data/Value";
import { Sheet } from "../ui/sheet";
import { Tabs } from "../ui/tabs";
import { BlockView } from "./Blocks";

/**
 * The pinned drawer. Its state lives in the URL (?view=customer:1,unit:2), so the browser Back button
 * closes one level. Links inside open the related entity on top, with a breadcrumb to go back:
 * Customer > Unit > Tower. The page underneath never changes.
 */
export function EntityDrawer() {
  const { stack, popTo, close } = useDrawer();
  const base = useEntityBase();
  const results = useQueries({
    queries: stack.map((item) => ({
      queryKey: ["entity", base, item.type, item.id, "full"],
      queryFn: () => api<EntityView>(entityUrl(base, item.type, item.id)),
      staleTime: 5 * 60 * 1000,
    })),
  });
  if (!stack.length) return null;
  const top = results[results.length - 1];
  const view = top.data;

  const breadcrumb = stack.length > 1 && (
    <nav aria-label="Drawer path" className="mb-1.5 flex flex-wrap items-center gap-1 text-xs text-muted">
      {stack.map((item, i) => {
        const label = results[i].data?.title ?? item.type;
        return (
          <span key={`${item.type}:${item.id}:${i}`} className="flex items-center gap-1">
            {i > 0 && <ChevronRight size={12} />}
            {i < stack.length - 1
              ? <button type="button" onClick={() => popTo(i)} className="max-w-[160px] truncate underline decoration-line underline-offset-2 hover:text-ink">{label}</button>
              : <span className="max-w-[160px] truncate font-medium text-ink">{label}</span>}
          </span>
        );
      })}
    </nav>
  );

  return (
    <Sheet open onClose={close} title={view?.title ?? "Loading"} description={view?.subtitle} header={breadcrumb}>
      {top.isError && <ErrorState message={(top.error as Error).message} onRetry={() => top.refetch()} />}
      {!view && !top.isError && <SkeletonBlock rows={8} />}
      {view && (
        <>
          <div className="mb-5 flex flex-wrap items-center gap-3">
            <StatusPill {...view.status} />
            {view.attention && (
              <p className="flex items-center gap-1.5 text-[13px] font-medium text-risk">
                <CircleAlert size={15} strokeWidth={1.75} />{view.attention}
              </p>
            )}
          </div>
          <Tabs
            key={`${view.type}:${view.id}`}
            items={(view.tabs ?? []).map((tab) => ({
              key: tab.key,
              label: tab.label,
              content: <div className="space-y-5">{tab.blocks.map((block, i) => <BlockView key={i} block={block} />)}</div>,
            }))}
          />
        </>
      )}
    </Sheet>
  );
}
