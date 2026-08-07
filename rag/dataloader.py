from langchain_community.document_loaders import DirectoryLoader, TextLoader


def load_documents(path="rag/knowledge_base"):
    """
    Load all Markdown files from the knowledge base folder.
    Returns a list of LangChain Document objects.
    """

    loader = DirectoryLoader(
        path=path,
        glob="*.md",
        loader_cls=TextLoader,
        loader_kwargs={"encoding": "utf-8"}
    )

    documents = loader.load()

    print("=" * 50)
    print(f"Loaded {len(documents)} document(s)\n")

    for i, doc in enumerate(documents, start=1):
        print(f"Document {i}")
        print(f"Source: {doc.metadata['source']}")
        print(f"Characters: {len(doc.page_content)}")
        print("-" * 50)

    return documents


if __name__ == "__main__":
    docs = load_documents()