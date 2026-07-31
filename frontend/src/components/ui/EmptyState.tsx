import type { ReactNode } from "react";

interface EmptyStateProps {
  title: string;
  description?: string;
  icon?: ReactNode;
  action?: ReactNode;
  compact?: boolean;
}

export default function EmptyState({ title, description, icon, action, compact }: EmptyStateProps) {
  return (
    <div
      className={`bg-slate-800/50 border border-slate-700/50 rounded-xl text-center ${
        compact ? "p-6" : "p-10"
      }`}
    >
      <div className="w-14 h-14 mx-auto mb-4 rounded-full bg-slate-700/50 flex items-center justify-center">
        {icon || (
          <svg className="w-7 h-7 text-slate-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M20 13V6a2 2 0 00-2-2H6a2 2 0 00-2 2v7m16 0v5a2 2 0 01-2 2H6a2 2 0 01-2-2v-5m16 0h-2.586a1 1 0 00-.707.293l-2.414 2.414a1 1 0 01-.707.293h-3.172a1 1 0 01-.707-.293l-2.414-2.414A1 1 0 006.586 13H4"
            />
          </svg>
        )}
      </div>
      <h3 className="text-base font-semibold text-white mb-1.5">{title}</h3>
      {description && (
        <p className="text-sm text-slate-400 max-w-md mx-auto mb-4">{description}</p>
      )}
      {action}
    </div>
  );
}
