import { useState } from "react";
import { Menu, Plus, Zap, X } from "lucide-react";
import type { Agent, AgentId } from "../types";
import { AgentIcon, ACCENT_MAP } from "../agentVisuals";

interface HeaderProps {
  agent: Agent;
  sessionId: string;
  onOpenSidebar: () => void;
  onNewSession: () => void;
  pendingCount: number;
}

export function Header({
  agent,
  sessionId,
  onOpenSidebar,
  onNewSession,
  pendingCount,
}: HeaderProps) {
  const accent = ACCENT_MAP[agent.accent];
  const [copied, setCopied] = useState(false);

  function copySession() {
    navigator.clipboard?.writeText(sessionId).then(() => {
      setCopied(true);
      setTimeout(() => setCopied(false), 1200);
    });
  }

  return (
    <header className="flex items-center gap-3 border-b border-white/5 bg-ink-900/60 px-4 py-3 backdrop-blur-xl sm:px-6">
      <button
        onClick={onOpenSidebar}
        className="grid h-9 w-9 place-items-center rounded-lg text-slate-300 hover:bg-white/5 hover:text-white lg:hidden"
        aria-label="Open menu"
      >
        <Menu className="h-5 w-5" />
      </button>

      <div className="flex min-w-0 flex-1 items-center gap-3">
        <div
          className={`grid h-10 w-10 shrink-0 place-items-center rounded-xl ${accent.bgSoft} ${accent.text} ${accent.glow}`}
        >
          <AgentIcon icon={agent.icon} className="h-5 w-5" />
        </div>
        <div className="min-w-0">
          <div className="flex items-center gap-2">
            <h1 className="truncate font-display text-sm font-semibold text-white sm:text-base">
              {agent.name}
            </h1>
            <span className={`chip ${accent.bgSoft} ${accent.text} hidden sm:inline-flex`}>
              <span className={`h-1.5 w-1.5 rounded-full ${accent.dot}`} /> active
            </span>
          </div>
          <p className="truncate text-[11px] text-slate-400">{agent.tagline}</p>
        </div>
      </div>

      <button
        onClick={copySession}
        title="Copy session id"
        className="hidden items-center gap-1.5 rounded-lg border border-white/5 bg-white/[0.03] px-2.5 py-1.5 text-[11px] text-slate-400 transition-colors hover:text-slate-200 md:flex"
      >
        <span className="font-mono">{copied ? "copied!" : sessionId.slice(0, 12)}…</span>
      </button>

      <div className="hidden items-center gap-1.5 rounded-lg border border-white/5 bg-white/[0.03] px-2.5 py-1.5 text-[11px] text-slate-400 sm:flex">
        <Zap className="h-3 w-3 text-amber-400" />
        <span>{pendingCount} queued</span>
      </div>

      <button
        onClick={onNewSession}
        className="flex items-center gap-1.5 rounded-lg border border-white/10 bg-white/[0.04] px-3 py-2 text-xs font-medium text-slate-200 transition-colors hover:border-brand-500/40 hover:bg-brand-500/10 hover:text-white"
      >
        <Plus className="h-3.5 w-3.5" /> New
      </button>
    </header>
  );
}

export function AgentSwitchBanner({
  fromAgent,
  toAgent,
  onDismiss,
}: {
  fromAgent: Agent;
  toAgent: Agent;
  onDismiss: () => void;
}) {
  return (
    <div className="flex items-center gap-2 border-b border-white/5 bg-brand-500/[0.06] px-4 py-2 text-xs text-slate-300 sm:px-8">
      <span className="text-slate-400">Switched from</span>
      <span className="font-medium text-slate-200">{fromAgent.name}</span>
      <span className="text-slate-500">→</span>
      <span className="font-medium text-white">{toAgent.name}</span>
      <button
        onClick={onDismiss}
        className="ml-auto grid h-5 w-5 place-items-center rounded text-slate-400 hover:text-white"
        aria-label="Dismiss"
      >
        <X className="h-3 w-3" />
      </button>
    </div>
  );
}

export type { AgentId };
