import api from "./api";
import type {
  ImageRegistration,
  ControlPoint,
  RegistrationHistory,
  RegistrationMetrics,
  RegistrationConfig,
  RegistrationCreateRequest,
  ControlPointCreateRequest,
  ControlPointMoveRequest,
} from "../types/registration";

export const registrationApi = {
  getConfig: () =>
    api.get<RegistrationConfig>("/registrations/config"),

  create: (projectId: string, data: RegistrationCreateRequest) =>
    api.post<ImageRegistration>(
      `/registrations/project/${projectId}`,
      data
    ),

  list: (projectId: string, params?: { status?: string; favorite?: boolean }) =>
    api.get<ImageRegistration[]>(
      `/registrations/project/${projectId}`,
      { params }
    ),

  get: (registrationId: string) =>
    api.get<ImageRegistration>(`/registrations/${registrationId}`),

  run: (registrationId: string) =>
    api.post<ImageRegistration>(`/registrations/${registrationId}/run`),

  runManual: (registrationId: string, resampling?: string) =>
    api.post<ImageRegistration>(
      `/registrations/${registrationId}/run-manual`,
      null,
      { params: { resampling: resampling || "bilinear" } }
    ),

  delete: (registrationId: string) =>
    api.delete(`/registrations/${registrationId}`),

  toggleFavorite: (registrationId: string) =>
    api.patch<{ id: string; favorite: boolean }>(
      `/registrations/${registrationId}/favorite`
    ),

  listHistory: (registrationId: string) =>
    api.get<RegistrationHistory[]>(
      `/registrations/${registrationId}/history`
    ),

  listAllHistory: (projectId: string) =>
    api.get<RegistrationHistory[]>(
      `/registrations/project/${projectId}/history`
    ),

  listMetrics: (registrationId: string) =>
    api.get<RegistrationMetrics[]>(
      `/registrations/${registrationId}/metrics`
    ),

  listControlPoints: (registrationId: string) =>
    api.get<ControlPoint[]>(
      `/registrations/${registrationId}/control-points`
    ),

  createControlPoint: (
    registrationId: string,
    data: ControlPointCreateRequest
  ) =>
    api.post<ControlPoint>(
      `/registrations/${registrationId}/control-points`,
      data
    ),

  bulkCreateControlPoints: (
    registrationId: string,
    points: ControlPointCreateRequest[]
  ) =>
    api.post<ControlPoint[]>(
      `/registrations/${registrationId}/control-points/bulk`,
      { points }
    ),

  moveControlPoint: (
    registrationId: string,
    pointId: string,
    data: ControlPointMoveRequest
  ) =>
    api.patch<ControlPoint>(
      `/registrations/${registrationId}/control-points/${pointId}`,
      data
    ),

  deleteControlPoint: (registrationId: string, pointId: string) =>
    api.delete(
      `/registrations/${registrationId}/control-points/${pointId}`
    ),

  deleteAllControlPoints: (registrationId: string) =>
    api.delete(
      `/registrations/${registrationId}/control-points`
    ),
};
