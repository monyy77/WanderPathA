import os
from dotenv import load_dotenv

load_dotenv()


def get_llm():
    """
    Returns the configured LLM.
    Falls back gracefully if LLM package/API key is unavailable.
    """

    api_key = os.getenv("MISTRAL_API_KEY")

    if not api_key:
        print(
            "WARNING: MISTRAL_API_KEY missing. "
            "Running without external LLM."
        )
        return None

    try:
        from langchain_mistralai import ChatMistralAI

        return ChatMistralAI(
            model="mistral-large-latest",
            temperature=0,
            api_key=api_key
        )

    except ImportError:
        print(
            "WARNING: langchain_mistralai is not installed. "
            "Running without Mistral LLM."
        )
        return None

    except Exception as e:
        print(
            f"WARNING: Failed initializing Mistral LLM: {e}"
        )
        return None
