import asyncio
import os
import sys

from agent import run_agent  
from client import create_client

path_to_mcp_server = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "../server/server.py")
)

mode = sys.argv[1] if len(sys.argv) > 1 else "stdio"

async def main():
    # إنشاء واستدعاء الـ MCP Client
    client = await create_client()

    print("===================================")
    print("  WanderPath Travel Support Agent  ")
    print("===================================")
    print("Commands: 'logout' to switch user, 'exit' to quit\n")

    try:
        while True:
            user_id = input("Enter your user ID login: ").strip()
            
            if user_id.lower() == "exit":
                print("Goodbye!")
                break
                
            if not user_id:
                continue

            logged_in = True
            print(f"\n---> Logged in as: {user_id} <---")

            while logged_in:
                user_input = input(f"[{user_id}] User: ").strip()

                if not user_input:
                    continue

                if user_input.lower() == "logout":
                    from agent import conversation_history
                    conversation_history.pop(user_id, None)
                    logged_in = False
                    print(f"Logged out from {user_id}.\n")
                    break

                if user_input.lower() == "exit":
                    print("Goodbye!")
                    return

                # تشغيل الـ Agent الموحد (MCP + Self-RAG + Memory)
                step = await run_agent(
                    client=client,
                    user_input=user_input,
                    user_id=user_id
                )

                if step and getattr(step, "action", None) == "end_conversation":
                    print("Conversation ended.")
                    break

    finally:
        # إغلاق جلسة الـ MCP بشكل آمن عند نهاية التشغيل
        if hasattr(client, "close"):
            await client.close()

if __name__ == "__main__":
    asyncio.run(main())