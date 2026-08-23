"""
Maps MCP capabilities
to local executors.
"""


CAPABILITY_MAP = {


    "planning_agent":
        "planning",



    "memory_agent":
        "memory",



    "flight_rebooking_graph":
        "flight",



    "refund_graph":
        "refund",



    "vip_graph":
        "vip",

}



def capability_to_agent(
        capability
):

    return CAPABILITY_MAP.get(
        capability
    )
