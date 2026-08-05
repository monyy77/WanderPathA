from langchain.messages import HumanMessage, AIMessage
from Context_eval.memory import ShortTermMemory

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


if __name__ == "__main__":
    test_memory()
