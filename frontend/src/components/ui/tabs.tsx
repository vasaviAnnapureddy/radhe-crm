import { Tabs as Radix } from "radix-ui";
import type { ReactNode } from "react";

export interface TabItem { key: string; label: string; content: ReactNode }

/** Underlined tabs. Extra content lives in tabs so the page above the fold stays calm. */
export function Tabs({ items, value, onChange }: { items: TabItem[]; value?: string; onChange?: (key: string) => void }) {
  if (!items.length) return null;
  return (
    <Radix.Root defaultValue={items[0].key} value={value} onValueChange={onChange}>
      <Radix.List className="mb-5 flex gap-6 overflow-x-auto border-b border-line">
        {items.map((item) => (
          <Radix.Trigger
            key={item.key}
            value={item.key}
            className="-mb-px whitespace-nowrap border-b-2 border-transparent pb-2.5 text-sm font-medium text-muted transition-colors duration-150 hover:text-ink data-[state=active]:border-primary data-[state=active]:text-ink"
          >
            {item.label}
          </Radix.Trigger>
        ))}
      </Radix.List>
      {items.map((item) => (
        <Radix.Content key={item.key} value={item.key} className="focus:outline-none">
          {item.content}
        </Radix.Content>
      ))}
    </Radix.Root>
  );
}
