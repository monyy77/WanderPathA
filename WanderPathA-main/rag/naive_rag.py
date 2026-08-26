import os
from rag.retriever import retrieve
from langchain_groq import ChatGroq

from dotenv import load_dotenv
load_dotenv()

llm = ChatGroq(
    model="llama-3.3-70b-versatile",
    groq_api_key=os.getenv("GROQ_API_KEY"),
    temperature=0.1,
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