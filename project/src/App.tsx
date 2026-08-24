import { useCallback, useMemo, useRef, useState } from "react";
import { Sidebar } from "./components/Sidebar";
import { Header, AgentSwitchBanner } from "./components/Header";
import { ChatWindow } from "./components/ChatWindow";
import { MessageInput } from "./components/MessageInput";
import { StatusPanel } from "./components/StatusPanel";
import { AGENTS, getAgent } from "./agents";
import type {
  Agent,
  AgentId,
  AgentStatus,
  ChatMessage,
  Step,
} from "./types";
import { sendMessage, createSessionId, createMessageId } from "./api";

export default function App() {
  const [sessionId] = useState(() => createSessionId());
  const [selectedId, setSelectedId] = useState<AgentId>("planning");
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [statusPanelOpen, setStatusPanelOpen] = useState(false);

  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [status, setStatus] = useState<AgentStatus>("idle");
  const [thinkingSteps, setThinkingSteps] = useState<Step[]>([]);
  const [lastActivity, setLastActivity] = useState<string | null>(null);
  const [switchBanner, setSwitchBanner] = useState<{ from: Agent; to: Agent } | null>(null);
  const stepTimers = useRef<ReturnType<typeof setTimeout>[]>([]);

  const selectedAgent = getAgent(selectedId);

  const perAgentMessageCount = useMemo(() => {
    const counts: Record<AgentId, number> = {
      memory: 0,
      planning: 0,
      flight: 0,
      refund: 0,
      vip: 0,
    };
    for (const m of messages) {
      if (m.role === "user") counts[m.agentId] = (counts[m.agentId] ?? 0) + 1;
    }
    return counts;
  }, [messages]);

  const clearStepTimers = useCallback(() => {
    stepTimers.current.forEach(clearTimeout);
    stepTimers.current = [];
  }, []);

  const animateSteps = useCallback(
    (agentId: AgentId): Step[] => {
      const stepDefs = STEP_DEFS[agentId];
      const initial: Step[] = stepDefs.map((label) => ({
        label,
        state: "pending" as const,
      }));
      setThinkingSteps(initial);

      stepDefs.forEach((_, i) => {
        const runT = setTimeout(() => {
          setThinkingSteps((prev) =>
            prev.map((s, idx) => (idx === i ? { ...s, state: "running" } : s)),
          );
        }, 250 + i * 380);
        stepTimers.current.push(runT);

        const doneT = setTimeout(() => {
          setThinkingSteps((prev) =>
            prev.map((s, idx) => (idx === i ? { ...s, state: "done" } : s)),
          );
        }, 250 + i * 380 + 320);
        stepTimers.current.push(doneT);
      });

      return stepDefs.map((label) => ({ label, state: "done" as const }));
    },
    [],
  );

  const handleSend = useCallback(
    async (text: string) => {
      const userMsg: ChatMessage = {
        id: createMessageId(),
        sessionId,
        agentId: selectedId,
        role: "user",
        content: text,
        createdAt: new Date().toISOString(),
      };
      setMessages((prev) => [...prev, userMsg]);
      setStatus("thinking");

      const finalSteps = animateSteps(selectedId);

      try {
        const res = await sendMessage({
          agent_id: selectedId,
          session_id: sessionId,
          message: text,
        });

        const assistantMsg: ChatMessage = {
          id: res.message_id,
          sessionId: res.session_id,
          agentId: res.agent_id,
          role: "assistant",
          content: res.content,
          steps: res.steps.length ? res.steps : finalSteps,
          status: res.status,
          createdAt: res.created_at,
        };
        setMessages((prev) => [...prev, assistantMsg]);
        setStatus(res.status === "error" ? "error" : "completed");
        setLastActivity(formatTime(res.created_at));
      } catch (err) {
        const errorMessage: ChatMessage = {
          id: createMessageId(),
          sessionId,
          agentId: selectedId,
          role: "assistant",
          content:
            err instanceof Error
              ? `Something went wrong: ${err.message}`
              : "Something went wrong. Please try again.",
          steps: [],
          status: "error",
          createdAt: new Date().toISOString(),
        };
        setMessages((prev) => [...prev, errorMessage]);
        setStatus("error");
      } finally {
        clearStepTimers();
        setTimeout(() => setThinkingSteps([]), 600);
      }
    },
    [selectedId, sessionId, animateSteps, clearStepTimers],
  );

  const handleSelectAgent = useCallback(
    (id: AgentId) => {
      if (id === selectedId) return;
      setSwitchBanner({ from: selectedAgent, to: getAgent(id) });
      setSelectedId(id);
      setStatus("idle");
      setThinkingSteps([]);
      setSidebarOpen(false);
    },
    [selectedId, selectedAgent],
  );

  const handleNewSession = useCallback(() => {
    setMessages([]);
    setStatus("idle");
    setThinkingSteps([]);
    setLastActivity(null);
    setSwitchBanner(null);
  }, []);

  return (
    <div className="aurora flex h-screen w-screen overflow-hidden bg-ink-950 text-slate-100">
      <Sidebar
        selectedId={selectedId}
        onSelect={handleSelectAgent}
        perAgentMessageCount={perAgentMessageCount}
        open={sidebarOpen}
        onClose={() => setSidebarOpen(false)}
      />

      <div className="flex min-w-0 flex-1 flex-col">
        <Header
          agent={selectedAgent}
          sessionId={sessionId}
          onOpenSidebar={() => setSidebarOpen(true)}
          onNewSession={handleNewSession}
          pendingCount={thinkingSteps.filter((s) => s.state === "running").length}
        />

        {switchBanner && (
          <AgentSwitchBanner
            fromAgent={switchBanner.from}
            toAgent={switchBanner.to}
            onDismiss={() => setSwitchBanner(null)}
          />
        )}

        <div className="flex min-h-0 flex-1 flex-col xl:flex-row">
          <main className="flex min-h-0 min-w-0 flex-1 flex-col">
            <ChatWindow
              messages={messages}
              agent={selectedAgent}
              isThinking={status === "thinking"}
              thinkingSteps={thinkingSteps}
            />
            <MessageInput
              onSend={handleSend}
              disabled={status === "thinking"}
              placeholder={`Message ${selectedAgent.name}…`}
            />
          </main>

          {/* Desktop status panel */}
          <div className="hidden xl:block">
            <StatusPanel
              activeAgent={selectedAgent}
              status={status}
              steps={thinkingSteps.length ? thinkingSteps : lastSteps(messages, selectedId)}
              lastActivity={lastActivity}
              totalMessages={messages.filter((m) => m.role === "user").length}
            />
          </div>
        </div>
      </div>

      {/* Mobile status toggle */}
      <MobileStatusToggle
        open={statusPanelOpen}
        onToggle={() => setStatusPanelOpen((o) => !o)}
      />
      {statusPanelOpen && (
        <div className="fixed inset-0 z-30 xl:hidden">
          <div
            className="absolute inset-0 bg-black/60 backdrop-blur-sm"
            onClick={() => setStatusPanelOpen(false)}
          />
          <div className="absolute bottom-0 left-0 right-0 max-h-[70vh] overflow-y-auto rounded-t-2xl border-t border-white/10 bg-ink-950">
            <StatusPanel
              activeAgent={selectedAgent}
              status={status}
              steps={thinkingSteps.length ? thinkingSteps : lastSteps(messages, selectedId)}
              lastActivity={lastActivity}
              totalMessages={messages.filter((m) => m.role === "user").length}
            />
          </div>
        </div>
      )}
    </div>
  );
}

