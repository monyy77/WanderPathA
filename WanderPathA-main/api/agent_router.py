"""
WanderPathA Agent Router

Dynamic MCP Runtime Router

Flow:

User Message
      |
      v
LLM Router
      |
      v
MCP tools/list Discovery
      |
      v
Capability Validation
      |
      v
Tool Schema Validation
      |
      v
Dynamic MCP Tool Calling
      |
      v
WanderPath MCP Server
      |
      v
Database / Response


No static agents.
No static tool mapping.
MCP Server is the source of truth.
"""


from planning.planning_agent import run_planning_agent


from api.llm_router import LLMRouter


from api.mcp_validator import (
    MCPCapabilityValidator
)


from api.tool_validator import (
    MCPToolValidator
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
        # Capability Validator
        #
        # Checks:
        # - tool exists
        # - discovered from MCP
        #
        # -----------------------------------------

        self.capability_validator = (
            MCPCapabilityValidator(
                mcp_registry
            )
        )





        # -----------------------------------------
        # Tool Schema Validator
        #
        # Checks:
        # - arguments
        # - required fields
        # - schema compatibility
        #
        # -----------------------------------------

        self.tool_validator = (
            MCPToolValidator(
                mcp_registry
            )
        )






        # -----------------------------------------
        # LLM Router
        #
        # Uses MCP tools/list
        #
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


            valid = await (

                self.capability_validator

                .is_valid_capability(

                    capability

                )

            )



            if valid:

                return capability







        # fallback only if LLM fails

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





        # -----------------------------------------
        # Validate tool exists + arguments
        # before execution
        # -----------------------------------------

        await self.tool_validator.validate(

            capability,

            request

        )







        # -----------------------------------------
        # Execute real MCP Tool
        # -----------------------------------------

        result = await (

            self.mcp_registry

            .mcp_client

            .call_tool(

                capability,

                request

            )

        )



        return {


            "tool":

                capability,


            "status":

                "success",


            "result":

                result

        }









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
