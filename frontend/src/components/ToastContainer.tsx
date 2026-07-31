import { useToastStore, type ToastType } from "../store/useToastStore";

const styles: Record<ToastType, { container: string; icon: string }> = {
  success: {
    container: "border-green-500/40 bg-green-500/10",
    icon: "bg-green-500",
  },
  info: {
    container: "border-blue-500/40 bg-blue-500/10",
    icon: "bg-blue-500",
  },
  warning: {
    container: "border-yellow-500/40 bg-yellow-500/10",
    icon: "bg-yellow-500",
  },
  error: {
    container: "border-red-500/40 bg-red-500/10",
    icon: "bg-red-500",
  },
};

const icons: Record<ToastType, string> = {
  success: "✓",
  info: "ℹ",
  warning: "⚠",
  error: "✕",
};

export default function ToastContainer() {
  const { toasts, dismiss } = useToastStore();

  if (toasts.length === 0) return null;

  return (
    <div className="fixed top-16 right-4 z-[10000] flex flex-col gap-2 w-80 max-w-[calc(100vw-2rem)]">
      {toasts.map((toast) => {
        const style = styles[toast.type];
        return (
          <div
            key={toast.id}
            role="status"
            className={`flex items-start gap-3 p-3 rounded-lg border shadow-lg backdrop-blur-sm ${style.container}`}
          >
            <span
              className={`w-5 h-5 shrink-0 rounded-full ${style.icon} text-white flex items-center justify-center text-xs font-bold`}
            >
              {icons[toast.type]}
            </span>
            <p className="flex-1 text-sm text-slate-200 leading-snug break-words">
              {toast.message}
            </p>
            <button
              onClick={() => dismiss(toast.id)}
              className="text-slate-400 hover:text-white transition-colors shrink-0"
              aria-label="Dismiss notification"
            >
              ✕
            </button>
          </div>
        );
      })}
    </div>
  );
}
