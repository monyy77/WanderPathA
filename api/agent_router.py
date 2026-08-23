def route_agent(agent_id, message):

    if agent_id == "planning":
        return planning_agent(message)

    elif agent_id == "refund":
        return refund_agent(message)

    elif agent_id == "flight":
        return flight_agent(message)

    elif agent_id == "vip":
        return vip_agent(message)

    elif agent_id == "memory":
        return memory_agent(message)

    else:
        raise ValueError("Unknown agent")
