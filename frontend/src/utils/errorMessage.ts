import type { AxiosError } from "axios";

export function getErrorMessage(error: unknown, fallback = "An unexpected error occurred"): string {
  if (!error) return fallback;

  if (typeof error === "object" && "response" in error) {
    const axiosErr = error as AxiosError<{ detail?: string; message?: string }>;
    const status = axiosErr.response?.status;
    const data = axiosErr.response?.data;

    if (data?.detail) return String(data.detail);
    if (data?.message) return String(data.message);

    if (status === 400) return "The request was invalid. Please check your input and try again.";
    if (status === 401) return "Your session has expired. Please sign in again.";
    if (status === 403) return "You do not have permission to perform this action.";
    if (status === 404) return "The requested resource was not found.";
    if (status === 409) return "There is a conflict with the current state of the resource.";
    if (status === 422) return "The submitted data is invalid. Please review the highlighted fields.";
    if (status === 500) return "An internal server error occurred. Please try again later.";
    if (status === 502 || status === 503 || status === 504) {
      return "The server is temporarily unavailable. Please try again shortly.";
    }
    if (axiosErr.code === "ECONNABORTED") return "The request timed out. Please try again.";
    if (axiosErr.code === "ERR_NETWORK") return "Unable to reach the server. Please check your connection.";
  }

  if (error instanceof Error) return error.message;
  return fallback;
}
