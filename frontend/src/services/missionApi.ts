import axios from "axios";
import type { Mission, MissionActivity, MissionNote, MissionStats } from "../types/mission";

const api = axios.create({ baseURL: "/api/v1" });

export const missionApi = {
  list: async (params?: { status?: string; priority?: string; search?: string; offset?: number; limit?: number }) => {
    const { data } = await api.get("/missions", { params });
    return data as { missions: Mission[]; total: number };
  },

  get: async (id: string) => {
    const { data } = await api.get(`/missions/${id}`);
    return data as Mission;
  },

  create: async (payload: Partial<Mission>) => {
    const { data } = await api.post("/missions", payload);
    return data as Mission;
  },

  update: async (id: string, payload: Partial<Mission>) => {
    const { data } = await api.put(`/missions/${id}`, payload);
    return data as Mission;
  },

  delete: async (id: string) => {
    await api.delete(`/missions/${id}`);
  },

  archive: async (id: string) => {
    const { data } = await api.post(`/missions/${id}/archive`);
    return data as Mission;
  },

  toggleFavorite: async (id: string) => {
    const { data } = await api.post(`/missions/${id}/favorite`);
    return data as Mission;
  },

  addProject: async (missionId: string, projectId: string, notes?: string) => {
    const { data } = await api.post(`/missions/${missionId}/project`, { project_id: projectId, notes });
    return data;
  },

  removeProject: async (missionId: string, projectId: string) => {
    await api.delete(`/missions/${missionId}/project/${projectId}`);
  },

  getProjects: async (missionId: string) => {
    const { data } = await api.get(`/missions/${missionId}/projects`);
    return data;
  },

  getTimeline: async (missionId: string, limit?: number) => {
    const { data } = await api.get(`/missions/${missionId}/timeline`, { params: { limit } });
    return data as MissionActivity[];
  },

  getNotes: async (missionId: string) => {
    const { data } = await api.get(`/missions/${missionId}/notes`);
    return data as MissionNote[];
  },

  addNote: async (missionId: string, payload: { title?: string; content?: string; author?: string }) => {
    const { data } = await api.post(`/missions/${missionId}/notes`, payload);
    return data as MissionNote;
  },

  getStats: async () => {
    const { data } = await api.get("/missions/stats");
    return data as MissionStats;
  },
};
