import os
import getpass
from pathlib import Path
from typing import List, Optional, Dict, Any, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta
import json, re, uuid, numpy as np

from pypdf import PdfReader
from dateutil import tz
import dateparser
from pydantic import BaseModel, Field, ValidationError
from icalendar import Calendar, Event as ICS
from tqdm import tqdm

from config import LOCAL_TZ, PDF_DIR, COLLECTION_NAME, EMBEDDING_MODEL, EMBEDDING_DIM
# --- Index Health Check ---
from collections import Counter

# ---------- RAG STORAGE: in-memory Qdrant + session manifest ----------
from qdrant_client import QdrantClient
from qdrant_client.http.models import Distance, VectorParams, PointStruct, Filter, FieldCondition, MatchValue
import numpy as np, hashlib
from pathlib import Path

from .data_processing import pdf_to_text, guess_newsletter_date, _coerce_dt, dedupe_events, list_upcoming, list_deadlines, to_ics

from openai import OpenAI

# Create OpenAI client
client = OpenAI()

# --- in-memory Qdrant ---
client_q = QdrantClient(location=":memory:")   # ephemeral, per notebook session

def ensure_collection(dim: int = EMBEDDING_DIM):
    existing = [c.name for c in client_q.get_collections().collections]
    if COLLECTION_NAME not in existing:
        client_q.recreate_collection(
            collection_name=COLLECTION_NAME,
            vectors_config=VectorParams(size=dim, distance=Distance.COSINE),
        )

# --- chunker ---
def split_into_chunks(txt: str, max_chars=800, overlap=100):
    chunks, i = [], 0
    while i < len(txt):
        j = min(len(txt), i + max_chars)
        chunk = txt[i:j]
        k = chunk.rfind(". ")
        if k > 300:
            j = i + k + 2
            chunk = txt[i:j]
        chunk = chunk.strip()
        if chunk:
            chunks.append(chunk)
        i = max(j - overlap, j)
    return chunks

# --- helpers for stable IDs + fingerprints ---
def file_fingerprint(path: Path) -> dict:
    st = path.stat()
    return {"mtime": int(st.st_mtime), "size": int(st.st_size)}

def point_id_for(source_pdf: str, chunk_idx: int) -> int:
    h = hashlib.blake2b(f"{source_pdf}:{chunk_idx}".encode(), digest_size=8).hexdigest()
    return int(h, 16)

# --- embeddings (reuse your OpenAI client) ---
from openai import OpenAI

def get_openai_client():
    """Get OpenAI client, creating it only when needed"""
    return OpenAI()

def embed_texts(texts: list[str]) -> np.ndarray:
    if not texts:
        return np.zeros((0, EMBEDDING_DIM), dtype="float32")
    client = get_openai_client()
    resp = client.embeddings.create(model=EMB_MODEL, input=texts)
    return np.array([d.embedding for d in resp.data], dtype="float32")

EMB_MODEL = EMBEDDING_MODEL

def embed_texts(texts: list[str]) -> np.ndarray:
    if not texts:
        return np.zeros((0, EMBEDDING_DIM), dtype="float32")
    resp = client.embeddings.create(model=EMB_MODEL, input=texts)
    return np.array([d.embedding for d in resp.data], dtype="float32")

# --- session manifest (to skip re-indexing) ---
MANIFEST_CACHE: dict[str, dict] = {}   # { "file.pdf": {"mtime":..., "size":...} }

def delete_chunks_for(source_pdf: str):
    client_q.delete(
        collection_name=COLLECTION_NAME,
        points_selector=Filter(
            must=[FieldCondition(key="source_pdf", match=MatchValue(value=source_pdf))]
        )
    )

