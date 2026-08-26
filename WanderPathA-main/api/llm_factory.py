import os
from dotenv import load_dotenv

load_dotenv()


def get_llm():
    """
    Returns the configured LLM.
    Falls back gracefully if LLM package/API key is unavailable.
    """

    api_key = os.getenv("GROQ_API_KEY")

    if not api_key:
        print(
            "WARNING: GROQ_API_KEY missing. "
            "Running without external LLM."
        )
        return None

    try:
        from langchain_groq import ChatGroq

        return ChatGroq(
            model="llama-3.1-8b-instant",
            groq_api_key=api_key,
            temperature=0.1
        )

    except ImportError:
        print(
            "WARNING: langchain_groq is not installed. "
            "Running without Groq LLM."
        )
        return None

    except Exception as e:
        print(
            f"WARNING: Failed initializing Groq LLM: {e}"
        )
        return None