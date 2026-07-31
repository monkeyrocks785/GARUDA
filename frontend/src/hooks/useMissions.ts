import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { missionApi } from "../services/missionApi";

export function useMissions(params?: { status?: string; priority?: string; search?: string }) {
  return useQuery({
    queryKey: ["missions", params],
    queryFn: () => missionApi.list(params),
  });
}

export function useMission(id: string | null) {
  return useQuery({
    queryKey: ["mission", id],
    queryFn: () => missionApi.get(id!),
    enabled: !!id,
  });
}

export function useCreateMission() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: missionApi.create,
    onSuccess: () => qc.invalidateQueries({ queryKey: ["missions"] }),
  });
}

export function useUpdateMission() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ id, ...payload }: { id: string } & Record<string, any>) => missionApi.update(id, payload),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["missions"] });
      qc.invalidateQueries({ queryKey: ["mission"] });
    },
  });
}

export function useDeleteMission() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: missionApi.delete,
    onSuccess: () => qc.invalidateQueries({ queryKey: ["missions"] }),
  });
}

export function useArchiveMission() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: missionApi.archive,
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["missions"] });
      qc.invalidateQueries({ queryKey: ["mission"] });
    },
  });
}

export function useToggleFavorite() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: missionApi.toggleFavorite,
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["missions"] });
      qc.invalidateQueries({ queryKey: ["mission"] });
    },
  });
}

export function useMissionTimeline(missionId: string | null) {
  return useQuery({
    queryKey: ["missionTimeline", missionId],
    queryFn: () => missionApi.getTimeline(missionId!),
    enabled: !!missionId,
  });
}

export function useMissionNotes(missionId: string | null) {
  return useQuery({
    queryKey: ["missionNotes", missionId],
    queryFn: () => missionApi.getNotes(missionId!),
    enabled: !!missionId,
  });
}

export function useAddMissionNote() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ missionId, ...payload }: { missionId: string; title?: string; content?: string; author?: string }) =>
      missionApi.addNote(missionId, payload),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["missionNotes"] }),
  });
}

export function useMissionProjects(missionId: string | null) {
  return useQuery({
    queryKey: ["missionProjects", missionId],
    queryFn: () => missionApi.getProjects(missionId!),
    enabled: !!missionId,
  });
}

export function useAddMissionProject() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ missionId, projectId, notes }: { missionId: string; projectId: string; notes?: string }) =>
      missionApi.addProject(missionId, projectId, notes),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["missionProjects"] }),
  });
}

export function useRemoveMissionProject() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ missionId, projectId }: { missionId: string; projectId: string }) =>
      missionApi.removeProject(missionId, projectId),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["missionProjects"] }),
  });
}

export function useMissionStats() {
  return useQuery({
    queryKey: ["missionStats"],
    queryFn: missionApi.getStats,
  });
}