def index_folder_incremental(pdf_folder: str, max_chars=800, overlap=100) -> dict:
    ensure_collection()
    pdf_dir = Path(pdf_folder)
    files = sorted(pdf_dir.glob("*.pdf"))

    indexed, skipped = 0, 0
    for path in files:
        src = path.name
        fp = file_fingerprint(path)
        if MANIFEST_CACHE.get(src) == fp:
            skipped += 1
            continue  # unchanged this session

        delete_chunks_for(src)
        text = pdf_to_text(path)
        chunks = split_into_chunks(text, max_chars=max_chars, overlap=overlap)
        vecs = embed_texts(chunks)

        points = []
        for i, (chunk, vec) in enumerate(zip(chunks, vecs)):
            points.append(PointStruct(
                id=point_id_for(src, i),
                vector=vec.tolist(),
                payload={
                    "source_pdf": src,
                    "chunk_index": i,
                    "text": chunk,
                    "fingerprint": fp
                }
            ))
        if points:
            for j in range(0, len(points), 256):
                client_q.upsert(collection_name=COLLECTION_NAME, points=points[j:j+256])

        MANIFEST_CACHE[src] = fp
        indexed += 1

    return {"indexed": indexed, "skipped": skipped, "total_files": len(files)}

# --- Qdrant search wrapper ---
def qdrant_search(query: str, k: int = 5, filter_sources: list[str] | None = None):
    qvec = embed_texts([query])[0].tolist()
    q_filter = None
    if filter_sources:
        q_filter = Filter(must=[FieldCondition(key="source_pdf", match=MatchValue(value=filter_sources))])
    res = client_q.search(
        collection_name=COLLECTION_NAME,
        query_vector=qvec,
        limit=k,
        query_filter=q_filter,
        with_payload=True,
    )
    out = []
    for r in res:
        payload = r.payload or {}
        out.append(({"source_pdf": payload.get("source_pdf"), "text": payload.get("text","")}, float(r.score)))
    return out

# --- plug into agent hooks ---
def build_rag_index_from_folder(pdf_folder: str):
    return index_folder_incremental(pdf_folder)

def rag_search(query: str, k=5):
    return qdrant_search(query, k=k)


def index_health_check(collection: str = COLLECTION_NAME, sample_query: str = "Spirit Day"):
    """Print stats of the in-memory Qdrant index and show a sample search."""
    try:
        cols = client_q.get_collections().collections
    except Exception as e:
        print("❌ Could not reach Qdrant client:", e)
        return

    if not cols:
        print("❌ No collections in Qdrant client.")
        return

    col_names = [c.name for c in cols]
    if collection not in col_names:
        print(f"⚠️  Collection '{collection}' not found. Available: {col_names}")
        return

    # Show basic stats
    info = client_q.get_collection(collection)
    total_points = getattr(info, "points_count", None) or getattr(info, "vectors_count", 0)
    print(f"🗂️  Collection: {collection} — {total_points:,} vectors")

    # Fetch all payloads (safe even if empty)
    try:
        scroll_result, _ = client_q.scroll(collection_name=collection, with_payload=True, limit=10000)
    except Exception as e:
        print("⚠️  Scroll failed:", e)
        scroll_result = []

    payloads = [p.payload for p in scroll_result if p.payload]
    if not payloads:
        print("⚠️  No chunks indexed yet.")
        return

    # Count by file
    by_file = Counter(p.get("source_pdf", "unknown") for p in payloads)
    print("\n📄 Chunks per file:")
    for f, c in by_file.most_common():
        print(f"  {f:<40} {c:>4}")

    # Optional sample query
    if sample_query:
        print(f"\n🎯 Sample search: '{sample_query}'")
        try:
            results = qdrant_search(sample_query, k=3)
            if not results:
                print("   (no matches returned)")
            for i, (chunk, score) in enumerate(results, 1):
                snippet = chunk["text"].replace("\n", " ")[:180]
                print(f"\nTop {i}: {chunk['source_pdf']} (score={score:.3f})\n  {snippet}...")
        except Exception as e:
            print("⚠️  Sample search failed:", e)