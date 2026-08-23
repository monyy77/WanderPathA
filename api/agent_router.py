"""
WanderPathA Agent Router

Intelligent routing layer.

User message
      |
Classifier
      |
Agent selection
      |
Execution
"""

from planning.planning_agent import run_planning_agent


# Optional imports
try:
    from agent.agent import run_agent
except Exception:
    run_agent = None


try:
    from state_graph.graphs.flight_rebooking import (
        run_flight_rebooking_graph
    )
except Exception:
    run_flight_rebooking_graph = None


try:
    from state_graph.graphs.refund import (
        run_refund_graph
    )
except Exception:
    run_refund_graph = None


try:
    from state_graph.graphs.vip import (
        run_vip_graph
    )
except Exception:
    run_vip_graph = None



class AgentRouter:


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



    # =================================================
    # Main Router
    # =================================================

    def route(self, request: dict):


        message = request.get(
            "message",
            ""
        )


        # Intelligent Classification

        agent_id = self.classify(
            message
        )


        return self.agents[agent_id](
            request
        )



    # =================================================
    # Classifier
    # =================================================

    def classify(self, message: str):


        text = message.lower()



        # -------------------------------
        # Memory
        # -------------------------------

        memory_keywords = [

            "remember",
            "forget",
            "my preference",
            "preferred",
            "usually",
            "save my",
        ]


        if any(
            word in text
            for word in memory_keywords
        ):

            return "memory"



        # -------------------------------
        # Refund
        # -------------------------------

        refund_keywords = [

            "refund",
            "money back",
            "compensation",
            "reimbursement",
        ]


        if any(
            word in text
            for word in refund_keywords
        ):

            return "refund"



        # -------------------------------
        # Flight
        # -------------------------------

        flight_keywords = [

            "flight",
            "cancelled",
            "canceled",
            "delayed",
            "rebook",
            "reschedule",
        ]


        if any(
            word in text
            for word in flight_keywords
        ):

            return "flight"



        # -------------------------------
        # VIP
        # -------------------------------

        vip_keywords = [

            "vip",
            "upgrade",
            "business class",
            "luxury",
            "premium",
        ]


        if any(
            word in text
            for word in vip_keywords
        ):

            return "vip"



        # -------------------------------
        # Default
        # -------------------------------

        return "planning"



    # =================================================
    # Agents
    # =================================================


    def run_planning(self, request):

        result = run_planning_agent(
            request["message"]
        )

        return {

            "agent": "planning",

            "status": "success",

            "result": result,
        }



    def run_memory(self, request):

        if run_agent is None:

            raise RuntimeError(
                "Memory Agent unavailable"
            )


        result = run_agent(
            request["message"]
        )


        return {

            "agent": "memory",

            "status": "success",

            "result": result,
        }



    def run_flight(self, request):

        if run_flight_rebooking_graph is None:

            raise RuntimeError(
                "Flight Graph unavailable"
            )


        result = run_flight_rebooking_graph(
            request
        )


        return {

            "agent": "flight",

            "status": "success",

            "result": result,
        }



    def run_refund(self, request):

        if run_refund_graph is None:

            raise RuntimeError(
                "Refund Graph unavailable"
            )


        result = run_refund_graph(
            request
        )


        return {

            "agent": "refund",

            "status": "success",

            "result": result,
        }



    def run_vip(self, request):

        if run_vip_graph is None:

            raise RuntimeError(
                "VIP Graph unavailable"
            )


        result = run_vip_graph(
            request
        )


        return {

            "agent": "vip",

            "status": "success",

            "result": result,
        }
