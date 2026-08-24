import type {
  Agent,
  AgentId,
  ChatRequest,
  ChatResponse,
  Step,
} from "./types";
import { AGENTS } from "./agents";

const API_BASE = "/api";

let useMockFallback = false;

function uid(prefix: string): string {
  return `${prefix}_${Math.random().toString(36).slice(2, 10)}`;
}

async function realChat(req: ChatRequest): Promise<ChatResponse> {
  const res = await fetch(`${API_BASE}/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(req),
  });
  if (!res.ok) {
    const text = await res.text().catch(() => "");
    throw new Error(`Request failed (${res.status}): ${text}`);
  }
  return (await res.json()) as ChatResponse;
}

const STEP_BANK: Record<AgentId, string[]> = {
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

const MOCK_REPLIES: Record<AgentId, string[]> = {
  memory: [
    "I've recalled your preferences: window seat, mid-range hotels, and a soft spot for coastal cities. Want me to feed this to the Planning Agent?",
    "Noted. I'll remember that you prefer trains over short-haul flights and avoid red-eyes. This will inform every future suggestion.",
    "Here's what I have on file for you: 12 past trips, two favorite regions (Iberia and Japan), and a noted allergy to shellfish.",
  ],
  planning: [
    "Here's a balanced 5-day Kyoto plan:\n\n**Day 1** — Arashiyama bamboo grove + Tenryu-ji temple (morning), Gion district walk (evening).\n**Day 2** — Fushimi Inari at sunrise, Nishiki Market for lunch, Kiyomizu-dera by afternoon.\n**Day 3** — Day trip to Nara: Todai-ji + Nara Park.\n**Day 4** — Philosopher's Path, Ginkaku-ji, tea ceremony.\n**Day 5** — Nijo Castle, Kyoto Imperial Palace, late-afternoon onsen.\n\nWant me to send this to the Flight Agent for routes?",
    "I can build that out. A few quick questions: preferred pace (packed vs. relaxed), any must-see sights, and hotel budget tier?",
  ],
  flight: [
    "I found 3 strong options for Lisbon → Tokyo on your dates:\n\n1. **TP / Lufthansa** — 1 stop, 16h40m, €612 (best value)\n2. **Emirates** — 1 stop DXB, 19h10m, €748 (best onboard experience)\n3. **ANA direct** — 13h35m, €899 (fastest)\n\nWhich one should I hold?",
    "The early-morning departure is cheaper but adds a 6h layover. The midday option lands fresher for €80 more — I'd recommend it for jet lag. Want me to proceed?",
  ],
  refund: [
    "Your booking LEG-77821 is eligible for a full refund under the 24-hour waiver. I can file it now — confirmation will arrive within 10 minutes.",
    "This fare is non-refundable, but I can request a travel credit equal to 80% of the ticket value. Shall I submit that on your behalf?",
  ],
  vip: [
    "As a Platinum member, I've secured a complimentary suite upgrade at your Kyoto hotel and two lounge passes for your layover in Frankfurt.",
    "I can arrange a private airport transfer and a reserved table at a Michelin two-star in Gion — both covered under your tier. Should I confirm?",
  ],
};

function buildSteps(agentId: AgentId): Step[] {
  return STEP_BANK[agentId].map((label) => ({ label, state: "done" as const }));
}

async function mockChat(req: ChatRequest): Promise<ChatResponse> {
  const delay = 900 + Math.random() * 900;
  await new Promise((r) => setTimeout(r, delay));
  const replies = MOCK_REPLIES[req.agent_id];
  const content = replies[Math.floor(Math.random() * replies.length)];
  return {
    session_id: req.session_id,
    agent_id: req.agent_id,
    message_id: uid("msg"),
    role: "assistant",
    content,
    status: "completed",
    steps: buildSteps(req.agent_id),
    created_at: new Date().toISOString(),
  };
}

export async function sendMessage(req: ChatRequest): Promise<ChatResponse> {
  if (useMockFallback) {
    return mockChat(req);
  }
  try {
    return await realChat(req);
  } catch (err) {
    // The backend is not implemented in this frontend-only build.
    // Fall back to a realistic mock so the dashboard is fully usable.
    useMockFallback = true;
    return mockChat(req);
  }
}

export async function fetchAgents(): Promise<Agent[]> {
  try {
    const res = await fetch(`${API_BASE}/agents`);
    if (!res.ok) throw new Error(`agents failed (${res.status})`);
    const data = (await res.json()) as { agents: Agent[] };
    return data.agents;
  } catch {
    return AGENTS;
  }
}

export function createSessionId(): string {
  return uid("sess");
}

export function createMessageId(): string {
  return uid("msg");
}
