"""
WanderPathA Agent Router

Central routing layer between User Platform
and autonomous agents / state graphs.
"""


from planning.planning_agent import run_planning_agent


# Memory Agent
try:
    from agent.agent import run_agent
except Exception:
    run_agent = None


# Flight Graph
try:
    from state_graph.graphs.flight_rebooking import (
        run_flight_rebooking_graph
    )
except Exception:
    run_flight_rebooking_graph = None


# Refund Graph
try:
    from state_graph.graphs.refund import (
        run_refund_graph
    )
except Exception:
    run_refund_graph = None


# VIP Graph
try:
    from state_graph.graphs.vip import (
        run_vip_graph
    )
except Exception:
    run_vip_graph = None



class AgentRouter:
    """
    Routes requests to the correct autonomous component.
    """


    def __init__(self):

        self.agents = {

            "planning":
                self.run_planning,

            "memory":
                self.run_memory,

            "flight":
                self.run_flight,

            "refund":
                self.run_refund,

            "vip":
                self.run_vip,
        }



    def route(self, request: dict):
        """
        Main entry point.

        Expected:

        {
            "agent": "planning",
            "message": "...",
            "session_id": "...",
            "customer_id": "..."
        }

        """

        agent_id = request.get(
            "agent",
            "planning"
        )


        if agent_id not in self.agents:

            raise ValueError(
                f"Unknown agent: {agent_id}"
            )


        return self.agents[agent_id](
            request
        )



    # -------------------------------------------------
    # Planning Agent
    # -------------------------------------------------

    def run_planning(self, request):

        result = run_planning_agent(
            request["message"]
        )


        return {

            "agent": "planning",

            "status": "success",

            "result": result,
        }



    # -------------------------------------------------
    # Memory Agent
    # -------------------------------------------------

    def run_memory(self, request):

        if run_agent is None:

            raise RuntimeError(
                "Memory Agent is not available"
            )


        result = run_agent(
            request["message"]
        )


        return {

            "agent": "memory",

            "status": "success",

            "result": result,
        }



    # -------------------------------------------------
    # Flight Graph
    # -------------------------------------------------

    def run_flight(self, request):

        if run_flight_rebooking_graph is None:

            raise RuntimeError(
                "Flight Graph is not available"
            )


        result = run_flight_rebooking_graph(
            request
        )


        return {

            "agent": "flight",

            "status": "success",

            "result": result,
        }



    # -------------------------------------------------
    # Refund Graph
    # -------------------------------------------------

    def run_refund(self, request):

        if run_refund_graph is None:

            raise RuntimeError(
                "Refund Graph is not available"
            )


        result = run_refund_graph(
            request
        )


        return {

            "agent": "refund",

            "status": "success",

            "result": result,
        }



    # -------------------------------------------------
    # VIP Graph
    # -------------------------------------------------

    def run_vip(self, request):

        if run_vip_graph is None:

            raise RuntimeError(
                "VIP Graph is not available"
            )


        result = run_vip_graph(
            request
        )


        return {

            "agent": "vip",

            "status": "success",

            "result": result,
        }
