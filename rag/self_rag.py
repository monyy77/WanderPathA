from retriever import retrieve
from langchain_groq import ChatGroq


llm = ChatGroq(
    model="llama-3.1-8b-instant",
    temperature=0
)


def verify_context(question, context):
    """
    Check whether the retrieved context is relevant to the question.
    """

    prompt = f"""
You are a retrieval verifier.

Question:
{question}

Retrieved Context:
{context}

Is this context relevant enough to answer the question?

Reply only with YES or NO.
"""

    result = llm.invoke(prompt).content.strip()

    return "YES" in result.upper()


def verify_answer(answer, context):
    """
    Check whether the generated answer is fully supported by the context.
    """

    prompt = f"""
You are a factual verifier.

Retrieved Context:
{context}

Generated Answer:
{answer}

Is the answer completely supported by the context?

Reply only with YES or NO.
"""

    result = llm.invoke(prompt).content.strip()

    return "YES" in result.upper()


def self_rag(question):

    # -----------------------------
    # RAG Retrieval
    # -----------------------------
    docs = retrieve(question, k=3)

    context = "\n\n".join(
        [doc.page_content for doc in docs]
    )

    # -------------------------------------------------
    # TODO (Memory Team):
    # Retrieve memories here (episodic / semantic),
    # verify them using verify_context(),
    # then merge them with the RAG context.
    #
    # Example:
    #
    # memories = retrieve_memory(question)
    #
    # if verify_context(question, memories):
    #     context += "\n\n" + memories
    #
    # This satisfies the requirement:
    # "Verification applies to both RAG and Memory."
    # -------------------------------------------------

    # -----------------------------
    # Verify retrieved context
    # -----------------------------
    if not verify_context(question, context):

        print("Retrieved context not relevant. Retrying...")

        docs = retrieve(question, k=5)

        context = "\n\n".join(
            [doc.page_content for doc in docs]
        )

        # If retrieval still fails -> visible consequence
        if not verify_context(question, context):

            return (
                "Unable to retrieve reliable information "
                "for this question."
            )

    # -----------------------------
    # Generate Answer
    # -----------------------------
    answer_prompt = f"""
You are a travel assistant.

Answer ONLY using the following context.

Context:
{context}

Question:
{question}

Answer:
"""

    answer = llm.invoke(answer_prompt).content

    # -----------------------------
    # Verify Generated Answer
    # -----------------------------
    if verify_answer(answer, context):

        return answer

    print("Generated answer is not supported. Regenerating...")

    # Retry generation once
    regenerated_answer = llm.invoke(answer_prompt).content

    if verify_answer(regenerated_answer, context):

        return regenerated_answer

    # Visible consequence if verification fails
    return (
        "The generated answer could not be verified "
        "against the retrieved knowledge."
    )


if __name__ == "__main__":

    question = "What happens if the airline cancels my flight?"

    print(self_rag(question))