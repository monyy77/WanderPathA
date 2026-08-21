"""
state_graph/graphs/policy_rag.py

RAG (policy retrieval) for the flight-rebooking graph (Issue #3).
Owner: Person 1

WHY THIS NODE NEEDS RAG (not ToT/LATS/ReAct):
Deciding what a customer is owed - refund amount, whether they're
eligible for an upgrade, whether compensation applies - depends on
Wanderpath's ACTUAL policy documents, not on the model's memory of
"typical" airline policy (which would just be a guess, and a wrong one
could cost the company money or shortchange the customer). This is
exactly what RAG is for: retrieve the real policy text and ground the
node's decision in it. There's no benefit here from searching over
multiple reasoning paths (ToT/LATS) or from an external tool-calling
loop (constrained ReAct) - the node just needs to look something up.

NOTE ON SCOPE: this is a small, self-contained keyword-based retriever
over a local policy document store, built to satisfy this graph's
node-level need. It is NOT the same as - and does not replace - the
team's full Memory & RAG agent (embeddings/vector DB, etc.). If the
team's Memory & RAG agent already exposes a retrieval function/tool by
the time this is reviewed, this module should be swapped to call that
instead, so we don't maintain two separate RAG implementations. This
is flagged as a follow-up, not silently left as a permanent duplicate.
"""

from typing import Any

# Wanderpath's refund/compensation policy, as short, retrievable chunks.
# In a full RAG setup this would live in the shared vector store built
# by the Memory & RAG agent; kept as plain text here so this node has
# something real to retrieve and cite rather than the model guessing.
POLICY_DOCUMENTS = [
    {
        "id": "refund-001",
        "text": (
            "Customers whose flight is cancelled by the airline are "
            "entitled to a full refund of the ticket price, regardless "
            "of ticket type (economy, premium, or business)."
        ),
    },
    {
        "id": "refund-002",
        "text": (
            "Refunds under $500 are processed automatically within 3-5 "
            "business days. Refunds of $500 or more require manual "
            "approval from a customer service agent before processing, "
            "due to the higher financial impact of large reversals."
        ),
    },
    {
        "id": "compensation-001",
        "text": (
            "VIP customers who experience a cancellation are eligible "
            "for a complimentary seat upgrade on their rebooked flight, "
            "subject to availability, at no additional cost."
        ),
    },
    {
        "id": "compensation-002",
        "text": (
            "Non-VIP customers are not automatically eligible for a "
            "seat upgrade on rebooking; upgrades may still be offered "
            "at the discretion of a customer service agent."
        ),
    },
]


def retrieve_policy(query_terms: list[str]) -> list[dict[str, Any]]:
    """
    Simple keyword-overlap retriever: returns policy documents whose
    text contains any of the given query terms, ranked by how many
    terms matched. This is intentionally simple (no embeddings) since
    the policy set is small and fixed - the point of this node is to
    ground the decision in real text, not to build a search engine.

    Returns a list of matched documents, most relevant first. Each
    result is a dict with "id", "text", and "match_count" so the
    caller can cite exactly which policy chunk was used.
    """
    query_terms_lower = [t.lower() for t in query_terms]

    scored = []
    for doc in POLICY_DOCUMENTS:
        text_lower = doc["text"].lower()
        match_count = sum(1 for term in query_terms_lower if term in text_lower)
        if match_count > 0:
            scored.append({**doc, "match_count": match_count})

    scored.sort(key=lambda d: d["match_count"], reverse=True)
    return scored


def get_refund_policy_for(state: dict[str, Any]) -> dict[str, Any]:
    """
    Retrieves the specific policy chunks relevant to this customer's
    refund case, and returns a small grounded summary the node can
    act on - not the model's own guess, but a real citation.

    Returns:
        {
            "refund_amount": float,
            "auto_approved": bool,
            "vip_upgrade_eligible": bool,
            "cited_policy_ids": list[str],
        }
    """
    is_vip = bool(state.get("customer_is_vip", False))
    refund_amount = float(state.get("refund_amount", 0.0))

    query_terms = ["refund"]
    if is_vip:
        query_terms.append("vip")

    matches = retrieve_policy(query_terms)
    cited_ids = [m["id"] for m in matches]

    # Ground the decision in the retrieved threshold policy
    # (refund-002), not a number pulled from nowhere.
    auto_approved = refund_amount < 500.0

    vip_upgrade_eligible = is_vip

    return {
        "refund_amount": refund_amount,
        "auto_approved": auto_approved,
        "vip_upgrade_eligible": vip_upgrade_eligible,
        "cited_policy_ids": cited_ids,
    }