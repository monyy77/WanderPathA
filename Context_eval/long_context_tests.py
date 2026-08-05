from langchain.messages import HumanMessage


def make_tool_noise(topic, count=20):
    return [
        HumanMessage(
            content=(
                f"Observation from tool: {topic} result #{i}. "
                "Hotel availability checked, room types compared, "
                "prices verified, cancellation policies reviewed, "
                "transportation options checked, customer ratings collected."
            )
        )
        for i in range(1, count + 1)
    ]


LONG_CONTEXT_TESTS = [
    {
        "name": "wheelchair_requirement",
        "conversation": [
            HumanMessage(
                content=(
                    "Customer: I want to book a family trip to Hurghada. "
                    "One traveler uses a wheelchair and requires wheelchair-accessible "
                    "hotel facilities and transportation."
                )
            ),
            *make_tool_noise("Hurghada hotel search", 25),
            HumanMessage(
                content=(
                    "Customer: Based on everything we checked, which option "
                    "should I choose?"
                )
            ),
        ],
        "expected": ["wheelchair"],
    },
    {
        "name": "budget_constraint",
        "conversation": [
            HumanMessage(
                content=(
                    "Customer: I want to travel to Sharm El Sheikh. "
                    "My maximum total budget is 30000 EGP."
                )
            ),
            *make_tool_noise("Sharm El Sheikh package search", 25),
            HumanMessage(
                content=(
                    "Customer: Based on the options you found, "
                    "which package should I choose?"
                )
            ),
        ],
        "expected": ["30000"],
    },
    {
        "name": "passport_requirement",
        "conversation": [
            HumanMessage(
                content=(
                    "Customer: I am planning an international trip. "
                    "My passport expires in 4 months."
                )
            ),
            *make_tool_noise("international travel search", 25),
            HumanMessage(
                content=(
                    "Customer: Can I proceed with the booking?"
                )
            ),
        ],
        "expected": ["passport", "4 months"],
    },
]
