"""
Custom Semantic Chunker Implementation

This module provides a custom chunking strategy that:
1. Chunks semantically similar sentences based on a designed threshold
2. Groups paragraphs greedily up to a maximum chunk size
3. Ensures minimum chunk size is a single sentence

**How It Works:**
1. **Sentence-Level Processing**: Splits paragraphs into individual sentences
2. **Semantic Similarity**: Calculates cosine similarity between sentence embeddings
3. **Consecutive Grouping**: Groups semantically similar consecutive sentences
4. **Greedy Merging**: Merges chunks up to maximum size while maintaining semantic coherence

**Example Process:**
```
Original Paragraph:
"The weather is sunny today. I love going to the beach. The stock market crashed. Investors are worried."

Processing:
- Sentences 1-2: Similar (weather/beach) → Chunk 1
- Sentences 3-4: Similar (finance) → Chunk 2

Result:
Chunk 1: "The weather is sunny today. I love going to the beach."
Chunk 2: "The stock market crashed. Investors are worried."
"""

import numpy as np
from typing import List, Dict, Any
from langchain_core.documents import Document
from langchain_openai import OpenAIEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
import re


class CustomSemanticChunker:
    """
    A custom chunker that groups semantically similar sentences and paragraphs
    greedily up to a maximum chunk size.
    """
    
    def __init__(
        self,
        embeddings_model=None,
        similarity_threshold: float = 0.7,
        max_chunk_size: int = 1000,
        min_chunk_size: int = 50,
        chunk_overlap: int = 0
    ):
        """
        Initialize the custom semantic chunker.
        
        Args:
            embeddings_model: The embedding model to use for semantic similarity
            similarity_threshold: Threshold for semantic similarity (0-1)
            max_chunk_size: Maximum characters per chunk
            min_chunk_size: Minimum characters per chunk (single sentence)
            chunk_overlap: Overlap between chunks
        """
        self.embeddings_model = embeddings_model or OpenAIEmbeddings(model="text-embedding-3-small")
        self.similarity_threshold = similarity_threshold
        self.max_chunk_size = max_chunk_size
        self.min_chunk_size = min_chunk_size
        self.chunk_overlap = chunk_overlap
        
        # Fallback text splitter for basic sentence splitting
        self.fallback_splitter = RecursiveCharacterTextSplitter(
            chunk_size=max_chunk_size,
            chunk_overlap=chunk_overlap,
            separators=["\n\n", "\n", ". ", "! ", "? ", " ", ""]
        )
    
    def _split_into_sentences(self, text: str) -> List[str]:
        """Split text into sentences using regex patterns."""
        # More robust sentence splitting
        sentence_patterns = [
            r'(?<=[.!?])\s+(?=[A-Z])',  # Period, exclamation, question mark
            r'(?<=\n)\s*(?=\n)',        # Double newlines
            r'(?<=\n)\s*(?=[A-Z])'      # Newline followed by capital letter
        ]
        
        sentences = [text]
        for pattern in sentence_patterns:
            new_sentences = []
            for sentence in sentences:
                new_sentences.extend(re.split(pattern, sentence))
            sentences = new_sentences
        
        # Clean up sentences
        sentences = [s.strip() for s in sentences if s.strip()]
        return sentences
    
    def _split_into_paragraphs(self, text: str) -> List[str]:
        """Split text into paragraphs."""
        paragraphs = text.split('\n\n')
        paragraphs = [p.strip() for p in paragraphs if p.strip()]
        return paragraphs
    
    def _get_embeddings(self, texts: List[str]) -> np.ndarray:
        """Get embeddings for a list of texts."""
        if not texts:
            return np.array([])
        
        embeddings = self.embeddings_model.embed_documents(texts)
        return np.array(embeddings)
    
    def _calculate_similarity(self, emb1: np.ndarray, emb2: np.ndarray) -> float:
        """Calculate cosine similarity between two embeddings."""
        if emb1.shape != emb2.shape:
            return 0.0
        
        # Normalize embeddings
        emb1_norm = emb1 / (np.linalg.norm(emb1) + 1e-8)
        emb2_norm = emb2 / (np.linalg.norm(emb2) + 1e-8)
        
        # Calculate cosine similarity
        similarity = np.dot(emb1_norm, emb2_norm)
        return float(similarity)
    
    def _chunk_semantically(self, sentences: List[str]) -> List[str]:
        """Chunk sentences based on semantic similarity."""
        if not sentences:
            return []
        
        if len(sentences) == 1:
            return sentences
        
        # Get embeddings for all sentences
        embeddings = self._get_embeddings(sentences)
        
        chunks = []
        current_chunk = [sentences[0]]
        current_chunk_emb = embeddings[0]
        
        for i in range(1, len(sentences)):
            sentence = sentences[i]
            sentence_emb = embeddings[i]
            
            # Calculate similarity with current chunk
            similarity = self._calculate_similarity(current_chunk_emb, sentence_emb)
            
            # Check if we should add to current chunk
            should_add = (
                similarity >= self.similarity_threshold and
                len(' '.join(current_chunk + [sentence])) <= self.max_chunk_size
            )
            
            if should_add:
                current_chunk.append(sentence)
                # Update chunk embedding (average of all sentences in chunk)
                current_chunk_emb = self._get_embeddings([' '.join(current_chunk)]).flatten()
            else:
                # Finalize current chunk if it meets minimum size
                chunk_text = ' '.join(current_chunk)
                if len(chunk_text) >= self.min_chunk_size:
                    chunks.append(chunk_text)
                else:
                    # If chunk is too small, try to merge with next chunk
                    # For now, we'll keep it as is
                    chunks.append(chunk_text)
                
                # Start new chunk
                current_chunk = [sentence]
                current_chunk_emb = sentence_emb
        
        # Add the last chunk
        if current_chunk:
            chunk_text = ' '.join(current_chunk)
            chunks.append(chunk_text)
        
        return chunks
    
    def split_documents(self, documents: List[Document]) -> List[Document]:
        """
        Split documents using the custom semantic chunking strategy.
        
        Args:
            documents: List of Document objects to split
            
        Returns:
            List of Document objects with semantic chunks
        """
        all_chunks = []
        
        for doc in documents:
            text = doc.page_content
            
            # First, split into paragraphs
            paragraphs = self._split_into_paragraphs(text)
            
            paragraph_chunks = []
            for paragraph in paragraphs:
                # Split paragraph into sentences
                sentences = self._split_into_sentences(paragraph)
                
                if len(sentences) == 0:
                    continue
                
                # If paragraph is already small enough, keep as is
                if len(paragraph) <= self.max_chunk_size:
                    paragraph_chunks.append(paragraph)
                else:
                    # Apply semantic chunking to sentences
                    semantic_chunks = self._chunk_semantically(sentences)
                    paragraph_chunks.extend(semantic_chunks)
            
            # Process paragraph chunks greedily
            final_chunks = self._greedy_merge_chunks(paragraph_chunks)
            
            # Create Document objects
            for chunk in final_chunks:
                chunk_doc = Document(
                    page_content=chunk,
                    metadata=doc.metadata.copy()
                )
                all_chunks.append(chunk_doc)
        
        return all_chunks
    
    def _greedy_merge_chunks(self, chunks: List[str]) -> List[str]:
        """Greedily merge chunks up to max_chunk_size."""
        if not chunks:
            return []
        
        merged_chunks = []
        current_chunk = chunks[0]
        
        for i in range(1, len(chunks)):
            next_chunk = chunks[i]
            
            # Check if we can merge
            combined = current_chunk + ' ' + next_chunk
            
            if len(combined) <= self.max_chunk_size:
                current_chunk = combined
            else:
                # Finalize current chunk
                merged_chunks.append(current_chunk)
                current_chunk = next_chunk
        
        # Add the last chunk
        merged_chunks.append(current_chunk)
        
        return merged_chunks
    
    def split_text(self, text: str) -> List[str]:
        """Split a single text string using the custom strategy."""
        # Create a temporary document
        temp_doc = Document(page_content=text, metadata={})
        chunks = self.split_documents([temp_doc])
        return [chunk.page_content for chunk in chunks]


# Example usage function
def create_semantic_chunker(
    similarity_threshold: float = 0.7,
    max_chunk_size: int = 1000,
    min_chunk_size: int = 50,
    chunk_overlap: int = 0
) -> CustomSemanticChunker:
    """
    Factory function to create a CustomSemanticChunker with default settings.
    
    Args:
        similarity_threshold: Threshold for semantic similarity (0-1)
        max_chunk_size: Maximum characters per chunk
        min_chunk_size: Minimum characters per chunk
        chunk_overlap: Overlap between chunks
        
    Returns:
        Configured CustomSemanticChunker instance
    """
    return CustomSemanticChunker(
        similarity_threshold=similarity_threshold,
        max_chunk_size=max_chunk_size,
        min_chunk_size=min_chunk_size,
        chunk_overlap=chunk_overlap
    )
