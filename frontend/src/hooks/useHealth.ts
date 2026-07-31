import { useQuery } from "@tanstack/react-query";
import { healthApi } from "../services/api";

export function useHealth() {
  return useQuery({
    queryKey: ["health"],
    queryFn: async () => {
      const response = await healthApi.getHealth();
      return response.data;
    },
    refetchInterval: 30000,
  });
}

export function useDetailedHealth() {
  return useQuery({
    queryKey: ["health", "detailed"],
    queryFn: async () => {
      const response = await healthApi.getDetailedHealth();
      return response.data;
    },
    refetchInterval: 60000,
  });
}
