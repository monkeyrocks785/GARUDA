import type { ReactNode } from "react";

type BadgeTone = "gray" | "green" | "blue" | "red" | "yellow" | "emerald" | "purple";

const tones: Record<BadgeTone, string> = {
  gray: "bg-slate-500/15 text-slate-300",
  green: "bg-green-500/15 text-green-400",
  blue: "bg-blue-500/15 text-blue-400",
  red: "bg-red-500/15 text-red-400",
  yellow: "bg-yellow-500/15 text-yellow-400",
  emerald: "bg-emerald-500/15 text-emerald-400",
  purple: "bg-purple-500/15 text-purple-400",
};

const defaultByStatus: Record<string, BadgeTone> = {
  active: "green",
  completed: "emerald",
  processing: "blue",
  running: "blue",
  queued: "yellow",
  pending: "yellow",
  paused: "yellow",
  failed: "red",
  error: "red",
  cancelled: "gray",
  archived: "gray",
  created: "gray",
  new: "blue",
  acknowledged: "yellow",
  resolved: "emerald",
  dismissed: "gray",
  in_review: "purple",
};

interface BadgeProps {
  children: ReactNode;
  tone?: BadgeTone;
  status?: string;
  className?: string;
}

export default function Badge({ children, tone, status, className = "" }: BadgeProps) {
  const resolvedTone = tone || (status ? defaultByStatus[status.toLowerCase()] || "gray" : "gray");
  return (
    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${tones[resolvedTone]} ${className}`}>
      {children}
    </span>
  );
}
