import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { pipelineApi } from "../services/pipelineApi";
import { usePipelineStore } from "../store/usePipelineStore";

export function usePipelines() {
  const { projectId } = usePipelineStore();
  return useQuery({
    queryKey: ["pipelines", projectId],
    queryFn: () => pipelineApi.list({ project_id: projectId || undefined }).then((r) => r.data),
  });
}

export function usePipeline(id: string | null) {
  return useQuery({
    queryKey: ["pipeline", id],
    queryFn: () => pipelineApi.get(id!).then((r) => r.data),
    enabled: !!id,
  });
}

export function usePipelineNodes(id: string | null) {
  return useQuery({
    queryKey: ["pipelineNodes", id],
    queryFn: () => pipelineApi.getNodes(id!).then((r) => r.data),
    enabled: !!id,
  });
}

export function usePipelineHistory(id: string | null) {
  return useQuery({
    queryKey: ["pipelineHistory", id],
    queryFn: () => pipelineApi.getHistory(id!).then((r) => r.data),
    enabled: !!id,
  });
}

export function usePipelineLogs(id: string | null) {
  return useQuery({
    queryKey: ["pipelineLogs", id],
    queryFn: () => pipelineApi.getLogs(id!).then((r) => r.data),
    enabled: !!id,
  });
}

export function usePipelineStats() {
  const { projectId } = usePipelineStore();
  return useQuery({
    queryKey: ["pipelineStats", projectId],
    queryFn: () => pipelineApi.getStats(projectId || undefined).then((r) => r.data),
  });
}

export function useQueueStatus() {
  return useQuery({
    queryKey: ["queueStatus"],
    queryFn: () => pipelineApi.getQueueStatus().then((r) => r.data),
    refetchInterval: 3000,
  });
}

export function useQueueEntries() {
  return useQuery({
    queryKey: ["queueEntries"],
    queryFn: () => pipelineApi.listQueue().then((r) => r.data),
    refetchInterval: 3000,
  });
}

export function useNodeTypes() {
  return useQuery({
    queryKey: ["nodeTypes"],
    queryFn: () => pipelineApi.getNodeTypes().then((r) => r.data),
  });
}

export function useCreatePipeline() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (data: { name: string; project_id?: string; description?: string; nodes?: any[] }) =>
      pipelineApi.create(data).then((r) => r.data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["pipelines"] });
      qc.invalidateQueries({ queryKey: ["pipelineStats"] });
    },
  });
}

export function useDeletePipeline() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => pipelineApi.delete(id).then((r) => r.data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["pipelines"] });
      qc.invalidateQueries({ queryKey: ["pipelineStats"] });
    },
  });
}

export function useStartPipeline() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => pipelineApi.start(id).then((r) => r.data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["pipelines"] });
      qc.invalidateQueries({ queryKey: ["pipelineStats"] });
    },
  });
}

export function usePausePipeline() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => pipelineApi.pause(id).then((r) => r.data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["pipelines"] });
    },
  });
}

export function useResumePipeline() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => pipelineApi.resume(id).then((r) => r.data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["pipelines"] });
    },
  });
}

export function useCancelPipeline() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => pipelineApi.cancel(id).then((r) => r.data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["pipelines"] });
      qc.invalidateQueries({ queryKey: ["pipelineStats"] });
    },
  });
}

export function useRetryPipeline() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => pipelineApi.retry(id).then((r) => r.data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["pipelines"] });
      qc.invalidateQueries({ queryKey: ["pipelineStats"] });
    },
  });
}
