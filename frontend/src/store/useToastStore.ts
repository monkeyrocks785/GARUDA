import { create } from "zustand";

export type ToastType = "success" | "info" | "warning" | "error";

export interface Toast {
  id: string;
  type: ToastType;
  message: string;
}

interface ToastState {
  toasts: Toast[];
  show: (type: ToastType, message: string) => void;
  dismiss: (id: string) => void;
  success: (message: string) => void;
  info: (message: string) => void;
  warning: (message: string) => void;
  error: (message: string) => void;
}

let toastCounter = 0;

export const useToastStore = create<ToastState>((set, get) => ({
  toasts: [],

  show: (type, message) => {
    const id = `toast-${++toastCounter}-${Date.now()}`;
    set((state) => ({ toasts: [...state.toasts, { id, type, message }] }));
    setTimeout(() => get().dismiss(id), 5000);
  },

  dismiss: (id) =>
    set((state) => ({ toasts: state.toasts.filter((t) => t.id !== id) })),

  success: (message) => get().show("success", message),
  info: (message) => get().show("info", message),
  warning: (message) => get().show("warning", message),
  error: (message) => get().show("error", message),
}));
