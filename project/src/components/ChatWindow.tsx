import { useEffect, useRef } from "react";
import { AlertCircle, Check, Loader2, Clock } from "lucide-react";
import type { ChatMessage, Agent } from "../types";
import { AgentIcon, ACCENT_MAP } from "../agentVisuals";

interface ChatWindowProps {
  messages: ChatMessage[];
  agent: Agent;
  isThinking: boolean;
  thinkingSteps: { label: string; state: "pending" | "running" | "done" | "error" }[];
}

export function ChatWindow({
  messages,
  agent,
  isThinking,
  thinkingSteps,
}: ChatWindowProps) {
  const scrollRef = useRef<HTMLDivElement>(null);
  const accent = ACCENT_MAP[agent.accent];

  useEffect(() => {
    const el = scrollRef.current;
    if (el) el.scrollTo({ top: el.scrollHeight, behavior: "smooth" });
  }, [messages, isThinking, thinkingSteps]);

  return (
    <div
      ref={scrollRef}
      className="scroll-thin flex-1 overflow-y-auto px-4 py-6 sm:px-8"
    >
      <div className="mx-auto flex max-w-3xl flex-col gap-5">
        {messages.length === 0 && !isThinking && <EmptyState agent={agent} />}

        {messages.map((m) => (
          <MessageBubble key={m.id} message={m} agent={agent} />
        ))}

        {isThinking && <ThinkingBubble agent={agent} steps={thinkingSteps} />}
      </div>
    </div>
  );
}

function EmptyState({ agent }: { agent: Agent }) {
  const accent = ACCENT_MAP[agent.accent];
  return (
    <div className="flex flex-col items-center justify-center py-16 text-center animate-fade-up">
      <div
        className={`mb-5 grid h-16 w-16 place-items-center rounded-2xl ${accent.bgSoft} ${accent.text} ${accent.glow}`}
      >
        <AgentIcon icon={agent.icon} className="h-8 w-8" />
      </div>
      <h2 className="font-display text-xl font-semibold text-white">
        {agent.name}
      </h2>
      <p className="mt-2 max-w-sm text-sm leading-relaxed text-slate-400">
        {agent.description}
      </p>
      <div className="mt-6 flex flex-wrap justify-center gap-2">
        {SUGGESTIONS[agent.id].map((s) => (
          <span
            key={s}
            className="chip border border-white/5 bg-white/[0.03] text-slate-300"
          >
            {s}
          </span>
        ))}
      </div>
    </div>
  );
}

const SUGGESTIONS: Record<Agent["id"], string[]> = {
  memory: ["What do you know about me?", "Update my preferences", "Show past trips"],
  planning: ["Plan a 5-day Kyoto trip", "Weekend in Lisbon", "10 days in Iceland"],
  flight: ["Lisbon → Tokyo in November", "Cheapest JFK → CDG", "Direct to Singapore"],
  refund: ["Refund booking LEG-77821", "Cancel my Friday flight", "Check refund status"],
  vip: ["Upgrade my Kyoto stay", "Lounge access for layover", "Private transfer"],
};

