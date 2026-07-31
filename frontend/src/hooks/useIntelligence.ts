import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { intelligenceApi } from "../services/intelligenceApi";
import type {
  ModelRegisterRequest,
  AnalysisJobCreateRequest,
  ReviewRequest,
  BatchReviewRequest,
} from "../types/intelligence";

// ── Config ──────────────────────────────────────────────────────────────────

export function useIntelligenceConfig() {
  return useQuery({
    queryKey: ["intelligenceConfig"],
    queryFn: async () => {
      const response = await intelligenceApi.getConfig();
      return response.data;
    },
  });
}

// ── Models ──────────────────────────────────────────────────────────────────

export function useModelList(params?: { task?: string; status?: string; loaded_only?: boolean }) {
  return useQuery({
    queryKey: ["intelligenceModels", params],
    queryFn: async () => {
      const response = await intelligenceApi.listModels(params);
      return response.data;
    },
  });
}

export function useModel(modelId: string | null) {
  return useQuery({
    queryKey: ["intelligenceModel", modelId],
    queryFn: async () => {
      if (!modelId) return null;
      const response = await intelligenceApi.getModel(modelId);
      return response.data;
    },
    enabled: !!modelId,
  });
}

export function useRegisterModel() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (data: ModelRegisterRequest) => {
      const response = await intelligenceApi.registerModel(data);
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["intelligenceModels"] });
    },
  });
}

export function useLoadModel() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (modelId: string) => {
      const response = await intelligenceApi.loadModel(modelId);
      return response.data;
    },
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ["intelligenceModels"] });
      queryClient.invalidateQueries({ queryKey: ["intelligenceModel", data.id] });
    },
  });
}

export function useUnloadModel() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (modelId: string) => {
      const response = await intelligenceApi.unloadModel(modelId);
      return response.data;
    },
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ["intelligenceModels"] });
      queryClient.invalidateQueries({ queryKey: ["intelligenceModel", data.id] });
    },
  });
}

export function useDeleteModel() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (modelId: string) => {
      await intelligenceApi.deleteModel(modelId);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["intelligenceModels"] });
    },
  });
}

export function useToggleModelFavorite() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (modelId: string) => {
      const response = await intelligenceApi.toggleModelFavorite(modelId);
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["intelligenceModels"] });
    },
  });
}

// ── Analysis Jobs ───────────────────────────────────────────────────────────

export function useAnalysisJobList(
  projectId: string | null,
  params?: { status?: string; task_type?: string }
) {
  return useQuery({
    queryKey: ["analysisJobs", projectId, params],
    queryFn: async () => {
      if (!projectId) return [];
      const response = await intelligenceApi.listJobs(projectId, params);
      return response.data;
    },
    enabled: !!projectId,
  });
}

export function useAnalysisJob(jobId: string | null) {
  return useQuery({
    queryKey: ["analysisJob", jobId],
    queryFn: async () => {
      if (!jobId) return null;
      const response = await intelligenceApi.getJob(jobId);
      return response.data;
    },
    enabled: !!jobId,
    refetchInterval: (query) => {
      const job = query.state.data;
      if (job && (job.status === "running" || job.status === "pending")) {
        return 2000;
      }
      return false;
    },
  });
}

export function useCreateAnalysisJob() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({
      projectId,
      data,
    }: {
      projectId: string;
      data: AnalysisJobCreateRequest;
    }) => {
      const response = await intelligenceApi.createJob(projectId, data);
      return response.data;
    },
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({
        queryKey: ["analysisJobs", variables.projectId],
      });
    },
  });
}

export function useRunAnalysisJob() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (jobId: string) => {
      const response = await intelligenceApi.runJob(jobId);
      return response.data;
    },
    onSuccess: (data) => {
      queryClient.invalidateQueries({
        queryKey: ["analysisJobs", data.project_id],
      });
      queryClient.invalidateQueries({
        queryKey: ["analysisJob", data.id],
      });
    },
  });
}

export function useCancelAnalysisJob() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (jobId: string) => {
      const response = await intelligenceApi.cancelJob(jobId);
      return response.data;
    },
    onSuccess: (data) => {
      queryClient.invalidateQueries({
        queryKey: ["analysisJobs", data.project_id],
      });
      queryClient.invalidateQueries({
        queryKey: ["analysisJob", data.id],
      });
    },
  });
}

