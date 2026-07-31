import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { workspaceApi } from "../services/workspaceApi";
import type { WorkspaceStateUpdate } from "../types/workspace";

export function useWorkspaceState(projectId: string | null) {
  return useQuery({
    queryKey: ["workspace", projectId],
    queryFn: async () => {
      if (!projectId) return null;
      const response = await workspaceApi.get(projectId);
      return response.data;
    },
    enabled: !!projectId,
  });
}

export function useUpdateWorkspace() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({
      projectId,
      data,
    }: {
      projectId: string;
      data: WorkspaceStateUpdate;
    }) => {
      const response = await workspaceApi.update(projectId, data);
      return response.data;
    },
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({
        queryKey: ["workspace", variables.projectId],
      });
    },
  });
}
