from langchain_text_splitters import RecursiveCharacterTextSplitter
from rag.dataloader import load_documents

    
def create_chunks(chunk_size=500, chunk_overlap=50):
    """
    Split loaded documents into smaller chunks.
    """

    documents = load_documents()

    splitter =RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap
    )

    chunks = splitter.split_documents(documents)

    print("=" * 50)
    print(f"Total Chunks: {len(chunks)}")

    for i, chunk in enumerate(chunks[:5], start=1):
        print(f"\nChunk {i}")
        print(f"Source: {chunk.metadata['source']}")
        print(f"Characters: {len(chunk.page_content)}")
        print(chunk.page_content[:150])
        print("-" * 50)

    return chunks


if __name__ == "__main__":
    create_chunks()