export function useDeleteAnalysisJob() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({
      jobId,
      projectId: _projectId,
    }: {
      jobId: string;
      projectId: string;
    }) => {
      await intelligenceApi.deleteJob(jobId);
    },
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({
        queryKey: ["analysisJobs", variables.projectId],
      });
    },
  });
}

export function useJobHistory(jobId: string | null) {
  return useQuery({
    queryKey: ["jobHistory", jobId],
    queryFn: async () => {
      if (!jobId) return [];
      const response = await intelligenceApi.getJobHistory(jobId);
      return response.data;
    },
    enabled: !!jobId,
  });
}

// ── Detections ──────────────────────────────────────────────────────────────

export function useJobDetections(
  jobId: string | null,
  params?: { class_name?: string; review_status?: string; min_confidence?: number }
) {
  return useQuery({
    queryKey: ["jobDetections", jobId, params],
    queryFn: async () => {
      if (!jobId) return [];
      const response = await intelligenceApi.listJobDetections(jobId, params);
      return response.data;
    },
    enabled: !!jobId,
  });
}

export function useJobDetectionsGeoJSON(
  jobId: string | null,
  params?: { class_name?: string; review_status?: string }
) {
  return useQuery({
    queryKey: ["jobDetectionsGeoJSON", jobId, params],
    queryFn: async () => {
      if (!jobId) return null;
      const response = await intelligenceApi.getJobDetectionsGeoJSON(jobId, params);
      return response.data;
    },
    enabled: !!jobId,
  });
}

export function useProjectDetections(
  projectId: string | null,
  params?: { class_name?: string; review_status?: string }
) {
  return useQuery({
    queryKey: ["projectDetections", projectId, params],
    queryFn: async () => {
      if (!projectId) return [];
      const response = await intelligenceApi.listProjectDetections(projectId, params);
      return response.data;
    },
    enabled: !!projectId,
  });
}

export function useJobReviewStats(jobId: string | null) {
  return useQuery({
    queryKey: ["jobReviewStats", jobId],
    queryFn: async () => {
      if (!jobId) return null;
      const response = await intelligenceApi.getJobReviewStats(jobId);
      return response.data;
    },
    enabled: !!jobId,
  });
}

export function useProjectReviewStats(projectId: string | null) {
  return useQuery({
    queryKey: ["projectReviewStats", projectId],
    queryFn: async () => {
      if (!projectId) return null;
      const response = await intelligenceApi.getProjectReviewStats(projectId);
      return response.data;
    },
    enabled: !!projectId,
  });
}

// ── Reviews ─────────────────────────────────────────────────────────────────

export function useReviewDetection() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({
      detectionId,
      data,
    }: {
      detectionId: string;
      data: ReviewRequest;
    }) => {
      const response = await intelligenceApi.reviewDetection(detectionId, data);
      return response.data;
    },
    onSuccess: (data) => {
      queryClient.invalidateQueries({
        queryKey: ["jobDetections", data.job_id],
      });
      queryClient.invalidateQueries({
        queryKey: ["jobReviewStats"],
      });
      queryClient.invalidateQueries({
        queryKey: ["projectDetections", data.project_id],
      });
    },
  });
}

export function useBatchReview() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (data: BatchReviewRequest) => {
      const response = await intelligenceApi.batchReview(data);
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["jobDetections"] });
      queryClient.invalidateQueries({ queryKey: ["jobReviewStats"] });
      queryClient.invalidateQueries({ queryKey: ["projectDetections"] });
      queryClient.invalidateQueries({ queryKey: ["projectReviewStats"] });
    },
  });
}

export function useAddDetectionNotes() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({
      detectionId,
      notes,
    }: {
      detectionId: string;
      notes: string;
    }) => {
      const response = await intelligenceApi.addNotes(detectionId, notes);
      return response.data;
    },
    onSuccess: (data) => {
      queryClient.invalidateQueries({
        queryKey: ["jobDetections", data.job_id],
      });
    },
  });
}

export function useEditDetectionGeometry() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({
      detectionId,
      geometry,
    }: {
      detectionId: string;
      geometry: Record<string, unknown>;
    }) => {
      const response = await intelligenceApi.editGeometry(detectionId, geometry);
      return response.data;
    },
    onSuccess: (data) => {
      queryClient.invalidateQueries({
        queryKey: ["jobDetections", data.job_id],
      });
    },
  });
}
