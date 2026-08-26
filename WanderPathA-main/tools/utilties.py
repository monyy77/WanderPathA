from dotenv import load_dotenv
load_dotenv()

from langchain.tools import tool
from langchain_community.tools.tavily_search import TavilySearchResults

tavily = TavilySearchResults(max_results=5)


@tool(
    "search_web",
    return_direct=False,
    description="Search the internet for current information."
)
def SearchWeb(query: str):
    return tavily.invoke(query)


@tool(
    "get_current_date",
    return_direct=False,
    description="Get the current date in YYYY-MM-DD format."
)
def GetCurrentDate():
    from datetime import date
    return date.today().isoformat()

@tool("end_conversation", return_direct=True, description="End the conversation with the agent.")
def EndConversation():
    """
    End the conversation with the agent.
    Returns:
        str: A message indicating that the conversation has ended.
    """
    return True