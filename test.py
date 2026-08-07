from memory.episodic_memory import EpisodicMemory
from memory.semantic_memory import SemanticMemory
from memory.memory_models import Episode, SemanticFact
from rag.self_rag import self_rag_app, global_episodic, global_semantic, self_rag

from datetime import datetime

def setup_test_data():
    # 1. Populate Episodic Memory
    ep1 = Episode(
        episode_id="ep_001",
        content="User mentioned they felt dizzy during their last flight.",
        entity_type="user",
        entity_id="usr_101",
        source="user_conversation",
        reason="overflow_routing"
    )
    global_episodic.save(ep1)

    # 2. Populate Semantic Memory
    # داخل ملف test.py
    fact1 = SemanticFact(
        fact_id="fact_001",
        predicate="seat_preference",
        value="window",
        entity_type="user",
        entity_id="usr_101",
        version=1,
        valid_from=datetime.now(),
        valid_until=None,
        confidence=1.0
    )
    global_semantic.save(fact1)
def run_test_cases():
    setup_test_data()

    test_queries = [
        # Test Case 1: Grounded in Semantic Memory
        "What is my preferred seat selection when booking a flight?",
        
        # Test Case 2: Grounded in Episodic Memory
        "Did I report any health issues during my recent flight?",
        
        # Test Case 3: Knowledge Base / Policy Document Retrieval
        "What is the standard cancellation policy for international tickets?",
        
        # Test Case 4: Irrelevant Query (Triggers query transformation / hallucination check)
        "What is the capital of Mars?"
    ]

    print("================ STARTING SELF-RAG TEST SUITE ================\n")
    for idx, query in enumerate(test_queries, 1):
        print(f"--- TEST CASE {idx}: '{query}' ---")
        try:
            response = self_rag(query)
            print(f"FINAL RESPONSE:\n{response}\n")
        except Exception as e:
            print(f"TEST CASE {idx} FAILED: {str(e)}\n")
        print("=" * 62)

if __name__ == "__main__":
    run_test_cases()