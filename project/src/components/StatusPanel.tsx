import { Activity, CheckCircle2, Clock, CircleDot, XCircle } from "lucide-react";
import type { Agent, AgentStatus, Step, AgentId } from "../types";
import { AGENTS } from "../agents";
import { AgentIcon, ACCENT_MAP } from "../agentVisuals";

interface StatusPanelProps {
  activeAgent: Agent;
  status: AgentStatus;
  steps: Step[];
  lastActivity: string | null;
  totalMessages: number;
}

export function StatusPanel({
  activeAgent,
  status,
  steps,
  lastActivity,
  totalMessages,
}: StatusPanelProps) {
  const accent = ACCENT_MAP[activeAgent.accent];

  return (
    <aside className="flex w-full flex-col gap-4 border-l border-white/5 bg-ink-950/60 p-4 backdrop-blur-xl xl:w-80">
      {/* Current agent card */}
      <section className="rounded-2xl border border-white/5 bg-ink-850/50 p-4">
        <p className="mb-3 text-[11px] font-semibold uppercase tracking-[0.16em] text-slate-500">
          Current Agent
        </p>
        <div className="flex items-center gap-3">
          <div
            className={`grid h-11 w-11 place-items-center rounded-xl ${accent.bgSoft} ${accent.text} ${accent.glow}`}
          >
            <AgentIcon icon={activeAgent.icon} className="h-5 w-5" />
          </div>
          <div className="min-w-0">
            <p className="truncate text-sm font-semibold text-white">
              {activeAgent.name}
            </p>
            <div className="mt-0.5 flex items-center gap-1.5">
              <StatusBadge status={status} />
            </div>
          </div>
        </div>
        <p className="mt-3 text-xs leading-relaxed text-slate-400">
          {activeAgent.description}
        </p>
      </section>

      {/* Execution status */}
      <section className="rounded-2xl border border-white/5 bg-ink-850/50 p-4">
        <div className="mb-3 flex items-center gap-2">
          <Activity className="h-3.5 w-3.5 text-brand-300" />
          <p className="text-[11px] font-semibold uppercase tracking-[0.16em] text-slate-500">
            Execution Status
          </p>
        </div>

        {steps.length === 0 ? (
          <p className="py-4 text-center text-xs text-slate-500">
            No active execution. Send a message to begin.
          </p>
        ) : (
          <ol className="space-y-2.5">
            {steps.map((step, i) => (
              <li key={i} className="flex items-start gap-2.5">
                <StepIcon state={step.state} index={i + 1} />
                <div className="min-w-0 flex-1">
                  <p
                    className={`text-xs font-medium ${
                      step.state === "running"
                        ? "text-white"
                        : step.state === "error"
                          ? "text-rose-300"
                          : step.state === "done"
                            ? "text-slate-200"
                            : "text-slate-500"
                    }`}
                  >
                    {step.label}
                  </p>
                  <p className="text-[10px] uppercase tracking-wide text-slate-500">
                    {step.state}
                  </p>
                </div>
              </li>
            ))}
          </ol>
        )}
      </section>

      {/* Quick stats */}
      <section className="grid grid-cols-2 gap-3">
        <Stat label="Messages" value={totalMessages} icon={<Clock className="h-3.5 w-3.5" />} />
        <Stat
          label="Last activity"
          value={lastActivity ?? "—"}
          icon={<CheckCircle2 className="h-3.5 w-3.5" />}
        />
      </section>

      {/* Agent roster mini */}
      <section className="rounded-2xl border border-white/5 bg-ink-850/50 p-4">
        <p className="mb-3 text-[11px] font-semibold uppercase tracking-[0.16em] text-slate-500">
          Roster
        </p>
        <ul className="space-y-2">
          {AGENTS.map((a) => {
            const a2 = ACCENT_MAP[a.accent];
            const isActive = a.id === activeAgent.id;
            return (
              <li
                key={a.id}
                className={`flex items-center gap-2.5 rounded-lg px-2 py-1.5 ${
                  isActive ? "bg-white/[0.05]" : ""
                }`}
              >
                <span
                  className={`grid h-6 w-6 place-items-center rounded-md ${a2.bgSoft} ${a2.text}`}
                >
                  <AgentIcon icon={a.icon} className="h-3.5 w-3.5" />
                </span>
                <span
                  className={`flex-1 truncate text-xs ${
                    isActive ? "font-medium text-white" : "text-slate-300"
                  }`}
                >
                  {a.name}
                </span>
                <span className={`h-1.5 w-1.5 rounded-full ${a2.dot} ${isActive ? "" : "opacity-40"}`} />
              </li>
            );
          })}
        </ul>
      </section>
    </aside>
  );
}

function StatusBadge({ status }: { status: AgentStatus }) {
  const map: Record<AgentStatus, { text: string; dot: string; label: string }> = {
    idle: { text: "text-slate-400", dot: "bg-slate-500", label: "idle" },
    thinking: { text: "text-brand-300", dot: "bg-brand-400 animate-pulse", label: "thinking" },
    completed: { text: "text-emerald-300", dot: "bg-emerald-400", label: "completed" },
    error: { text: "text-rose-300", dot: "bg-rose-400", label: "error" },
  };
  const m = map[status];
  return (
    <span className={`inline-flex items-center gap-1.5 text-[11px] font-medium ${m.text}`}>
      <span className={`h-1.5 w-1.5 rounded-full ${m.dot}`} /> {m.label}
    </span>
  );
}

function StepIcon({
  state,
  index,
}: {
  state: Step["state"];
  index: number;
}) {
  if (state === "done")
    return (
      <span className="mt-0.5 grid h-5 w-5 shrink-0 place-items-center rounded-full bg-emerald-500/15 text-emerald-300">
        <CheckCircle2 className="h-3.5 w-3.5" />
      </span>
    );
  if (state === "running")
    return (
      <span className="mt-0.5 grid h-5 w-5 shrink-0 place-items-center rounded-full bg-brand-500/20 text-brand-200 ring-2 ring-brand-500/30">
        <CircleDot className="h-3.5 w-3.5 animate-pulse" />
      </span>
    );
  if (state === "error")
    return (
      <span className="mt-0.5 grid h-5 w-5 shrink-0 place-items-center rounded-full bg-rose-500/15 text-rose-300">
        <XCircle className="h-3.5 w-3.5" />
      </span>
    );
  return (
    <span className="mt-0.5 grid h-5 w-5 shrink-0 place-items-center rounded-full border border-white/10 text-[10px] font-semibold text-slate-500">
      {index}
    </span>
  );
}

function Stat({
  label,
  value,
  icon,
}: {
  label: string;
  value: string | number;
  icon: React.ReactNode;
}) {
  return (
    <div className="rounded-xl border border-white/5 bg-ink-850/50 p-3">
      <div className="mb-1 flex items-center gap-1.5 text-slate-500">
        {icon}
        <span className="text-[10px] font-medium uppercase tracking-wide">{label}</span>
      </div>
      <p className="truncate text-sm font-semibold text-white">{value}</p>
    </div>
  );
}

export type { AgentId };