function MobileStatusToggle({
  open,
  onToggle,
}: {
  open: boolean;
  onToggle: () => void;
}) {
  return (
    <button
      onClick={onToggle}
      className="fixed bottom-24 right-4 z-20 grid h-12 w-12 place-items-center rounded-full bg-gradient-to-br from-brand-500 to-accent-500 text-white shadow-glow transition-transform xl:hidden"
      aria-label="Toggle status panel"
    >
      <span className="relative flex h-4 w-4 items-center justify-center">
        {open ? (
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round">
            <path d="M6 6l12 12M6 18L18 6" />
          </svg>
        ) : (
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
            <path d="M22 12h-4l-3 9L9 3l-3 9H2" />
          </svg>
        )}
      </span>
    </button>
  );
}

function lastSteps(messages: ChatMessage[], agentId: AgentId): Step[] {
  for (let i = messages.length - 1; i >= 0; i--) {
    const m = messages[i];
    if (m.agentId === agentId && m.role === "assistant" && m.steps?.length) {
      return m.steps;
    }
  }
  return [];
}

function formatTime(iso: string): string {
  try {
    return new Date(iso).toLocaleTimeString([], {
      hour: "2-digit",
      minute: "2-digit",
    });
  } catch {
    return "—";
  }
}

const STEP_DEFS: Record<AgentId, string[]> = {
  memory: [
    "Reading profile context",
    "Recalling past trips",
    "Indexing preferences",
    "Composing recall summary",
  ],
  planning: [
    "Understanding request",
    "Selecting destinations",
    "Balancing daily rhythm",
    "Drafting itinerary",
  ],
  flight: [
    "Parsing route details",
    "Searching carriers",
    "Comparing fares",
    "Ranking options",
  ],
  refund: [
    "Locating booking",
    "Reviewing refund policy",
    "Checking eligibility",
    "Preparing request",
  ],
  vip: [
    "Verifying member tier",
    "Curating perks",
    "Securing upgrades",
    "Finalizing concierge note",
  ],
};

export { AGENTS };
