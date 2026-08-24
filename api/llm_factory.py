import os
from dotenv import load_dotenv
from langchain_mistralai import ChatMistralAI


load_dotenv()


def get_llm():

    api_key = os.getenv("MISTRAL_API_KEY")

    if not api_key:
        raise ValueError(
            "MISTRAL_API_KEY missing"
        )


    return ChatMistralAI(
        model="mistral-large-latest",
        temperature=0,
        api_key=api_key
    )