import asyncio
import os
import sys

from agent import run_agent
from client import create_client


async def main():
    client = await create_client()

    print("===================================")
    print("  WanderPath Travel Support Agent  ")
    print("===================================")

    test_user_id = "CUST-101"
    test_query = "What is the general cancellation policy?"

    print(f"\nUser ID: {test_user_id}")
    print(f"Query: {test_query}\n")

    try:
        step = await run_agent(
            client=client,
            user_input=test_query,
            user_id=test_user_id
        )

        print("\n===================================")
        print("    PIPELINE EXECUTION FINISHED    ")
        print("===================================")

    finally:
        if hasattr(client, "close"):
            await client.close()


if __name__ == "__main__":
    asyncio.run(main())