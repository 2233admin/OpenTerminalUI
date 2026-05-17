import { api } from "./base";
import type {
  JournalEntry,
  JournalStats,
  JournalEquityPoint,
  JournalCalendarDay,
} from "../types";
import type {
  JournalEntryPayload,
  JournalEntryUpdatePayload,
  JournalListFilters,
} from "./types";

export async function fetchJournalEntries(params?: JournalListFilters & { limit?: number; offset?: number }): Promise<JournalEntry[]> {
  const { data } = await api.get<{ items: JournalEntry[] }>("/journal/entries", { params });
  return Array.isArray(data?.items) ? data.items : [];
}

export async function createJournalEntry(payload: JournalEntryPayload | Partial<JournalEntry>): Promise<JournalEntry> {
  const { data } = await api.post<JournalEntry>("/journal/entries", payload);
  return data;
}

export async function updateJournalEntry(id: string | number, payload: JournalEntryUpdatePayload | Partial<JournalEntry>): Promise<JournalEntry> {
  const { data } = await api.put<JournalEntry>(`/journal/entries/${encodeURIComponent(id)}`, payload);
  return data;
}

export async function deleteJournalEntry(id: string | number): Promise<void> {
  await api.delete(`/journal/entries/${encodeURIComponent(id)}`);
}

export async function fetchJournalStats(): Promise<JournalStats> {
  const { data } = await api.get<JournalStats>("/journal/stats");
  return data;
}

export async function fetchJournalEquityCurve(): Promise<JournalEquityPoint[]> {
  const { data } = await api.get<{ items: JournalEquityPoint[] }>("/journal/equity-curve");
  return Array.isArray(data?.items) ? data.items : [];
}

export async function fetchJournalCalendar(month?: number, year?: number): Promise<JournalCalendarDay[]> {
  const { data } = await api.get<{ items: JournalCalendarDay[] }>("/journal/calendar", { params: { month, year } });
  return Array.isArray(data?.items) ? data.items : [];
}
