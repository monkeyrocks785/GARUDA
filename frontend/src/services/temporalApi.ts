import axios from "axios";
import type {
  Timeline,
  TimelineEntry,
  ComparisonSession,
  TimelineBookmark,
  TimelineLog,
  TimelineStats,
} from "../types/temporal";

const api = axios.create({ baseURL: "/api/v1" });

export const temporalApi = {
  // Timelines
  list: async (params?: { project_id?: string; search?: string; offset?: number; limit?: number }) => {
    const { data } = await api.get("/timelines", { params });
    return data as { timelines: Timeline[]; total: number };
  },

  get: async (id: string) => {
    const { data } = await api.get(`/timelines/${id}`);
    return data as Timeline;
  },

  create: async (payload: Partial<Timeline>) => {
    const { data } = await api.post("/timelines", payload);
    return data as Timeline;
  },

  update: async (id: string, payload: Partial<Timeline>) => {
    const { data } = await api.put(`/timelines/${id}`, payload);
    return data as Timeline;
  },

  delete: async (id: string) => {
    await api.delete(`/timelines/${id}`);
  },

  duplicate: async (id: string, name?: string) => {
    const params = name ? { name } : {};
    const { data } = await api.post(`/timelines/${id}/duplicate`, null, { params });
    return data as Timeline;
  },

  toggleFavorite: async (id: string) => {
    const { data } = await api.post(`/timelines/${id}/favorite`);
    return data as Timeline;
  },

  // Entries
  getEntries: async (timelineId: string, params?: { sensor?: string; date_from?: string; date_to?: string }) => {
    const { data } = await api.get(`/timelines/${timelineId}/entries`, { params });
    return data as TimelineEntry[];
  },

  addEntry: async (timelineId: string, payload: Partial<TimelineEntry>) => {
    const { data } = await api.post(`/timelines/${timelineId}/entries`, payload);
    return data as TimelineEntry;
  },

  updateEntry: async (timelineId: string, entryId: string, payload: Partial<TimelineEntry>) => {
    const { data } = await api.put(`/timelines/${timelineId}/entries/${entryId}`, payload);
    return data as TimelineEntry;
  },

  removeEntry: async (timelineId: string, entryId: string) => {
    await api.delete(`/timelines/${timelineId}/entries/${entryId}`);
  },

  reorderEntries: async (timelineId: string, entryIds: string[]) => {
    await api.post(`/timelines/${timelineId}/entries/reorder`, { entry_ids: entryIds });
  },

  getSensors: async (timelineId: string) => {
    const { data } = await api.get(`/timelines/${timelineId}/sensors`);
    return data as { sensors: string[] };
  },

  // Comparisons
  createComparison: async (timelineId: string, payload: Partial<ComparisonSession>) => {
    const { data } = await api.post(`/timelines/${timelineId}/comparison`, payload);
    return data as ComparisonSession;
  },

  getComparison: async (timelineId: string, sessionId: string) => {
    const { data } = await api.get(`/timelines/${timelineId}/comparison/${sessionId}`);
    return data as ComparisonSession;
  },

  updateComparison: async (timelineId: string, sessionId: string, payload: Partial<ComparisonSession>) => {
    const { data } = await api.put(`/timelines/${timelineId}/comparison/${sessionId}`, payload);
    return data as ComparisonSession;
  },

  // Bookmarks
  getBookmarks: async (timelineId: string) => {
    const { data } = await api.get(`/timelines/${timelineId}/bookmarks`);
    return data as TimelineBookmark[];
  },

  addBookmark: async (timelineId: string, payload: Partial<TimelineBookmark>) => {
    const { data } = await api.post(`/timelines/${timelineId}/bookmarks`, payload);
    return data as TimelineBookmark;
  },

  deleteBookmark: async (timelineId: string, bookmarkId: string) => {
    await api.delete(`/timelines/${timelineId}/bookmarks/${bookmarkId}`);
  },

  // Logs
  getLogs: async (timelineId: string, limit?: number) => {
    const { data } = await api.get(`/timelines/${timelineId}/logs`, { params: { limit } });
    return data as TimelineLog[];
  },

  // Stats
  getStats: async () => {
    const { data } = await api.get("/timelines/stats");
    return data as TimelineStats;
  },
};
