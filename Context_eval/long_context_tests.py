from langchain.messages import AIMessage, HumanMessage

def _tool_step(action: str, detail: str, i: int):
    """One realistic agent step: an AIMessage (thought/action) followed
    by a HumanMessage (observation) — matching the exact shape agent.py
    actually produces in the transcript.
    """
    return [
        AIMessage(
            content=(
                f"Thought: checking {action} option #{i}\n"
                f"Action: {action}\nInput: {{'query_index': {i}}}"
            )
        ),
        HumanMessage(
            content=f"Observation from {action}: {detail} (result #{i})",
        ),
    ]

def _tool_noise(action: str, detail: str, count: int):
    noise = []
    for i in range(1, count + 1):
        noise.extend(_tool_step(action, detail, i))
    return noise


LONG_CONTEXT_TESTS = [
    # --- Decision at the very start (baseline / easy case) ---
    {
        "name": "wheelchair_requirement",
        "conversation": [
            HumanMessage(
                content=(
                    "Customer: I want to book a family trip to Hurghada. "
                    "One traveler uses a wheelchair and requires "
                    "wheelchair-accessible hotel facilities and transport."
                )
            ),
            *_tool_noise("check_hotel_availability", "hotel option checked", 12),
            *_tool_noise("check_transport_options", "transport option checked", 10),
            HumanMessage(
                content="Customer: Based on everything we checked, which option should I choose?"
            ),
        ],
        "expected": ["wheelchair"],
    },
    {
        "name": "budget_constraint",
        "conversation": [
            HumanMessage(
                content="Customer: I want to travel to Sharm El Sheikh. My maximum total budget is 30000 EGP."
            ),
            *_tool_noise("check_package_price", "package price checked", 12),
            *_tool_noise("check_flight_availability", "flight option checked", 10),
            HumanMessage(
                content="Customer: Based on the options you found, which package should I choose?"
            ),
        ],
        "expected": ["30000"],
    },
    {
        "name": "passport_requirement",
        "conversation": [
            HumanMessage(
                content="Customer: I am planning an international trip. My passport expires in 4 months."
            ),
            *_tool_noise("check_visa_requirements", "visa requirement checked", 12),
            *_tool_noise("check_flight_availability", "flight option checked", 10),
            HumanMessage(content="Customer: Can I proceed with the booking?"),
        ],
        "expected": ["passport", "4 months"],
    },
    # --- Decision buried in the MIDDLE of a multi-leg modification ---
    # This is the realistic WanderPath case from issue #30: a multi-city
    # booking change where the customer's preference gets stated partway
    # through, then buried under tool noise for the *remaining* legs.
    {
        "name": "refund_preference_buried_mid",
        "conversation": [
            HumanMessage(
                content=(
                    "Customer: I need to modify my Cairo-Istanbul-Rome trip, "
                    "booking WPT-4471. Let's start with the Istanbul leg."
                )
            ),
            *_tool_noise("get_booking_details", "Istanbul leg details fetched", 4),
            *_tool_noise("check_change_fee", "Istanbul leg change fee checked", 4),
            HumanMessage(
                content=(
                    "Customer: OK, cancel the Istanbul hotel night. For any refund "
                    "on this trip, I want it as a travel voucher, not cash."
                )
            ),
            *_tool_noise("check_hotel_availability", "Rome leg hotel option checked", 10),
            *_tool_noise("check_flight_availability", "Rome leg flight option checked", 10),
            *_tool_noise("check_refund_policy", "refund policy clause checked", 6),
            HumanMessage(
                content="Customer: Alright, go ahead and finalize all the changes we discussed."
            ),
        ],
        "expected": ["voucher"],
    },
    {
        "name": "conditional_change_threshold_buried_mid",
        "conversation": [
            HumanMessage(
                content=(
                    "Customer: I have a 3-city booking WPT-5820 and want to see if "
                    "cheaper flights exist for each leg."
                )
            ),
            *_tool_noise("check_flight_availability", "Cairo leg flight option checked", 6),
            HumanMessage(
                content=(
                    "Customer: Only go ahead and change a leg if the fare difference "
                    "is under 50 USD — otherwise leave it as booked."
                )
            ),
            *_tool_noise("check_flight_availability", "Istanbul leg flight option checked", 10),
            *_tool_noise("check_change_fee", "Istanbul leg change fee checked", 6),
            *_tool_noise("check_flight_availability", "Rome leg flight option checked", 10),
            HumanMessage(
                content="Customer: Go ahead and apply whatever changes make sense."
            ),
        ],
        "expected": ["50"],
    },
]
