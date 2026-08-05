from langchain.messages import HumanMessage
from Context_eval.context_strategies import (
    sliding_window,
    observation_masking,
    recursive_summarization,
    zone_based_pruning,
)
messages = [
    HumanMessage(content=f"Message {i}")
    for i in range(20)
]

def test_strategies():
    
    result = sliding_window(messages, 5)
    assert len(result) == 5

    result = observation_masking(
        messages + [HumanMessage(content="Observation from tool: booking data")]
    )
    assert "[Tool output masked]" in result[-1].content

    result = recursive_summarization(messages, 5)
    assert len(result) <= 6

    result = zone_based_pruning(messages, 5)
    assert len(result) == 5

    print("All four strategies passed!")
    

if __name__ == "__main__":
    test_strategies()