function MessageBubble({ message, agent }: { message: ChatMessage; agent: Agent }) {
  const isUser = message.role === "user";
  const accent = ACCENT_MAP[agent.accent];

  if (isUser) {
    return (
      <div className="flex justify-end animate-fade-up">
        <div className="max-w-[85%] rounded-2xl rounded-br-md bg-gradient-to-br from-brand-600 to-brand-500 px-4 py-3 text-sm leading-relaxed text-white shadow-lg shadow-brand-900/40">
          <p className="whitespace-pre-wrap">{message.content}</p>
          <time className="mt-1.5 block text-right text-[10px] text-brand-100/70">
            {formatTime(message.createdAt)}
          </time>
        </div>
      </div>
    );
  }

  const isError = message.status === "error";

  return (
    <div className="flex gap-3 animate-fade-up">
      <div
        className={`mt-0.5 grid h-9 w-9 shrink-0 place-items-center rounded-xl ${accent.bgSoft} ${accent.text}`}
      >
        <AgentIcon icon={agent.icon} className="h-[18px] w-[18px]" />
      </div>
      <div className="min-w-0 flex-1">
        <div className="mb-1 flex items-center gap-2">
          <span className="text-xs font-semibold text-white">{agent.name}</span>
          {isError ? (
            <span className="chip border border-rose-500/30 bg-rose-500/10 text-rose-300">
              <AlertCircle className="h-3 w-3" /> error
            </span>
          ) : (
            <span className="chip border border-emerald-500/20 bg-emerald-500/10 text-emerald-300">
              <Check className="h-3 w-3" /> completed
            </span>
          )}
        </div>
        <div className="rounded-2xl rounded-tl-md border border-white/5 bg-ink-850/60 px-4 py-3 text-sm leading-relaxed text-slate-100">
          <p className="whitespace-pre-wrap">{message.content}</p>
          {message.steps && message.steps.length > 0 && (
            <div className="mt-3 space-y-1.5 border-t border-white/5 pt-3">
              {message.steps.map((step, i) => (
                <div
                  key={i}
                  className="flex items-center gap-2 text-[11px] text-slate-400"
                >
                  <StepDot state={step.state} />
                  <span>{step.label}</span>
                </div>
              ))}
            </div>
          )}
          <time className="mt-2 flex items-center gap-1 text-[10px] text-slate-500">
            <Clock className="h-3 w-3" /> {formatTime(message.createdAt)}
          </time>
        </div>
      </div>
    </div>
  );
}

function ThinkingBubble({
  agent,
  steps,
}: {
  agent: Agent;
  steps: { label: string; state: "pending" | "running" | "done" | "error" }[];
}) {
  const accent = ACCENT_MAP[agent.accent];
  return (
    <div className="flex gap-3 animate-fade-up">
      <div
        className={`mt-0.5 grid h-9 w-9 shrink-0 place-items-center rounded-xl ${accent.bgSoft} ${accent.text}`}
      >
        <AgentIcon icon={agent.icon} className="h-[18px] w-[18px]" />
      </div>
      <div className="min-w-0 flex-1">
        <div className="mb-1 flex items-center gap-2">
          <span className="text-xs font-semibold text-white">{agent.name}</span>
          <span className={`chip ${accent.bgSoft} ${accent.text}`}>
            <Loader2 className="h-3 w-3 animate-spin" /> thinking
          </span>
        </div>
        <div className="w-full max-w-sm rounded-2xl rounded-tl-md border border-white/5 bg-ink-850/60 px-4 py-3">
          <div className="mb-2.5 flex items-center gap-1.5">
            <span className="typing-dot h-1.5 w-1.5 rounded-full bg-slate-400" />
            <span className="typing-dot h-1.5 w-1.5 rounded-full bg-slate-400" />
            <span className="typing-dot h-1.5 w-1.5 rounded-full bg-slate-400" />
          </div>
          {steps.length > 0 && (
            <div className="space-y-1.5">
              {steps.map((s, i) => (
                <div
                  key={i}
                  className="flex items-center gap-2 text-[11px] text-slate-400"
                >
                  <StepDot state={s.state} />
                  <span className={s.state === "running" ? "text-slate-200" : ""}>
                    {s.label}
                  </span>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

function StepDot({ state }: { state: "pending" | "running" | "done" | "error" }) {
  if (state === "done")
    return <Check className="h-3 w-3 text-emerald-400" />;
  if (state === "running")
    return <Loader2 className="h-3 w-3 animate-spin text-brand-300" />;
  if (state === "error")
    return <AlertCircle className="h-3 w-3 text-rose-400" />;
  return <span className="h-1.5 w-1.5 rounded-full bg-slate-600" />;
}

function formatTime(iso: string): string {
  try {
    return new Date(iso).toLocaleTimeString([], {
      hour: "2-digit",
      minute: "2-digit",
    });
  } catch {
    return "";
  }
}
