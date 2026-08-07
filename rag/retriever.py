from rag.vector_db import get_vector_store

def retrieve(query, k=2, filter_dict=None):
    """
    Retrieve top-k chunks with optional pre/mid-search Metadata Filtering.
    """
    vector_store = get_vector_store()
    
    # Pre/Mid filtering logic using Chroma metadata filter
    results = vector_store.similarity_search(
        query=query,
        k=k,
        filter=filter_dict )
    return results


if __name__ == "__main__":

    question = "What is the baggage allowance?"

    docs = retrieve(question)

    print("=" * 50)
    print(f"Question: {question}")
    print("=" * 50)

    for i, doc in enumerate(docs, start=1):
        print(f"\nResult {i}")
        print(f"Source: {doc.metadata['source']}")
        print("-" * 40)
        print(doc.page_content)