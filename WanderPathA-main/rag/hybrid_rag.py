import os
from rag.retriever import retrieve
from rag.chunking import create_chunks

from rank_bm25 import BM25Okapi

from langchain_groq import ChatGroq
from dotenv import load_dotenv

load_dotenv()

llm = ChatGroq(
    model="llama-3.3-70b-versatile",
    groq_api_key=os.getenv("GROQ_API_KEY"),
    temperature=0.1,
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
    return [chunks[i] for i in top_indexes]


def reciprocal_rank_fusion(vector_docs, keyword_docs, k=60, top_n=3):
    """Reciprocal Rank Fusion (RRF) for Hybrid Search Combination"""
    doc_scores = {}

    def score_docs(docs):
        for rank, doc in enumerate(docs):
            doc_id = doc.page_content
            if doc_id not in doc_scores:
                doc_scores[doc_id] = {"doc": doc, "score": 0.0}
            doc_scores[doc_id]["score"] += 1.0 / (k + rank + 1)

    score_docs(vector_docs)
    score_docs(keyword_docs)

    # Sorting documents by combined RRF score
    sorted_docs = sorted(doc_scores.values(), key=lambda x: x["score"], reverse=True)
    return [item["doc"] for item in sorted_docs[:top_n]]


def hybrid_retrieve(query, k=3):
    # 1. Vector Search
    vector_results = retrieve(query, k=k)

    # 2. Keyword Search 
    keyword_results = keyword_search(query, k=k)

    # 3. RRF Fusion & Re-ranking
    final_docs = reciprocal_rank_fusion(vector_results, keyword_results, top_n=k)

    return final_docs


def hybrid_rag(question):
    docs = hybrid_retrieve(question)

    context = "\n\n".join([doc.page_content for doc in docs])

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