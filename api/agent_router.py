"""
Agent Router

Responsible for routing user requests
to the correct autonomous agent.
"""


from planning.planning_agent import run_planning_agent


class AgentRouter:
    """
    Central router for all WanderPath agents.
    """


    def __init__(self):
        self.agents = {
            "planning": self.run_planning,
        }


    def route(self, request: dict):
        """
        Main entry point.

        request example:

        {
            "agent": "planning",
            "message": "Rebook my delayed flight"
        }

        """

        agent_name = request.get(
            "agent",
            "planning"
        )

        if agent_name not in self.agents:
            raise ValueError(
                f"Unknown agent: {agent_name}"
            )

        return self.agents[agent_name](request)



    def run_planning(self, request: dict):
        """
        Execute Planning Agent.
        """

        user_message = request.get(
            "message"
        )

        if not user_message:
            raise ValueError(
                "Missing user message"
            )


        result = run_planning_agent(
            user_message
        )


        return {
            "agent": "planning",
            "status": "success",
            "result": result
        }
