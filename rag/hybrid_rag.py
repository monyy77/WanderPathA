from rag.retriever import retrieve
from rag.chunking import create_chunks

from rank_bm25 import BM25Okapi

from langchain_groq import ChatGroq
from dotenv import load_dotenv
load_dotenv()


llm = ChatGroq(
    model="llama-3.1-8b-instant",
    temperature=0
)



# Load documents for BM25
chunks = create_chunks()


# Prepare BM25 index
tokenized_chunks = [
    doc.page_content.lower().split()
    for doc in chunks
]

bm25 = BM25Okapi(tokenized_chunks)



def keyword_search(query, k=3):

    tokens = query.lower().split()

    scores = bm25.get_scores(tokens)

    top_indexes = scores.argsort()[-k:][::-1]

    return [
        chunks[i]
        for i in top_indexes
    ]



def hybrid_retrieve(query, k=3):

    # Vector results
    vector_results = retrieve(
        query,
        k=k
    )


    # Keyword results
    keyword_results = keyword_search(
        query,
        k=k
    )


    # Merge results
    combined = vector_results + keyword_results


    # Remove duplicates
    unique_docs = []

    seen = set()

    for doc in combined:

        if doc.page_content not in seen:

            unique_docs.append(doc)

            seen.add(doc.page_content)


    return unique_docs[:k]



def hybrid_rag(question):

    docs = hybrid_retrieve(
        question
    )


    context = "\n\n".join(
        [
            doc.page_content
            for doc in docs
        ]
    )


    prompt = f"""
You are a travel assistant.

Use only this context:

{context}

Question:
{question}

Answer:
"""


    response = llm.invoke(prompt)

    return response.content



if __name__ == "__main__":

    question = "What is the 24-hour grace period?"

    answer = hybrid_rag(question)

    print(answer)