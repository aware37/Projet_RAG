from typing import List
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter


def create_document(docs: list[Document]) -> List[Document]:
    """
    Create a list of Document objects from the input documents.
    Each Document contains the page content and its source metadata.
    """
    document: List[Document] = []

    for doc in docs:
        src = doc.metadata.get("source")
        document.append(
            Document(
                page_content = doc.page_content,
                metadata = {
                    "source": doc.metadata.get("source", ""),
                    "title": doc.metadata.get("title", ""),
                    "author": doc.metadata.get("author", ""),
                    "keywords": doc.metadata.get("keywords", ""),
                    "date": doc.metadata.get("date", ""),
                    "page": doc.metadata.get("page", None),
                }
            )
        )
    
    return document


def chunk_text(documents: List[Document]) -> List[Document]:
    """Chunks the input documents into smaller pieces for processing."""
    
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=300,
        separators=["\n\n", "\n", ".", " ", ""],
        add_start_index=True,
        keep_separator=True, 
        is_separator_regex=False,
    )
       
    return text_splitter.split_documents(documents)