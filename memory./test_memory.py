from langchain.messages import AIMessage, HumanMessage
from memory.scratchpad import ShortTermMemory, process_customer_message
from Context_eval.context_strategies import sliding_window


def test_memory():
    memory = ShortTermMemory()

    memory.add(HumanMessage(content="I need an accessible hotel."))
    memory.add(AIMessage(content="I'll look for suitable hotels."))

    memory.update_scratchpad(
        plan="Find an accessible hotel",
        current_subgoal="Search available hotels",
    )

    messages = memory.get_messages()
    scratchpad = memory.get_scratchpad()

    assert len(messages) == 2
    assert scratchpad.plan == "Find an accessible hotel"
    assert scratchpad.current_subgoal == "Search available hotels"

    print("Memory test passed!")


def test_process_customer_message_pins_high_stakes_facts():
    memory = ShortTermMemory()

    process_customer_message(
        memory, "One traveler uses a wheelchair.", turn=1
    )
    process_customer_message(
        memory, "My budget is 20000 EGP max.", turn=2
    )
    process_customer_message(memory, "ok great, thanks!", turn=3)

    facts = [pf.fact for pf in memory.scratchpad.pinned_facts]
    assert any("wheelchair" in f.lower() for f in facts)
    assert any("20000" in f for f in facts)
    assert len(facts) == 2  # the "ok great, thanks!" turn pinned nothing

    print("Fact-pinning test passed!")


def test_scratchpad_survives_transcript_pruning():
    """The whole point of keeping the scratchpad separate: no matter how
    aggressively the rolling buffer gets pruned, the scratchpad must be
    untouched.
    """
    memory = ShortTermMemory()
    memory.update_scratchpad(plan="Modify booking WPT-4471")
    process_customer_message(
        memory, "Refund as a voucher please, not cash.", turn=1
    )

    for i in range(30):
        memory.add(HumanMessage(content=f"Observation from tool: noise {i}"))

    # Prune the transcript hard.
    pruned = sliding_window(memory.get_messages(), max_messages=3)
    assert len(pruned) == 3

    # The scratchpad was never passed into sliding_window at all, so it
    # can't have been touched — but assert it explicitly to make the
    # isolation guarantee a real, checked test rather than an assumption.
    assert memory.scratchpad.plan == "Modify booking WPT-4471"
    assert any("voucher" in pf.fact for pf in memory.scratchpad.pinned_facts)

    print("Scratchpad isolation test passed!")


if __name__ == "__main__":
    test_memory()
    test_process_customer_message_pins_high_stakes_facts()
    test_scratchpad_survives_transcript_pruning()
    print("All memory tests passed!")
