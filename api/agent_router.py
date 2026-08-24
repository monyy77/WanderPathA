"""
WanderPathA Agent Router

Dynamic MCP Runtime Router

User Message
      |
      v
LLM Router
      |
      v
MCP Runtime Tools Discovery
      |
      v
Capability Validation
      |
      v
Dynamic MCP Tool Calling
      |
      v
WanderPath MCP Server


Execution:

Planning -> Internal Agent
Memory   -> Internal Agent
Others   -> MCP Tools
"""


from planning.planning_agent import run_planning_agent


from api.llm_router import LLMRouter


from api.mcp_validator import (
    MCPCapabilityValidator
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


        # -----------------------------------------
        # MCP Runtime Registry
        # -----------------------------------------

        self.mcp_registry = mcp_registry



        # -----------------------------------------
        # MCP Capability Validator
        # -----------------------------------------

        self.capability_validator = (
            MCPCapabilityValidator(
                mcp_registry
            )
        )



        # -----------------------------------------
        # LLM Router
        # -----------------------------------------

        self.llm_router = LLMRouter(

            llm,

            mcp_registry

        )








    # =================================================
    # Main Router
    # =================================================


    async def route(
        self,
        request: dict
    ):



        capability = await self.classify(

            request.get(
                "message",
                ""
            )

        )



        return await self.execute_capability(

            capability,

            request

        )








    # =================================================
    # Capability Classification
    # =================================================


    async def classify(
        self,
        message: str
    ):



        capability = await (

            self.llm_router

            .classify(

                message

            )

        )



        if capability:



            is_valid = await (

                self.capability_validator

                .is_valid_capability(

                    capability

                )

            )



            if is_valid:

                return capability






        # fallback

        return self.keyword_fallback(

            message

        )









    # =================================================
    # Dynamic MCP Execution
    # =================================================


    async def execute_capability(
        self,
        capability,
        request
    ):



        if self.mcp_registry is None:


            raise RuntimeError(

                "MCP Registry unavailable"

            )



        return await (

            self.mcp_registry

            .mcp_client

            .call_tool(

                capability,

                request

            )

        )









    # =================================================
    # Keyword Fallback
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


            return (
                "refund_with_confirmation"
            )






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


            return (
                "rebook_flight"
            )







        if any(

            word in text

            for word in [

                "vip",
                "upgrade",
                "premium",
                "business"

            ]

        ):


            return (
                "upgrade_to_vip"
            )






        if any(

            word in text

            for word in [

                "remember",
                "forget",
                "preference",
                "save"

            ]

        ):


            return (
                "memory_agent"
            )






        return (
            "planning_agent"
        )









    # =================================================
    # Internal Planning Agent
    # =================================================


    async def run_planning(
        self,
        request
    ):



        result = run_planning_agent(

            request["message"]

        )



        return {


            "tool":

                "planning_agent",


            "status":

                "success",


            "result":

                result

        }









    # =================================================
    # Internal Memory Agent
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


            "tool":

                "memory_agent",


            "status":

                "success",


            "result":

                result

        }
