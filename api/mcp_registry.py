"""
MCP Runtime Registry

Discovers available capabilities
from MCP Server.
"""


class MCPRegistry:


    def __init__(self, mcp_client=None):

        self.mcp_client = mcp_client



    def list_capabilities(self):

        """
        Runtime discovery.

        Later replaced by:
        mcp_client.list_tools()
        """

        if self.mcp_client:

            return self.mcp_client.list_tools()



        # Temporary fallback
        # until MCP client connection exists

        return [

            {
                "name": "planning_agent",
                "description":
                    "Creates travel plans and decomposes tasks",
            },


            {
                "name": "memory_agent",
                "description":
                    "Stores and retrieves customer memories",
            },


            {
                "name": "flight_rebooking_graph",
                "description":
                    "Handles flight delays, cancellations and rebooking",
            },


            {
                "name": "refund_graph",
                "description":
                    "Handles refunds and compensation",
            },


            {
                "name": "vip_graph",
                "description":
                    "Handles VIP upgrades and premium services",
            },

        ]



    def get_capabilities_prompt(self):


        tools = self.list_capabilities()


        return "\n".join(

            [
                f"{tool['name']}: {tool['description']}"
                for tool in tools
            ]

        )
