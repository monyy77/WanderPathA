"""
MCP Tool Schema Validator
"""


class MCPToolValidator:



    def __init__(
        self,
        registry
    ):

        self.registry = registry






    async def validate(
        self,
        tool_name,
        arguments
    ):



        tools = await (

            self.registry

            .list_capabilities()

        )



        tool = next(

            (

                t

                for t in tools

                if t["name"] == tool_name

            ),

            None

        )



        if tool is None:


            raise ValueError(

                f"MCP Tool not found: {tool_name}"

            )



        schema = tool.get(
            "input_schema",
            {}
        )



        required = schema.get(
            "required",
            []
        )



        missing = [

            key

            for key in required

            if key not in arguments

        ]



        if missing:


            raise ValueError(

                f"Missing arguments: {missing}"

            )



        return True
