"""
Agent Registry

Single source of truth for available agents.
Prevents hallucinated routing.
"""


AVAILABLE_AGENTS = {

    "planning": {
        "description":
            "Task decomposition and travel planning",
        "type":
            "planning_agent",
    },


    "memory": {
        "description":
            "Customer memory and preferences",
        "type":
            "memory_agent",
    },


    "flight": {
        "description":
            "Flight rebooking and flight disruption workflows",
        "type":
            "state_graph",
    },


    "refund": {
        "description":
            "Refund and compensation workflows",
        "type":
            "state_graph",
    },


    "vip": {
        "description":
            "VIP travel customization workflows",
        "type":
            "state_graph",
    },

}



def is_allowed_agent(agent_id: str):

    return agent_id in AVAILABLE_AGENTS



def get_agents_description():

    return "\n".join(

        [
            f"{key}: {value['description']}"
            for key, value
            in AVAILABLE_AGENTS.items()
        ]

    )
