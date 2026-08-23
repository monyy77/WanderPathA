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
from rag.self_rag import self_rag
from rag.self_rag import self_rag_with_sources
from rag.hybrid_rag import hybrid_retrieve
# Wanderpath's refund/compensation policy, as short, retrievable chunks.
# In a full RAG setup this would live in the shared vector store built
# by the Memory & RAG agent; kept as plain text here so this node has
# something real to retrieve  rather than the model guessing.

def get_refund_policy_for(state: dict[str, Any]) -> dict[str, Any]:

    is_vip = bool(state.get("customer_is_vip", False))
    refund_amount = float(state.get("refund_amount", 0.0))

    question = f"""
    Determine the refund policy for this customer case.

    Refund amount: {refund_amount}
    Customer VIP: {is_vip}

    Identify:
    1. Whether the refund requires human approval.
    2. Whether the customer is eligible for compensation or upgrade.
    3. Which policy documents support the decision.
    """

    rag_result = self_rag_with_sources(question)

    documents = rag_result["documents"]

    cited_policy_ids = []

    for doc in documents:
        # لو metadata متاحة
        if isinstance(doc, dict):
            source = doc.get("source") or doc.get("id")
            if source:
                cited_policy_ids.append(source)

    return {
        "refund_amount": refund_amount,
        "auto_approved": refund_amount < 500.0,
        "vip_upgrade_eligible": is_vip,
        "cited_policy_ids": cited_policy_ids,
        "policy_answer": rag_result["answer"],
        "retrieved_documents": documents,
    }