import { useMemo } from "react";
import type { ChatHistoryItem } from "../types/api";

export type HistoryGroupLabel = "TODAY" | "YESTERDAY" | "LAST WEEK" | "OLDER";

export interface GroupedHistory {
  label: HistoryGroupLabel;
  items: ChatHistoryItem[];
}

function startOfDay(date: Date): Date {
  return new Date(date.getFullYear(), date.getMonth(), date.getDate());
}

export function groupHistoryByDate(items: ChatHistoryItem[]): GroupedHistory[] {
  const now = new Date();
  const today = startOfDay(now).getTime();
  const yesterday = today - 86_400_000;
  const lastWeek = today - 7 * 86_400_000;

  const buckets: Record<HistoryGroupLabel, ChatHistoryItem[]> = {
    TODAY: [],
    YESTERDAY: [],
    "LAST WEEK": [],
    OLDER: [],
  };

  for (const item of items) {
    const timestamp = startOfDay(new Date(item.lastActive)).getTime();
    if (timestamp >= today) buckets.TODAY.push(item);
    else if (timestamp >= yesterday) buckets.YESTERDAY.push(item);
    else if (timestamp >= lastWeek) buckets["LAST WEEK"].push(item);
    else buckets.OLDER.push(item);
  }

  return (Object.entries(buckets) as [HistoryGroupLabel, ChatHistoryItem[]][])
    .filter(([, groupItems]) => groupItems.length > 0)
    .map(([label, groupItems]) => ({ label, items: groupItems }));
}

export function useGroupedHistory(items: ChatHistoryItem[]): GroupedHistory[] {
  return useMemo(() => groupHistoryByDate(items), [items]);
}
