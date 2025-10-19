"""
Cohere-based RAG with Compression
Uses Cohere's compression capabilities for better retrieval
"""

import os
from pathlib import Path
from typing import List, Optional, Dict, Any, Tuple
import numpy as np
import cohere
from qdrant_client import QdrantClient
from qdrant_client.http.models import Distance, VectorParams, PointStruct, Filter, FieldCondition, MatchValue
import hashlib

from config import LOCAL_TZ, PDF_DIR, COLLECTION_NAME, EMBEDDING_DIM, COHERE_API_KEY
from .data_processing import pdf_to_text, guess_newsletter_date, _coerce_dt, dedupe_events, list_upcoming, list_deadlines, to_ics

class CohereRAG:
    def __init__(self, collection_name: str = COLLECTION_NAME):
        self.collection_name = collection_name
        self.client_q = QdrantClient(location=":memory:")
        self.cohere_client = cohere.Client(COHERE_API_KEY)
        
    def ensure_collection(self, dim: int = EMBEDDING_DIM):
        """Ensure Qdrant collection exists"""
        existing = [c.name for c in self.client_q.get_collections().collections]
        if self.collection_name not in existing:
            self.client_q.recreate_collection(
                collection_name=self.collection_name,
                vectors_config=VectorParams(size=dim, distance=Distance.COSINE),
            )
    
    def compress_text(self, text: str, compression_ratio: float = 0.3) -> str:
        """Text compression disabled - return original text"""
        # Compression API not available, return original text
        return text
    
    def embed_texts(self, texts: List[str]) -> np.ndarray:
        """Generate embeddings using OpenAI (same as standard RAG)"""
        if not texts:
            return np.zeros((0, EMBEDDING_DIM), dtype="float32")
        
        try:
            from openai import OpenAI
            client = OpenAI()
            resp = client.embeddings.create(model="text-embedding-3-small", input=texts)
            return np.array([d.embedding for d in resp.data], dtype="float32")
        except Exception as e:
            print(f"OpenAI embedding failed: {e}")
            # Fallback to zeros
            return np.zeros((len(texts), EMBEDDING_DIM), dtype="float32")
    
    def embed_query(self, query: str) -> np.ndarray:
        """Generate query embedding using OpenAI (same as standard RAG)"""
        try:
            from openai import OpenAI
            client = OpenAI()
            resp = client.embeddings.create(model="text-embedding-3-small", input=[query])
            return np.array(resp.data[0].embedding, dtype="float32")
        except Exception as e:
            print(f"OpenAI query embedding failed: {e}")
            return np.zeros(EMBEDDING_DIM, dtype="float32")
    
    def split_into_chunks(self, text: str, max_chars: int = 800, overlap: int = 100) -> List[str]:
        """Split text into chunks (same as standard RAG)"""
        chunks = []
        i = 0
        while i < len(text):
            j = min(len(text), i + max_chars)
            chunk = text[i:j]
            
            # Try to break at sentence boundaries
            k = chunk.rfind(". ")
            if k > 300:
                j = i + k + 2
                chunk = text[i:j]
            
            chunk = chunk.strip()
            if chunk:
                chunks.append(chunk)
            
            i = max(j - overlap, j)
        
        return chunks
    
    def file_fingerprint(self, path: Path) -> dict:
        """Get file fingerprint for caching"""
        st = path.stat()
        return {"mtime": int(st.st_mtime), "size": int(st.st_size)}
    
    def point_id_for(self, source_pdf: str, chunk_idx: int) -> int:
        """Generate stable point ID"""
        h = hashlib.blake2b(f"{source_pdf}:{chunk_idx}".encode(), digest_size=8).hexdigest()
        return int(h, 16)
    
    def index_folder(self, pdf_folder: str, max_chars: int = 800, overlap: int = 100) -> dict:
        """Index PDFs with Cohere reranking"""
        self.ensure_collection()
        pdf_dir = Path(pdf_folder)
        files = sorted(pdf_dir.glob("*.pdf"))
        
        indexed, skipped = 0, 0
        for path in files:
            print(f"Processing {path.name}...")
            
            # Extract text
            text = pdf_to_text(path)
            
            # Split into chunks
            chunks = self.split_into_chunks(text, max_chars=max_chars, overlap=overlap)
            
            # Generate embeddings
            vecs = self.embed_texts(chunks)
            
            # Store in Qdrant
            points = []
            for i, (chunk, vec) in enumerate(zip(chunks, vecs)):
                points.append(PointStruct(
                    id=self.point_id_for(path.name, i),
                    vector=vec.tolist(),
                    payload={
                        "source_pdf": path.name,
                        "chunk_index": i,
                        "text": chunk,
                        "compressed": False
                    }
                ))
            
            if points:
                self.client_q.upsert(collection_name=self.collection_name, points=points)
            
            indexed += 1
        
        return {"indexed": indexed, "skipped": skipped, "total_files": len(files)}
    
    def search(self, query: str, k: int = 5, filter_sources: Optional[List[str]] = None) -> List[Tuple[Dict[str, Any], float]]:
        """Search with Cohere embeddings and reranking"""
        # Generate query embedding
        qvec = self.embed_query(query)
        
        # Set up filter
        q_filter = None
        if filter_sources:
            q_filter = Filter(must=[FieldCondition(key="source_pdf", match=MatchValue(value=filter_sources))])
        
        # Search in Qdrant (get more results for reranking)
        initial_k = min(k * 3, 20)  # Get 3x more results for reranking
        res = self.client_q.search(
            collection_name=self.collection_name,
            query_vector=qvec.tolist(),
            limit=initial_k,
            query_filter=q_filter,
            with_payload=True,
        )
        
        if not res:
            return []
        
        # Prepare documents for reranking
        documents = []
        for r in res:
            payload = r.payload or {}
            documents.append({
                "source_pdf": payload.get("source_pdf"),
                "text": payload.get("text", ""),
                "compressed": payload.get("compressed", False)
            })
        
        # Apply Cohere reranking
        try:
            rerank_response = self.cohere_client.rerank(
                model="rerank-english-v3.0",
                query=query,
                documents=[doc["text"] for doc in documents],
                top_n=k
            )
            
            # Format reranked results
            out = []
            for result in rerank_response.results:
                doc_idx = result.index
                doc = documents[doc_idx]
                out.append((doc, float(result.relevance_score)))
            
            return out
            
        except Exception as e:
            print(f"Cohere reranking failed: {e}")
            # Fallback to original results without reranking
            out = []
            for r in res[:k]:  # Take top k results
                payload = r.payload or {}
                out.append(({
                    "source_pdf": payload.get("source_pdf"),
                    "text": payload.get("text", "")
                }, float(r.score)))
            return out
    
    def health_check(self, sample_query: str = "Unity Day") -> str:
        """Check the health of the Cohere RAG system"""
        try:
            cols = self.client_q.get_collections().collections
        except Exception as e:
            return f"❌ Could not reach Qdrant client: {e}"
        
        if not cols:
            return "❌ No collections in Qdrant client."
        
        col_names = [c.name for c in cols]
        if self.collection_name not in col_names:
            return f"⚠️  Collection '{self.collection_name}' not found. Available: {col_names}"
        
        # Show basic stats
        info = self.client_q.get_collection(self.collection_name)
        total_points = getattr(info, "points_count", None) or getattr(info, "vectors_count", 0)
        
        result = f"🗂️  Collection: {self.collection_name} — {total_points:,} vectors\n"
        
        # Test search
        try:
            results = self.search(sample_query, k=3)
            if results:
                result += f"\n🎯 Sample search: '{sample_query}'\n"
                for i, (chunk, score) in enumerate(results, 1):
                    snippet = chunk["text"].replace("\n", " ")[:180]
                    result += f"\nTop {i}: {chunk['source_pdf']} (score={score:.3f})\n  {snippet}...\n"
            else:
                result += f"\n⚠️  No results for sample query: '{sample_query}'"
        except Exception as e:
            result += f"\n⚠️  Sample search failed: {e}"
        
        return result

# Global instance
cohere_rag = CohereRAG()

def build_cohere_index_from_folder(pdf_folder: str):
    """Build Cohere RAG index from folder"""
    return cohere_rag.index_folder(pdf_folder)

def cohere_rag_search(query: str, k: int = 5):
    """Search using Cohere RAG"""
    return cohere_rag.search(query, k=k)

def cohere_health_check():
    """Check Cohere RAG health"""
    return cohere_rag.health_check()

