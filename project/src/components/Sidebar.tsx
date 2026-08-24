import { Compass, X, Sparkles, ChevronRight } from "lucide-react";
import type { Agent, AgentId } from "../types";
import { AGENTS } from "../agents";
import { AgentIcon, ACCENT_MAP } from "../agentVisuals";

interface SidebarProps {
  selectedId: AgentId;
  onSelect: (id: AgentId) => void;
  perAgentMessageCount: Record<AgentId, number>;
  open: boolean;
  onClose: () => void;
}

export function Sidebar({
  selectedId,
  onSelect,
  perAgentMessageCount,
  open,
  onClose,
}: SidebarProps) {
  return (
    <>
      {/* Mobile backdrop */}
      <div
        className={`fixed inset-0 z-30 bg-black/60 backdrop-blur-sm transition-opacity lg:hidden ${
          open ? "opacity-100" : "pointer-events-none opacity-0"
        }`}
        onClick={onClose}
        aria-hidden
      />

      <aside
        className={`fixed z-40 flex h-full w-72 flex-col border-r border-white/5 bg-ink-950/80 backdrop-blur-xl transition-transform duration-300 lg:static lg:translate-x-0 ${
          open ? "translate-x-0" : "-translate-x-full"
        }`}
      >
        {/* Brand */}
        <div className="flex items-center justify-between px-5 pt-5 pb-4">
          <div className="flex items-center gap-3">
            <div className="relative grid h-10 w-10 place-items-center rounded-xl bg-gradient-to-br from-brand-500 to-accent-500 shadow-glow">
              <Compass className="h-5 w-5 text-white" />
              <span className="absolute -right-0.5 -top-0.5 h-2.5 w-2.5 rounded-full bg-emerald-400 ring-2 ring-ink-950" />
            </div>
            <div className="leading-tight">
              <p className="font-display text-base font-semibold tracking-tight text-white">
                WanderPath
              </p>
              <p className="text-[11px] font-medium uppercase tracking-[0.18em] text-brand-300/80">
                AI Travel
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="grid h-8 w-8 place-items-center rounded-lg text-slate-400 hover:bg-white/5 hover:text-white lg:hidden"
            aria-label="Close menu"
          >
            <X className="h-4 w-4" />
          </button>
        </div>

        <div className="mx-5 mb-3 flex items-center gap-2 rounded-lg border border-white/5 bg-white/[0.03] px-3 py-2">
          <Sparkles className="h-3.5 w-3.5 text-accent-400" />
          <span className="text-[11px] font-medium text-slate-300">
            5 agents online
          </span>
        </div>

        <div className="px-3 pb-2 text-[11px] font-semibold uppercase tracking-[0.16em] text-slate-500">
          Agents
        </div>

        <nav className="scroll-thin flex-1 space-y-1 overflow-y-auto px-3 pb-4">
          {AGENTS.map((agent) => (
            <AgentButton
              key={agent.id}
              agent={agent}
              selected={agent.id === selectedId}
              count={perAgentMessageCount[agent.id] ?? 0}
              onSelect={() => onSelect(agent.id)}
            />
          ))}
        </nav>

        <div className="border-t border-white/5 px-5 py-4">
          <div className="flex items-center gap-3">
            <div className="grid h-9 w-9 place-items-center rounded-full bg-gradient-to-br from-brand-600 to-accent-600 text-sm font-semibold text-white">
              AT
            </div>
            <div className="min-w-0 flex-1 leading-tight">
              <p className="truncate text-sm font-medium text-white">
                Alex Traveler
              </p>
              <p className="truncate text-[11px] text-slate-400">
                Platinum member
              </p>
            </div>
            <ChevronRight className="h-4 w-4 text-slate-500" />
          </div>
        </div>
      </aside>
    </>
  );
}

function AgentButton({
  agent,
  selected,
  count,
  onSelect,
}: {
  agent: Agent;
  selected: boolean;
  count: number;
  onSelect: () => void;
}) {
  const accent = ACCENT_MAP[agent.accent];
  return (
    <button
      onClick={onSelect}
      className={`group relative flex w-full items-center gap-3 rounded-xl px-3 py-2.5 text-left transition-all ${
        selected
          ? `bg-white/[0.06] ${accent.border} border`
          : "border border-transparent hover:bg-white/[0.03]"
      }`}
    >
      <span
        className={`relative grid h-9 w-9 shrink-0 place-items-center rounded-lg transition-all ${
          selected
            ? `${accent.bgSoft} ${accent.text} ${accent.glow}`
            : "bg-white/[0.04] text-slate-300 group-hover:text-white"
        }`}
      >
        <AgentIcon icon={agent.icon} className="h-[18px] w-[18px]" />
        {selected && (
          <span className={`absolute -right-0.5 -top-0.5 h-2 w-2 rounded-full ${accent.dot}`} />
        )}
      </span>
      <span className="min-w-0 flex-1">
        <span
          className={`block truncate text-sm font-medium ${
            selected ? "text-white" : "text-slate-200"
          }`}
        >
          {agent.name}
        </span>
        <span className="block truncate text-[11px] text-slate-400">
          {agent.tagline}
        </span>
      </span>
      {count > 0 && (
        <span className="shrink-0 rounded-full bg-white/[0.06] px-1.5 py-0.5 text-[10px] font-semibold text-slate-300">
          {count}
        </span>
      )}
    </button>
  );
}
