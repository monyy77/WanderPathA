"""
WanderPathA Agent Router

Intelligent routing layer.

User message
      |
      v
LLM Router
      |
      v
MCP Capability
      |
      v
Capability Mapper
      |
      v
Agent Validation
      |
      v
Fallback Keyword Router (if needed)
      |
      v
Agent execution
"""


from planning.planning_agent import run_planning_agent


from api.llm_router import LLMRouter

from api.agent_registry import (
    is_allowed_agent
)

from api.capability_mapper import (
    capability_to_agent
)



# -------------------------------------------------
# Optional Imports
# -------------------------------------------------

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



    def __init__(self, llm=None):


        # -----------------------------------------
        # MCP-aware LLM Router
        # -----------------------------------------

        self.llm_router = LLMRouter(
            llm
        )



        # -----------------------------------------
        # Available execution routes
        # -----------------------------------------

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



        agent_id = self.classify(
            message
        )



        # Final safety validation

        if not is_allowed_agent(
            agent_id
        ):

            agent_id = "planning"



        return self.agents[agent_id](
            request
        )






    # =================================================
    # Intelligent Classifier
    # =================================================


    def classify(self, message: str):


        # -----------------------------------------
        # First: MCP + LLM Routing
        # -----------------------------------------

        capability = (

            self.llm_router
            .classify(message)

        )



        if capability:


            agent = capability_to_agent(
                capability
            )



            if (

                agent

                and

                is_allowed_agent(agent)

            ):

                return agent






        # -----------------------------------------
        # Second: Fallback Router
        # -----------------------------------------

        return self.keyword_fallback(
            message
        )








    # =================================================
    # Keyword Fallback
    # =================================================


    def keyword_fallback(self, message):


        text = message.lower()



        # -------------------------------
        # Refund
        # -------------------------------

        if any(

            word in text

            for word in [

                "refund",

                "compensation",

                "money back",

                "reimbursement",

            ]

        ):

            return "refund"






        # -------------------------------
        # Flight
        # -------------------------------

        if any(

            word in text

            for word in [

                "flight",

                "cancelled",

                "canceled",

                "delayed",

                "rebook",

                "reschedule",

            ]

        ):

            return "flight"






        # -------------------------------
        # Memory
        # -------------------------------

        if any(

            word in text

            for word in [

                "remember",

                "forget",

                "preference",

                "prefer",

                "save my",

            ]

        ):

            return "memory"






        # -------------------------------
        # VIP
        # -------------------------------

        if any(

            word in text

            for word in [

                "vip",

                "upgrade",

                "business class",

                "luxury",

                "premium",

            ]

        ):

            return "vip"






        # Default

        return "planning"









    # =================================================
    # Planning Agent
    # =================================================


    def run_planning(self, request):


        result = run_planning_agent(

            request["message"]

        )



        return {


            "agent":

                "planning",



            "status":

                "success",



            "result":

                result,

        }









    # =================================================
    # Memory Agent
    # =================================================


    def run_memory(self, request):


        if run_agent is None:


            raise RuntimeError(

                "Memory Agent unavailable"

            )



        result = run_agent(

            request["message"]

        )



        return {


            "agent":

                "memory",



            "status":

                "success",



            "result":

                result,

        }









    # =================================================
    # Flight Graph
    # =================================================


    def run_flight(self, request):


        if run_flight_rebooking_graph is None:


            raise RuntimeError(

                "Flight Graph unavailable"

            )



        result = run_flight_rebooking_graph(

            request

        )



        return {


            "agent":

                "flight",



            "status":

                "success",



            "result":

                result,

        }









    # =================================================
    # Refund Graph
    # =================================================


    def run_refund(self, request):


        if run_refund_graph is None:


            raise RuntimeError(

                "Refund Graph unavailable"

            )



        result = run_refund_graph(

            request

        )



        return {


            "agent":

                "refund",



            "status":

                "success",



            "result":

                result,

        }









    # =================================================
    # VIP Graph
    # =================================================


    def run_vip(self, request):


        if run_vip_graph is None:


            raise RuntimeError(

                "VIP Graph unavailable"

            )



        result = run_vip_graph(

            request

        )



        return {


            "agent":

                "vip",



            "status":

                "success",



            "result":

                result,

        }
