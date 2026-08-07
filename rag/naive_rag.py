from rag.retriever import retrieve
from langchain_groq import ChatGroq

from dotenv import load_dotenv
load_dotenv()
# LLM
llm = ChatGroq(
    model="llama-3.1-8b-instant",
    temperature=0
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