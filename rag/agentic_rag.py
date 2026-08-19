from groq import Groq
from dotenv import load_dotenv
from rag.retriever import retrieve
from langchain_groq import ChatGroq

from langchain_mistralai import ChatMistralAI
import os
llm = ChatMistralAI(
    model="mistral-large-latest",
    temperature=0,
    api_key=os.getenv("MISTRAL_API_KEY"),
)



def agentic_rag(question, max_steps=2):

    collected_context = []

    for step in range(max_steps):

        print(f"Retrieval step {step+1}")

        docs = retrieve(
            question,
            k=3
        )


        context = "\n\n".join(
            [doc.page_content for doc in docs]
        )


        collected_context.append(context)


        check_prompt = f"""
You are a retrieval decision agent.

Question:
{question}

Retrieved information:
{context}

Is this information enough to answer the question?
Reply only YES or NO.
"""


        decision = llm.invoke(check_prompt).content


        if "YES" in decision.upper():

            break



    final_context = "\n\n".join(
        collected_context
    )


    answer_prompt = f"""
You are a travel assistant.

Answer only using this context:

{final_context}

Question:
{question}

Answer:
"""


    answer = llm.invoke(answer_prompt)

    return answer.content



if __name__ == "__main__":

    q = """
I booked a promotional flight ticket.
I want to cancel after 24 hours.
What refund can I get?
"""

    print(agentic_rag(q))