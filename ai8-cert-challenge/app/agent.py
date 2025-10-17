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

from config import LOCAL_TZ, PDF_DIR, COLLECTION_NAME, EMBEDDING_MODEL, EMBEDDING_DIM, AGENT_MODEL, AGENT_TEMPERATURE

# ---------- LangChain Agent Setup ----------
from langchain.tools import BaseTool
from langchain.agents import AgentExecutor, create_openai_tools_agent
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate

# Import from other modules
from .data_processing import ExtractedEvent, ExtractionBundle, pdf_to_text, guess_newsletter_date, _coerce_dt, dedupe_events, list_upcoming, list_deadlines, to_ics
from .rag import client_q, ensure_collection, split_into_chunks, file_fingerprint, point_id_for, embed_texts, MANIFEST_CACHE, delete_chunks_for, index_folder_incremental, qdrant_search, build_rag_index_from_folder, rag_search
from .tools import AGENT_STATE, TOOLS, tool, read_pdfs, extract_events, dedupe_tool, build_index_tool, parse_query, parse_query_tool, find_events_by_date, find_events_by_keyword, answer_query_tool, ensure_prepared

# Create LLM
llm = ChatOpenAI(model=AGENT_MODEL, temperature=AGENT_TEMPERATURE)

# Create tools manually (not using @tool decorator)
class SearchEventsTool(BaseTool):
    name: str = "search_events"
    description: str = "Search structured events by date or keywords. Use this for finding specific events."
    
    def _run(self, query: str) -> str:
        events = AGENT_STATE["all_events"]
        
        # Try to parse as date first
        try:
            from datetime import date
            target_date = date.fromisoformat(query)
            matching_events = [e for e in events if e.start and e.start.date() == target_date]
            if matching_events:
                result = f"Found {len(matching_events)} events on {query}:\n"
                for e in matching_events:
                    result += f"- {e.title} at {e.start.strftime('%I:%M %p') if e.start else 'All day'}"
                    if e.location:
                        result += f" ({e.location})"
                    result += "\n"
                return result
        except:
            pass
        
        # Search by keywords
        keywords = query.lower().split()
        matching_events = []
        for e in events:
            hay = " ".join([e.title, e.location or "", e.notes or "", " ".join(e.actions or [])]).lower()
            if any(k in hay for k in keywords):
                matching_events.append(e)
        
        if matching_events:
            result = f"Found {len(matching_events)} events matching '{query}':\n"
            for e in matching_events:
                result += f"- {e.title} on {e.start.strftime('%Y-%m-%d') if e.start else 'TBD'}"
                if e.location:
                    result += f" at {e.location}"
                result += "\n"
            return result
        else:
            return f"No events found matching '{query}'"

class SearchDocumentsTool(BaseTool):
    name: str = "search_documents"
    description: str = "Search raw document chunks using RAG. Use this for finding detailed information."
    
    def _run(self, query: str) -> str:
        try:
            snippets = rag_search(query, k=5)
            if not snippets:
                return f"No relevant information found for '{query}'"
            
            result = f"Found {len(snippets)} relevant document snippets for '{query}':\n\n"
            for i, (chunk, score) in enumerate(snippets, 1):
                result += f"{i}. From {chunk['source_pdf']} (relevance: {score:.3f}):\n"
                result += f"   {chunk['text'][:200]}...\n\n"
            return result
        except Exception as e:
            return f"Error searching documents: {str(e)}"

# Create tools list
tools = [SearchEventsTool(), SearchDocumentsTool()]

# Create prompt template
prompt = ChatPromptTemplate.from_messages([
    ("system", """You are a helpful school events assistant. You can search for events and documents to answer questions about school activities, dates, and instructions.
    
    Available tools:
    - search_events: Find events by date or keywords
    - search_documents: Search raw document content for detailed information
    
    Always use the appropriate tool to find information before answering. Be helpful and provide specific details when available."""),
    ("user", "{input}"),
    ("placeholder", "{agent_scratchpad}")
])

# Create agent
agent = create_openai_tools_agent(llm, tools, prompt)
agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True)

def ask(question: str, pdf_folder: str) -> str:
    """Agent-based question answering."""
    # Ensure data is prepared (keep your existing logic)
    if (AGENT_STATE.get("pdf_folder") != pdf_folder or 
        not AGENT_STATE.get("all_events") or 
        len(AGENT_STATE["all_events"]) == 0):
        ensure_prepared(pdf_folder)
    
    # Use agent to answer
    result = agent_executor.invoke({"input": question})
    return result["output"]