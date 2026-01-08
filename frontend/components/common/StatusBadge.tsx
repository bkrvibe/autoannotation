import { cva, type VariantProps } from "class-variance-authority";
import { cn } from "@/lib/utils";
import { 
  Clock, 
  Loader2, 
  CheckCircle2, 
  XCircle, 
  AlertCircle,
  Pause
} from "lucide-react";

const statusBadgeVariants = cva(
  "inline-flex items-center gap-1.5 rounded-full px-3 py-1 text-xs font-medium",
  {
    variants: {
      status: {
        queued: "bg-amber-500/15 text-amber-400 border border-amber-500/20",
        running: "bg-blue-500/15 text-blue-400 border border-blue-500/20",
        success: "bg-emerald-500/15 text-emerald-400 border border-emerald-500/20",
        failed: "bg-red-500/15 text-red-400 border border-red-500/20",
        cancelled: "bg-zinc-500/15 text-zinc-400 border border-zinc-500/20",
        pending: "bg-violet-500/15 text-violet-400 border border-violet-500/20",
      },
    },
    defaultVariants: {
      status: "queued",
    },
  }
);

const statusIcons = {
  queued: Clock,
  running: Loader2,
  success: CheckCircle2,
  failed: XCircle,
  cancelled: Pause,
  pending: AlertCircle,
};

const statusLabels: Record<string, string> = {
  queued: "Queued",
  running: "Running",
  success: "Completed",
  failed: "Failed",
  cancelled: "Cancelled",
  pending: "Pending",
};

type StatusType = "queued" | "running" | "success" | "failed" | "cancelled" | "pending";

interface StatusBadgeProps {
  status: string;
  className?: string;
}

export function StatusBadge({ status, className }: StatusBadgeProps) {
  const normalizedStatus = status.toLowerCase() as StatusType;
  const Icon = statusIcons[normalizedStatus] || Clock;
  const label = statusLabels[normalizedStatus] || status;

  return (
    <span className={cn(statusBadgeVariants({ status: normalizedStatus }), className)}>
      <Icon className={cn("h-3 w-3", normalizedStatus === "running" && "animate-spin")} />
      {label}
    </span>
  );
}
