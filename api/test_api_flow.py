"""
End-to-End API Flow Test

Flow:

Client
 |
POST /api/chat
 |
FastAPI
 |
AgentRouter
 |
Classifier
 |
Agent Execution
"""


import requests



BASE_URL = "http://localhost:8000"



def test_chat(message):

    response = requests.post(

        f"{BASE_URL}/api/chat",

        json={

            "message": message,

            "session_id": "TEST001",

            "customer_id": "C001",

        }

    )


    print("\nSTATUS:")
    print(response.status_code)


    print("\nRESPONSE:")
    print(
        response.json()
    )



if __name__ == "__main__":


    print(
        "Testing Flight Routing..."
    )

    test_chat(
        "My flight was cancelled, I need rebooking"
    )



    print(
        "\nTesting Refund Routing..."
    )

    test_chat(
        "I want compensation for my cancelled trip"
    )



    print(
        "\nTesting Memory Routing..."
    )

    test_chat(
        "Remember that I prefer window seats"
    )



    print(
        "\nTesting Planning Routing..."
    )

    test_chat(
        "Help me organize my travel"
    )



    print(
        "\nTesting VIP Routing..."
    )

    test_chat(
        "I need a VIP business class upgrade"
    )
