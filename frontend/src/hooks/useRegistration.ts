import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { registrationApi } from "../services/registrationApi";
import type {
  RegistrationCreateRequest,
  ControlPointCreateRequest,
  ControlPointMoveRequest,
} from "../types/registration";

export function useRegistrationConfig() {
  return useQuery({
    queryKey: ["registrationConfig"],
    queryFn: async () => {
      const response = await registrationApi.getConfig();
      return response.data;
    },
  });
}

export function useRegistrationList(
  projectId: string | null,
  params?: { status?: string; favorite?: boolean }
) {
  return useQuery({
    queryKey: ["registrations", projectId, params],
    queryFn: async () => {
      if (!projectId) return [];
      const response = await registrationApi.list(projectId, params);
      return response.data;
    },
    enabled: !!projectId,
  });
}

export function useRegistration(registrationId: string | null) {
  return useQuery({
    queryKey: ["registration", registrationId],
    queryFn: async () => {
      if (!registrationId) return null;
      const response = await registrationApi.get(registrationId);
      return response.data;
    },
    enabled: !!registrationId,
  });
}

export function useCreateRegistration() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({
      projectId,
      data,
    }: {
      projectId: string;
      data: RegistrationCreateRequest;
    }) => {
      const response = await registrationApi.create(projectId, data);
      return response.data;
    },
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({
        queryKey: ["registrations", variables.projectId],
      });
    },
  });
}

export function useRunRegistration() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (registrationId: string) => {
      const response = await registrationApi.run(registrationId);
      return response.data;
    },
    onSuccess: (data) => {
      queryClient.invalidateQueries({
        queryKey: ["registrations", data.project_id],
      });
      queryClient.invalidateQueries({
        queryKey: ["registration", data.id],
      });
    },
  });
}

export function useRunManualRegistration() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({
      registrationId,
      resampling,
    }: {
      registrationId: string;
      resampling?: string;
    }) => {
      const response = await registrationApi.runManual(
        registrationId,
        resampling
      );
      return response.data;
    },
    onSuccess: (data) => {
      queryClient.invalidateQueries({
        queryKey: ["registrations", data.project_id],
      });
      queryClient.invalidateQueries({
        queryKey: ["registration", data.id],
      });
    },
  });
}

export function useDeleteRegistration() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({
      registrationId,
    }: {
      registrationId: string;
      projectId: string;
    }) => {
      await registrationApi.delete(registrationId);
    },
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({
        queryKey: ["registrations", variables.projectId],
      });
    },
  });
}

export function useToggleFavorite() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (registrationId: string) => {
      const response = await registrationApi.toggleFavorite(registrationId);
      return response.data;
    },
    onSuccess: (data) => {
      queryClient.invalidateQueries({
        queryKey: ["registrations"],
      });
      queryClient.invalidateQueries({
        queryKey: ["registration", data.id],
      });
    },
  });
}

export function useRegistrationHistory(registrationId: string | null) {
  return useQuery({
    queryKey: ["registrationHistory", registrationId],
    queryFn: async () => {
      if (!registrationId) return [];
      const response = await registrationApi.listHistory(registrationId);
      return response.data;
    },
    enabled: !!registrationId,
  });
}

export function useRegistrationMetrics(registrationId: string | null) {
  return useQuery({
    queryKey: ["registrationMetrics", registrationId],
    queryFn: async () => {
      if (!registrationId) return [];
      const response = await registrationApi.listMetrics(registrationId);
      return response.data;
    },
    enabled: !!registrationId,
  });
}

export function useControlPoints(registrationId: string | null) {
  return useQuery({
    queryKey: ["controlPoints", registrationId],
    queryFn: async () => {
      if (!registrationId) return [];
      const response = await registrationApi.listControlPoints(registrationId);
      return response.data;
    },
    enabled: !!registrationId,
  });
}

export function useCreateControlPoint() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({
      registrationId,
      data,
    }: {
      registrationId: string;
      data: ControlPointCreateRequest;
    }) => {
      const response = await registrationApi.createControlPoint(
        registrationId,
        data
      );
      return response.data;
    },
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({
        queryKey: ["controlPoints", variables.registrationId],
      });
    },
  });
}

export function useBulkCreateControlPoints() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({
      registrationId,
      points,
    }: {
      registrationId: string;
      points: ControlPointCreateRequest[];
    }) => {
      const response = await registrationApi.bulkCreateControlPoints(
        registrationId,
        points
      );
      return response.data;
    },
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({
        queryKey: ["controlPoints", variables.registrationId],
      });
    },
  });
}

export function useMoveControlPoint() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({
      registrationId,
      pointId,
      data,
    }: {
      registrationId: string;
      pointId: string;
      data: ControlPointMoveRequest;
    }) => {
      const response = await registrationApi.moveControlPoint(
        registrationId,
        pointId,
        data
      );
      return response.data;
    },
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({
        queryKey: ["controlPoints", variables.registrationId],
      });
    },
  });
}

export function useDeleteControlPoint() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({
      registrationId,
      pointId,
    }: {
      registrationId: string;
      pointId: string;
    }) => {
      await registrationApi.deleteControlPoint(registrationId, pointId);
    },
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({
        queryKey: ["controlPoints", variables.registrationId],
      });
    },
  });
}

export function useDeleteAllControlPoints() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (registrationId: string) => {
      await registrationApi.deleteAllControlPoints(registrationId);
    },
    onSuccess: (_, registrationId) => {
      queryClient.invalidateQueries({
        queryKey: ["controlPoints", registrationId],
      });
    },
  });
}
