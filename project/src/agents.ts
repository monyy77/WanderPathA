import type { Agent, AgentId } from "./types";

export const AGENTS: Agent[] = [
  {
    id: "memory",
    name: "Memory Agent",
    tagline: "Remembers every detail of your journey",
    description:
      "Stores your preferences, past trips, and profile context so every other agent knows you better.",
    icon: "brain",
    accent: "indigo",
  },
  {
    id: "planning",
    name: "Planning Agent",
    tagline: "Crafts full day-by-day itineraries",
    description:
      "Turns a destination and a timeframe into a balanced, bookable trip plan with activities and timing.",
    icon: "map",
    accent: "sky",
  },
  {
    id: "flight",
    name: "Flight Agent",
    tagline: "Searches, compares, and books flights",
    description:
      "Finds the best routes and fares across carriers, presents clear options, and can initiate booking.",
    icon: "plane",
    accent: "violet",
  },
  {
    id: "refund",
    name: "Refund Agent",
    tagline: "Handles cancellations and refunds",
    description:
      "Reviews eligibility, walks you through policy, and processes refund or cancellation requests.",
    icon: "rotate-ccw",
    accent: "rose",
  },
  {
    id: "vip",
    name: "VIP Agent",
    tagline: "Concierge upgrades and exclusive perks",
    description:
      "Unlocks suite upgrades, lounge access, private transfers, and curated experiences for members.",
    icon: "crown",
    accent: "amber",
  },
];

export function getAgent(id: AgentId): Agent {
  const found = AGENTS.find((a) => a.id === id);
  if (!found) throw new Error(`Unknown agent: ${id}`);
  return found;
}
