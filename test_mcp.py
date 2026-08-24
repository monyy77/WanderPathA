"""
test_mcp.py

End-to-end test for the WanderPathA MCP Server.

Tests:
1. Connect to MCP Server.
2. Discover runtime tools.
3. Execute ping().
4. (Optional) Execute a real business tool.
5. Disconnect cleanly.
"""

import asyncio

from api.mcp_client import MCPClient


async def main():

    client = MCPClient("http://localhost:9000")

    try:
        print("=" * 60)
        print("Connecting to MCP Server...")
        print("=" * 60)

        await client.connect()

        print("\nDiscovering tools...\n")

        tools = await client.list_tools()

        if not tools:
            print("❌ No tools discovered.")
            return

        print(f"Discovered {len(tools)} tool(s):\n")

        for tool in tools:
            print(f"- {tool.name}")
            if tool.description:
                print(f"    {tool.description}")

        print("\n" + "=" * 60)

        print("Testing ping tool...\n")

        result = await client.call_tool("ping", {})

        print("ping() =>")
        print(result)

        print("\n" + "=" * 60)

        # ----------------------------------------------------
        # Optional Business Tool Test
        # Uncomment when database is ready
        # ----------------------------------------------------
        #
        # result = await client.call_tool(
        #     "get_customer_profile",
        #     {
        #         "user_id": 1
        #     }
        # )
        #
        # print(result)

        print("\nAll MCP tests completed successfully.")

    except Exception as exc:

        print("\nMCP TEST FAILED")
        print(type(exc).__name__)
        print(exc)

    finally:

        await client.disconnect()


if __name__ == "__main__":
    asyncio.run(main())