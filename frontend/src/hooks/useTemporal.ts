import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { temporalApi } from "../services/temporalApi";

export function useTimelines(params?: { project_id?: string; search?: string }) {
  return useQuery({
    queryKey: ["timelines", params],
    queryFn: () => temporalApi.list(params),
  });
}

export function useTimeline(id: string | null) {
  return useQuery({
    queryKey: ["timeline", id],
    queryFn: () => temporalApi.get(id!),
    enabled: !!id,
  });
}

export function useCreateTimeline() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: temporalApi.create,
    onSuccess: () => qc.invalidateQueries({ queryKey: ["timelines"] }),
  });
}

export function useUpdateTimeline() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ id, ...payload }: { id: string } & Record<string, any>) => temporalApi.update(id, payload),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["timelines"] });
      qc.invalidateQueries({ queryKey: ["timeline"] });
    },
  });
}

export function useDeleteTimeline() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: temporalApi.delete,
    onSuccess: () => qc.invalidateQueries({ queryKey: ["timelines"] }),
  });
}

export function useDuplicateTimeline() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ id, name }: { id: string; name?: string }) => temporalApi.duplicate(id, name),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["timelines"] }),
  });
}

export function useToggleFavorite() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: temporalApi.toggleFavorite,
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["timelines"] });
      qc.invalidateQueries({ queryKey: ["timeline"] });
    },
  });
}

export function useTimelineEntries(timelineId: string | null, params?: { sensor?: string; date_from?: string; date_to?: string }) {
  return useQuery({
    queryKey: ["timelineEntries", timelineId, params],
    queryFn: () => temporalApi.getEntries(timelineId!, params),
    enabled: !!timelineId,
  });
}

export function useAddEntry() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ timelineId, ...payload }: { timelineId: string } & Record<string, any>) =>
      temporalApi.addEntry(timelineId, payload),
    onSuccess: (_data, variables) => {
      qc.invalidateQueries({ queryKey: ["timelineEntries", variables.timelineId] });
      qc.invalidateQueries({ queryKey: ["timeline", variables.timelineId] });
      qc.invalidateQueries({ queryKey: ["timelines"] });
    },
  });
}

export function useRemoveEntry() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ timelineId, entryId }: { timelineId: string; entryId: string }) =>
      temporalApi.removeEntry(timelineId, entryId),
    onSuccess: (_data, variables) => {
      qc.invalidateQueries({ queryKey: ["timelineEntries", variables.timelineId] });
      qc.invalidateQueries({ queryKey: ["timeline", variables.timelineId] });
      qc.invalidateQueries({ queryKey: ["timelines"] });
    },
  });
}

export function useTimelineSensors(timelineId: string | null) {
  return useQuery({
    queryKey: ["timelineSensors", timelineId],
    queryFn: () => temporalApi.getSensors(timelineId!),
    enabled: !!timelineId,
  });
}

export function useTimelineBookmarks(timelineId: string | null) {
  return useQuery({
    queryKey: ["timelineBookmarks", timelineId],
    queryFn: () => temporalApi.getBookmarks(timelineId!),
    enabled: !!timelineId,
  });
}

export function useAddBookmark() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ timelineId, ...payload }: { timelineId: string } & Record<string, any>) =>
      temporalApi.addBookmark(timelineId, payload),
    onSuccess: (_data, variables) => {
      qc.invalidateQueries({ queryKey: ["timelineBookmarks", variables.timelineId] });
    },
  });
}

export function useDeleteBookmark() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ timelineId, bookmarkId }: { timelineId: string; bookmarkId: string }) =>
      temporalApi.deleteBookmark(timelineId, bookmarkId),
    onSuccess: (_data, variables) => {
      qc.invalidateQueries({ queryKey: ["timelineBookmarks", variables.timelineId] });
    },
  });
}

export function useTimelineLogs(timelineId: string | null) {
  return useQuery({
    queryKey: ["timelineLogs", timelineId],
    queryFn: () => temporalApi.getLogs(timelineId!),
    enabled: !!timelineId,
  });
}

export function useTimelineStats() {
  return useQuery({
    queryKey: ["timelineStats"],
    queryFn: temporalApi.getStats,
  });
}

export function useCreateComparison() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ timelineId, ...payload }: { timelineId: string } & Record<string, any>) =>
      temporalApi.createComparison(timelineId, payload),
    onSuccess: (_data, variables) => {
      qc.invalidateQueries({ queryKey: ["timeline", variables.timelineId] });
    },
  });
}

export function useUpdateComparison() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ timelineId, sessionId, ...payload }: { timelineId: string; sessionId: string } & Record<string, any>) =>
      temporalApi.updateComparison(timelineId, sessionId, payload),
    onSuccess: (_data, variables) => {
      qc.invalidateQueries({ queryKey: ["timeline", variables.timelineId] });
    },
  });
}
