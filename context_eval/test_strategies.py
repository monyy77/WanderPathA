from langchain.messages import AIMessage, HumanMessage, SystemMessage
from Context_eval.context_strategies import (
    sliding_window,
    observation_masking,
    recursive_summarization,
    zone_based_pruning,
)


def test_sliding_window():
    messages = [HumanMessage(content=f"Message {i}") for i in range(20)]
    result = sliding_window(messages, 5)
    assert len(result) == 5
    assert result[-1].content == "Message 19"


def test_observation_masking_keeps_recent_masks_old():
    messages = [
        HumanMessage(content="Observation from tool_a: old result"),
        HumanMessage(content="Observation from tool_b: newer result"),
        HumanMessage(content="Observation from tool_c: newest result"),
    ]
    result = observation_masking(messages, keep_recent_observations=2)
    assert "[Tool output masked" in result[0].content
    assert result[1].content == "Observation from tool_b: newer result"
    assert result[2].content == "Observation from tool_c: newest result"


def test_recursive_summarization_compresses_and_keeps_facts():
    old = [
        HumanMessage(content="Customer: my passport expires in 3 months."),
        *[
            HumanMessage(content=f"Observation from check_visa: option {i}")
            for i in range(10)
        ],
    ]
    recent = [HumanMessage(content=f"Message {i}") for i in range(5)]
    result = recursive_summarization(old + recent, max_recent=5, chunk_size=6)

    assert len(result) == 6  # 1 summary message + 5 recent
    assert "passport" in result[0].content
    assert "3 months" in result[0].content


def test_zone_based_pruning_protects_customer_message_from_reasoning_noise():
    messages = [
        SystemMessage(content="system prompt"),
        HumanMessage(content="Customer: my budget is 10000 EGP."),
    ]
    # A long run of agent reasoning + tool noise that used to crowd the
    # customer's original message out of the "conversation" window.
    for i in range(15):
        messages.append(AIMessage(content=f"Thought: step {i}\nAction: check_x"))
        messages.append(HumanMessage(content=f"Observation from check_x: result {i}"))
    messages.append(HumanMessage(content="Customer: which option is best?"))

    result = zone_based_pruning(messages, keep_recent_conversation=6)

    assert result[0].content == "system prompt"
    text = " ".join(str(m.content) for m in result)
    assert "10000" in text  # the original customer statement survived


def test_all_four_strategies_run():
    messages = [HumanMessage(content=f"Message {i}") for i in range(20)]

    assert len(sliding_window(messages, 5)) == 5
    assert len(observation_masking(messages)) == len(messages)
    assert len(recursive_summarization(messages, max_recent=5, chunk_size=6)) <= 6
    assert len(zone_based_pruning(messages, keep_recent_conversation=5)) == 5

    print("All four strategies passed!")


if __name__ == "__main__":
    test_sliding_window()
    test_observation_masking_keeps_recent_masks_old()
    test_recursive_summarization_compresses_and_keeps_facts()
    test_zone_based_pruning_protects_customer_message_from_reasoning_noise()
    test_all_four_strategies_run()
    print("All tests passed!")
