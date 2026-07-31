interface LoadingStateProps {
  label?: string;
  compact?: boolean;
}

export default function LoadingState({ label = "Loading...", compact }: LoadingStateProps) {
  return (
    <div
      className={`flex flex-col items-center justify-center ${
        compact ? "py-6" : "py-16"
      } text-slate-400`}
    >
      <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-500 mb-3" />
      <p className="text-sm">{label}</p>
    </div>
  );
}
