from rag.retriever import retrieve
from langchain_groq import ChatGroq
from memory.episodic_memory import retrieve as retrieve_episodic
from memory.semantic_memory import retrieve as retrieve_semantic

# episodic = retrieve_episodic(question)
# semantic = retrieve_semantic(question)
# memory_context = episodic + "\n\n" + semantic

llm = ChatGroq(
    model="llama-3.1-8b-instant",
    temperature=0
)


def verify_context(question, context):
    """
    Verify that the retrieved information
    (RAG documents OR Memories) is relevant.
    """

    prompt = f"""
You are a retrieval verifier.

Question:
{question}

Retrieved Information:
{context}

Is this information relevant enough to answer the question?

Reply ONLY with YES or NO.
"""

    result = llm.invoke(prompt).content.strip()

    return "YES" in result.upper()


def verify_answer(answer, context):
    """
    Verify that the generated answer is supported
    by the retrieved information.
    """

    prompt = f"""
You are a factual verifier.

Retrieved Information:
{context}

Generated Answer:
{answer}

Is the answer fully supported by the retrieved information?

Reply ONLY with YES or NO.
"""

    result = llm.invoke(prompt).content.strip()

    return "YES" in result.upper()


def self_rag(question, memory_context=""):
    """
    Self-RAG Verification Layer

    Parameters
    ----------
    question : str

    memory_context : str
        Retrieved episodic / semantic memory.
        Default = "".
    """

    # -----------------------------
    # Retrieve RAG Documents
    # -----------------------------

    docs = retrieve(question, k=3)

    rag_context = "\n\n".join(
        doc.page_content
        for doc in docs
    )

    # -----------------------------
    # Verify RAG Context
    # -----------------------------

    if not verify_context(question, rag_context):

        print("RAG retrieval not sufficient. Retrying...")

        docs = retrieve(question, k=5)

        rag_context = "\n\n".join(
            doc.page_content
            for doc in docs
        )

    # -----------------------------
    # Verify Memory
    # -----------------------------

    verified_memory = ""

    if memory_context:

        if verify_context(question, memory_context):

            verified_memory = memory_context

        else:

            print("Memory rejected by verification.")

    # -----------------------------
    # Merge Context
    # -----------------------------

    full_context = rag_context

    if verified_memory:

        full_context += "\n\n" + verified_memory

    # -----------------------------
    # Generate Answer
    # -----------------------------

    prompt = f"""
You are a travel assistant.

Answer ONLY using the provided information.

Context:
{full_context}

Question:
{question}

Answer:
"""

    answer = llm.invoke(prompt).content

    # -----------------------------
    # Verify Final Answer
    # -----------------------------

    if verify_answer(answer, full_context):

        return answer

    print("Answer verification failed. Regenerating...")

    regenerated = llm.invoke(prompt).content

    if verify_answer(regenerated, full_context):

        return regenerated

    return (
        "The generated answer could not be verified "
        "against the retrieved knowledge."
    )


if __name__ == "__main__":

    question = "What happens if the airline cancels my flight?"

    print(
        self_rag(
            question,
            memory_context=""
        )
    )