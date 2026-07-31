import api from "./api";
import type { WorkspaceState, WorkspaceStateUpdate } from "../types/workspace";

export const workspaceApi = {
  get: (projectId: string) =>
    api.get<WorkspaceState>(`/projects/${projectId}/workspace`),

  update: (projectId: string, data: WorkspaceStateUpdate) =>
    api.put<WorkspaceState>(`/projects/${projectId}/workspace`, data),
};
