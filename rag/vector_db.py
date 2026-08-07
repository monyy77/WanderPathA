import os

from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings

from chunking import create_chunks


PERSIST_DIRECTORY = "./chroma_db"


def get_vector_store():

    embeddings = HuggingFaceEmbeddings(
        model_name="sentence-transformers/all-MiniLM-L6-v2"
    )

    # If the database already exists, just load it
    if os.path.exists(PERSIST_DIRECTORY) and os.listdir(PERSIST_DIRECTORY):
        print("Loading existing vector database...")

        vector_store = Chroma(
            persist_directory=PERSIST_DIRECTORY,
            embedding_function=embeddings
        )

    # Otherwise create it for the first time
    else:
        print("Creating vector database...")

        chunks = create_chunks()

        vector_store = Chroma.from_documents(
            documents=chunks,
            embedding=embeddings,
            persist_directory=PERSIST_DIRECTORY
        )

        print(f"Indexed {len(chunks)} chunks.")

    return vector_store


if __name__ == "__main__":

    db = get_vector_store()

    print("Vector database is ready.")