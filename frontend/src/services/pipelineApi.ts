import axios from "axios";
import type {
  Pipeline, PipelineNode, PipelineHistory, PipelineLog,
  QueueEntry, QueueStatus, NodeType, PipelineStats,
} from "../types/pipeline";

const api = axios.create({
  baseURL: "/api/v1",
  headers: { "Content-Type": "application/json" },
});

api.interceptors.response.use(
  (response) => response,
  (error) => {
    console.error("API Error:", error.response?.data || error.message);
    return Promise.reject(error);
  }
);

export const pipelineApi = {
  list: (params: { project_id?: string; status?: string; offset?: number; limit?: number } = {}) =>
    api.get<{ pipelines: Pipeline[]; total: number; offset: number; limit: number }>("/pipelines", { params }),

  get: (id: string) => api.get<Pipeline>(`/pipelines/${id}`),

  create: (data: { name: string; project_id?: string; description?: string; owner?: string; nodes?: any[] }) =>
    api.post<Pipeline>("/pipelines", data),

  delete: (id: string) => api.delete(`/pipelines/${id}`),

  start: (id: string) => api.post(`/pipelines/${id}/start`),

  pause: (id: string) => api.post(`/pipelines/${id}/pause`),

  resume: (id: string) => api.post(`/pipelines/${id}/resume`),

  cancel: (id: string) => api.post(`/pipelines/${id}/cancel`),

  retry: (id: string) => api.post(`/pipelines/${id}/retry`),

  enqueue: (id: string, priority: number = 0) =>
    api.post(`/pipelines/${id}/enqueue?priority=${priority}`),

  dequeue: (id: string) => api.delete(`/pipelines/${id}/queue`),

  getNodes: (id: string) => api.get<PipelineNode[]>(`/pipelines/${id}/nodes`),

  getHistory: (id: string, limit: number = 50) =>
    api.get<PipelineHistory[]>(`/pipelines/${id}/history`, { params: { limit } }),

  getLogs: (id: string, params: { node_id?: string; level?: string; limit?: number } = {}) =>
    api.get<PipelineLog[]>(`/pipelines/${id}/logs`, { params }),

  getStats: (projectId?: string) =>
    api.get<PipelineStats>("/pipelines/stats", { params: { project_id: projectId } }),

  getQueueStatus: () => api.get<QueueStatus>("/pipelines/queue/status"),

  listQueue: () => api.get<QueueEntry[]>("/pipelines/queue"),

  getNodeTypes: () => api.get<NodeType[]>("/pipelines/node-types"),
};
