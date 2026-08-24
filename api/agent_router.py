"""
WanderPathA Agent Router

Intelligent routing layer.

User Message
      |
      v
LLM Router
      |
      v
MCP Runtime Capabilities
      |
      v
Capability Mapper
      |
      v
Agent Validation
      |
      v
Agent Execution

Execution:
    Planning -> Planning Agent
    Memory   -> Memory Agent
    Flight   -> MCP Tool Calling
    Refund   -> MCP Tool Calling
    VIP      -> MCP Tool Calling
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
# Optional Memory Agent
# -------------------------------------------------

try:

    from agent.agent import run_agent

except Exception:

    run_agent = None





class AgentRouter:



    def __init__(
        self,
        llm=None,
        mcp_registry=None
    ):


        # MCP Registry
        # Runtime discovered tools

        self.mcp_registry = mcp_registry



        # LLM Router

        self.llm_router = LLMRouter(

            llm,

            mcp_registry

        )



        # Available Routes

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


    async def route(
        self,
        request: dict
    ):


        message = request.get(
            "message",
            ""
        )


        agent_id = await self.classify(
            message
        )



        if not is_allowed_agent(
            agent_id
        ):

            agent_id = "planning"



        return await self.agents[agent_id](
            request
        )






    # =================================================
    # LLM Classification
    # =================================================


    async def classify(
        self,
        message: str
    ):


        capability = await self.llm_router.classify(
            message
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





        return self.keyword_fallback(
            message
        )






    # =================================================
    # Fallback Router
    # =================================================


    def keyword_fallback(
        self,
        message
    ):


        text = message.lower()



        if any(

            word in text

            for word in [

                "refund",
                "compensation",
                "money back",
                "reimbursement"

            ]

        ):

            return "refund"




        if any(

            word in text

            for word in [

                "flight",
                "cancelled",
                "canceled",
                "delayed",
                "rebook",
                "reschedule"

            ]

        ):

            return "flight"




        if any(

            word in text

            for word in [

                "remember",
                "forget",
                "preference",
                "prefer",
                "save"

            ]

        ):

            return "memory"




        if any(

            word in text

            for word in [

                "vip",
                "upgrade",
                "business",
                "premium"

            ]

        ):

            return "vip"



        return "planning"






    # =================================================
    # Planning Agent
    # =================================================


    async def run_planning(
        self,
        request
    ):


        result = run_planning_agent(

            request["message"]

        )



        return {


            "agent":

                "planning",


            "status":

                "success",


            "result":

                result

        }







    # =================================================
    # Memory Agent
    # =================================================


    async def run_memory(
        self,
        request
    ):


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

                result

        }







    # =================================================
    # Flight MCP Execution
    # =================================================


    async def run_flight(
        self,
        request
    ):


        if self.mcp_registry is None:

            raise RuntimeError(
                "MCP Registry unavailable"
            )



        result = await self.mcp_registry.mcp_client.call_tool(

            "rebook_flight",

            {

                "message":

                    request["message"],


                "customer_id":

                    request.get(
                        "customer_id"
                    )

            }

        )



        return {


            "agent":

                "flight",


            "status":

                "success",


            "result":

                result

        }







    # =================================================
    # Refund MCP Execution
    # =================================================


    async def run_refund(
        self,
        request
    ):


        if self.mcp_registry is None:

            raise RuntimeError(
                "MCP Registry unavailable"
            )



        result = await self.mcp_registry.mcp_client.call_tool(

            "refund_with_confirmation",

            {


                "booking_id":

                    request.get(
                        "booking_id"
                    )

            }

        )



        return {


            "agent":

                "refund",


            "status":

                "success",


            "result":

                result

        }







    # =================================================
    # VIP MCP Execution
    # =================================================


    async def run_vip(
        self,
        request
    ):


        if self.mcp_registry is None:

            raise RuntimeError(
                "MCP Registry unavailable"
            )



        result = await self.mcp_registry.mcp_client.call_tool(

            "upgrade_to_vip",

            {


                "customer_id":

                    request.get(
                        "customer_id"
                    )

            }

        )



        return {


            "agent":

                "vip",


            "status":

                "success",


            "result":

                result

        }
