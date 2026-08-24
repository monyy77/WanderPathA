from agent_router import AgentRouter



router = AgentRouter()


response = router.route(
    {
        "agent": "planning",
        "message":
        "My flight was cancelled, find alternatives"
    }
)


print(response)
