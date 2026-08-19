from rag.retriever import retrieve
from langchain_groq import ChatGroq

from dotenv import load_dotenv
load_dotenv()
# LLM
from langchain_mistralai import ChatMistralAI
import os
llm = ChatMistralAI(
    model="mistral-large-latest",
    temperature=0,
    api_key=os.getenv("MISTRAL_API_KEY"),
)


def naive_rag(question):

    # Retrieve relevant documents
    docs = retrieve(
        question,
        k=3
    )

    context = "\n\n".join(
        [doc.page_content for doc in docs]
    )


    prompt = f"""
You are a travel support assistant.

Answer the question only using the provided context.

Context:
{context}

Question:
{question}

Answer:
"""

    response = llm.invoke(prompt)

    return response.content



if __name__ == "__main__":

    question = "What is the baggage allowance?"

    answer = naive_rag(question)

    print(answer)