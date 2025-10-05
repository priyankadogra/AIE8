"""
Example usage of the Custom Semantic Chunker

This script demonstrates how to use the custom semantic chunking strategy
that chunks semantically similar sentences and paragraphs greedily.
"""

from semantic_chunker import create_semantic_chunker
from langchain_community.document_loaders import DirectoryLoader, PyMuPDFLoader


def main():
    """Example usage of the custom semantic chunker."""
    
    # Load documents (same as in your notebook)
    path = "data/"
    loader = DirectoryLoader(path, glob="*.pdf", loader_cls=PyMuPDFLoader)
    docs = loader.load()
    
    print(f"Loaded {len(docs)} documents")
    
    # Create custom semantic chunker with your specifications
    text_splitter = create_semantic_chunker(
        similarity_threshold=0.7,  # Adjust based on your needs
        max_chunk_size=1000,       # Maximum characters per chunk
        min_chunk_size=50,         # Minimum characters per chunk (single sentence)
        chunk_overlap=0            # No overlap between chunks
    )
    
    # Split documents using the custom strategy
    print("Chunking documents with custom semantic strategy...")
    split_documents = text_splitter.split_documents(docs)
    
    # Display results
    num_chunks = len(split_documents)
    print(f"\nNumber of chunks created: {num_chunks}")
    
    # Show statistics about chunk sizes
    chunk_sizes = [len(doc.page_content) for doc in split_documents]
    print(f"Average chunk size: {sum(chunk_sizes) / len(chunk_sizes):.1f} characters")
    print(f"Min chunk size: {min(chunk_sizes)} characters")
    print(f"Max chunk size: {max(chunk_sizes)} characters")
    
    # Display sample chunks
    print(f"\nSample chunks:")
    for i, doc in enumerate(split_documents[:3]):  # Show first 3 chunks
        print(f"\n--- Chunk {i+1} ({len(doc.page_content)} chars) ---")
        print(f"Content: {doc.page_content[:200]}...")
        if len(doc.page_content) > 200:
            print("...")
    
    return split_documents


if __name__ == "__main__":
    split_documents = main()
