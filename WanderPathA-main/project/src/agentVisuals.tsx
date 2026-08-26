import {
  Brain,
  Map as MapIcon,
  Plane,
  RotateCcw,
  Crown,
  type LucideIcon,
} from "lucide-react";
import type { Agent } from "./types";

const ICONS: Record<string, LucideIcon> = {
  brain: Brain,
  map: MapIcon,
  plane: Plane,
  "rotate-ccw": RotateCcw,
  crown: Crown,
};

export function AgentIcon({
  icon,
  className,
}: {
  icon: string;
  className?: string;
}) {
  const Cmp = ICONS[icon] ?? Brain;
  return <Cmp className={className} />;
}

export const ACCENT_MAP: Record<
  Agent["accent"],
  {
    text: string;
    ring: string;
    bgSoft: string;
    bgSolid: string;
    border: string;
    glow: string;
    dot: string;
  }
> = {
  indigo: {
    text: "text-brand-300",
    ring: "ring-brand-500/40",
    bgSoft: "bg-brand-500/15",
    bgSolid: "bg-brand-500",
    border: "border-brand-500/40",
    glow: "shadow-glow",
    dot: "bg-brand-400",
  },
  violet: {
    text: "text-accent-400",
    ring: "ring-accent-500/40",
    bgSoft: "bg-accent-500/15",
    bgSolid: "bg-accent-500",
    border: "border-accent-500/40",
    glow: "shadow-glow-purple",
    dot: "bg-accent-400",
  },
  sky: {
    text: "text-sky2-400",
    ring: "ring-sky2-500/40",
    bgSoft: "bg-sky2-500/15",
    bgSolid: "bg-sky2-500",
    border: "border-sky2-500/40",
    glow: "shadow-glow",
    dot: "bg-sky2-400",
  },
  rose: {
    text: "text-rose-300",
    ring: "ring-rose-500/40",
    bgSoft: "bg-rose-500/15",
    bgSolid: "bg-rose-500",
    border: "border-rose-500/40",
    glow: "shadow-glow",
    dot: "bg-rose-400",
  },
  amber: {
    text: "text-amber-300",
    ring: "ring-amber-500/40",
    bgSoft: "bg-amber-500/15",
    bgSolid: "bg-amber-500",
    border: "border-amber-500/40",
    glow: "shadow-glow",
    dot: "bg-amber-400",
  },
};
