import api from "./api";
import type {
  RegisteredModel,
  ModelRegisterRequest,
  AnalysisJob,
  AnalysisJobCreateRequest,
  Detection,
  ReviewRequest,
  BatchReviewRequest,
  IntelligenceConfig,
  ReviewStats,
  AnalysisHistoryEntry,
} from "../types/intelligence";

export const intelligenceApi = {
  // ── Config ──────────────────────────────────────────────────────────
  getConfig: () =>
    api.get<IntelligenceConfig>("/intelligence/models/config"),

  // ── Models ──────────────────────────────────────────────────────────
  listModels: (params?: { task?: string; status?: string; loaded_only?: boolean }) =>
    api.get<RegisteredModel[]>("/intelligence/models", { params }),

  getModel: (modelId: string) =>
    api.get<RegisteredModel>(`/intelligence/models/${modelId}`),

  registerModel: (data: ModelRegisterRequest) =>
    api.post<RegisteredModel>("/intelligence/models", data),

  loadModel: (modelId: string) =>
    api.post<RegisteredModel>(`/intelligence/models/${modelId}/load`),

  unloadModel: (modelId: string) =>
    api.post<RegisteredModel>(`/intelligence/models/${modelId}/unload`),

  deleteModel: (modelId: string) =>
    api.delete(`/intelligence/models/${modelId}`),

  toggleModelFavorite: (modelId: string) =>
    api.patch<{ id: string; favorite: boolean }>(`/intelligence/models/${modelId}/favorite`),

  // ── Analysis Jobs ──────────────────────────────────────────────────
  createJob: (projectId: string, data: AnalysisJobCreateRequest) =>
    api.post<AnalysisJob>(`/intelligence/project/${projectId}/jobs`, data),

  listJobs: (projectId: string, params?: { status?: string; task_type?: string }) =>
    api.get<AnalysisJob[]>(`/intelligence/project/${projectId}/jobs`, { params }),

  getJob: (jobId: string) =>
    api.get<AnalysisJob>(`/intelligence/jobs/${jobId}`),

  runJob: (jobId: string) =>
    api.post<AnalysisJob>(`/intelligence/jobs/${jobId}/run`),

  cancelJob: (jobId: string) =>
    api.post<AnalysisJob>(`/intelligence/jobs/${jobId}/cancel`),

  deleteJob: (jobId: string) =>
    api.delete(`/intelligence/jobs/${jobId}`),

  getJobHistory: (jobId: string) =>
    api.get<AnalysisHistoryEntry[]>(`/intelligence/jobs/${jobId}/history`),

  // ── Detections ──────────────────────────────────────────────────────
  listJobDetections: (
    jobId: string,
    params?: { class_name?: string; review_status?: string; min_confidence?: number }
  ) =>
    api.get<Detection[]>(`/intelligence/jobs/${jobId}/detections`, { params }),

  getJobDetectionsGeoJSON: (
    jobId: string,
    params?: { class_name?: string; review_status?: string }
  ) =>
    api.get<unknown>(`/intelligence/jobs/${jobId}/detections/geojson`, { params }),

  listProjectDetections: (
    projectId: string,
    params?: { class_name?: string; review_status?: string }
  ) =>
    api.get<Detection[]>(`/intelligence/project/${projectId}/detections`, { params }),

  getProjectDetectionsGeoJSON: (
    projectId: string,
    params?: { class_name?: string; review_status?: string }
  ) =>
    api.get<unknown>(`/intelligence/project/${projectId}/detections/geojson`, { params }),

  getJobReviewStats: (jobId: string) =>
    api.get<ReviewStats>(`/intelligence/jobs/${jobId}/review-stats`),

  getProjectReviewStats: (projectId: string) =>
    api.get<ReviewStats>(`/intelligence/project/${projectId}/review-stats`),

  // ── Reviews ─────────────────────────────────────────────────────────
  reviewDetection: (detectionId: string, data: ReviewRequest) =>
    api.patch<Detection>(`/intelligence/detections/${detectionId}/review`, data),

  batchReview: (data: BatchReviewRequest) =>
    api.post<Detection[]>("/intelligence/detections/batch-review", data),

  addNotes: (detectionId: string, notes: string) =>
    api.patch<Detection>(`/intelligence/detections/${detectionId}/notes`, { notes }),

  editGeometry: (detectionId: string, geometry: Record<string, unknown>) =>
    api.patch<Detection>(`/intelligence/detections/${detectionId}/geometry`, { geometry }),
};
