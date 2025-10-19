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

from .data_processing import ExtractedEvent, ExtractionBundle, pdf_to_text, guess_newsletter_date, _coerce_dt, dedupe_events, list_upcoming, list_deadlines, to_ics

from .rag import build_rag_index_from_folder, rag_search, client_q, ensure_collection, split_into_chunks, file_fingerprint, point_id_for, embed_texts, MANIFEST_CACHE, delete_chunks_for, index_folder_incremental, qdrant_search
from .cohere_rag import build_cohere_index_from_folder, cohere_rag_search, cohere_health_check

# ---------- Agent state & tool registry ----------
AGENT_STATE = {"all_events": [], "pdf_folder": None}
TOOLS: Dict[str, Any] = {}
def tool(name):
    def deco(fn): TOOLS[name]=fn; return fn
    return deco

@tool("read_pdfs")
def read_pdfs(folder: str) -> Dict[str, Any]:
    # List PDFs in the folder
    pdf_dir = Path(folder)
    out = []
    for pdf in sorted(pdf_dir.glob("*.pdf")):
        out.append(pdf.name)
    return {"pdfs": out, "count": len(out)}

@tool("extract_events")
def extract_events(folder: str) -> Dict[str, Any]:
    events = extract_from_folder(Path(folder))
    AGENT_STATE["all_events"] = events
    return {"events": len(events), "sample_titles": [e.title for e in events[:5]]}

@tool("dedupe")
def dedupe_tool(_: str = "") -> Dict[str, Any]:
    ev = dedupe_events(AGENT_STATE["all_events"]); AGENT_STATE["all_events"] = ev
    return {"events": len(ev)}

@tool("build_index")
def build_index_tool(folder: str) -> dict:
    return build_rag_index_from_folder(folder)

@tool("build_cohere_index")
def build_cohere_index_tool(folder: str) -> dict:
    """Build RAG index using Cohere compression for better retrieval quality"""
    return build_cohere_index_from_folder(folder)

# ---- Query parsing ----
PARSE_SYSTEM = """You parse a parent's question about school events.
Output ONLY JSON:
{"intent":"date_query"|"event_query"|"instructions_query",
 "date": "YYYY-MM-DD" or null,
 "keywords":[str]}
- date_query: "what's on Oct 21"
- event_query: "when is Spirit Day"
- instructions_query: "any instructions for Spirit Day"
Assume America/Los_Angeles; resolve dates to YYYY-MM-DD."""

def parse_query(q: str) -> dict:
    msg = [{"role":"system","content":PARSE_SYSTEM},
           {"role":"user","content":q + "\nReturn ONLY JSON."}]
    resp = client.chat.completions.create(model="gpt-4o-mini", temperature=0, messages=msg)
    return json.loads(resp.choices[0].message.content.strip())

@tool("parse_query")
def parse_query_tool(query: str) -> dict:
    return parse_query(query)

# ---- Answer composition ----
ANSWER_SYSTEM = """You answer questions about school events using:
(1) structured events and (2) retrieved newsletter snippets.
- Be concise and exact for dates.
- For instructions, list short bullets and cite the source filename in parentheses.
- If unknown, say so."""

def find_events_by_date(events, iso_date: str):
    from datetime import date
    target = date.fromisoformat(iso_date)
    return [e for e in events if e.start and e.start.date() == target]

def find_events_by_keyword(events, keywords: List[str]):
    kws = [k.lower() for k in keywords]
    hits = []
    for e in events:
        hay = " ".join([e.title, e.location or "", e.notes or "", " ".join(e.actions or [])]).lower()
        if all(k in hay for k in kws):
            hits.append(e)
    if not hits:
        for e in events:
            hay = " ".join([e.title, e.location or "", e.notes or "", " ".join(e.actions or [])]).lower()
            if any(k in hay for k in kws):
                hits.append(e)
    return hits

@tool("answer_query")
def answer_query_tool(query: str) -> dict:
    intent = parse_query(query)
    intent_type = intent.get("intent")
    date_iso = intent.get("date")
    keywords = intent.get("keywords") or []
    events = AGENT_STATE["all_events"]

    selected: List[ExtractedEvent] = []
    if intent_type == "date_query" and date_iso:
        selected = find_events_by_date(events, date_iso)
        search_text = f"{date_iso} " + " ".join(keywords)
    elif intent_type in ("event_query","instructions_query") and keywords:
        selected = find_events_by_keyword(events, keywords)
        search_text = " ".join(keywords)
    else:
        search_text = query

    snippets = rag_search(search_text, k=5)

    context = {
        "query": query,
        "intent": intent,
        "events": [{
            "title": e.title,
            "start": e.start.isoformat() if e.start else None,
            "all_day": e.all_day,
            "location": e.location,
            "grades": e.grades,
            "actions": e.actions,
            "deadline": e.deadline.isoformat() if e.deadline else None,
            "source": e.source_pdf,
            "notes": e.notes,
            "confidence": e.confidence,
        } for e in selected],
        "snippets": [{
            "source": ch["source_pdf"],
            "similarity": sim,
            "text": ch["text"][:500]
        } for ch, sim in snippets]
    }

    prompt = f"""Answer the user's question using ONLY the context.
If giving instructions, list bullets and cite the source filename in parentheses.

CONTEXT:
{json.dumps(context, ensure_ascii=False)}
"""
    resp = client.chat.completions.create(
        model="gpt-4o-mini", temperature=0.2,
        messages=[{"role":"system","content":ANSWER_SYSTEM},
                  {"role":"user","content":prompt}]
    )
    answer = resp.choices[0].message.content.strip()
    return {"parsed_intent": intent,
            "events_matched": len(selected),
            "sources_consulted": list({s["source"] for s in context["snippets"]})[:3],
            "answer": answer}

@tool("answer_query_cohere")
def answer_query_cohere_tool(query: str) -> dict:
    """Answer queries using Cohere-compressed retrieval for better context quality"""
    intent = parse_query(query)
    intent_type = intent.get("intent")
    date_iso = intent.get("date")
    keywords = intent.get("keywords") or []
    events = AGENT_STATE["all_events"]

    selected: List[ExtractedEvent] = []
    if intent_type == "date_query" and date_iso:
        selected = find_events_by_date(events, date_iso)
        search_text = f"{date_iso} " + " ".join(keywords)
    elif intent_type in ("event_query","instructions_query") and keywords:
        selected = find_events_by_keyword(events, keywords)
        search_text = " ".join(keywords)
    else:
        search_text = query

    # Use Cohere-based search instead of regular RAG
    snippets = cohere_rag_search(search_text, k=5)

    context = {
        "query": query,
        "intent": intent,
        "events": [{
            "title": e.title,
            "start": e.start.isoformat() if e.start else None,
            "all_day": e.all_day,
            "location": e.location,
            "grades": e.grades,
            "actions": e.actions,
            "deadline": e.deadline.isoformat() if e.deadline else None,
            "source": e.source_pdf,
            "notes": e.notes,
            "confidence": e.confidence,
        } for e in selected],
        "snippets": [{"source": ch["source_pdf"], "similarity": sim, "text": ch["text"][:500], "compressed": ch.get("compressed", False)} for ch, sim in snippets]
    }

    prompt = f"""Answer the user's question using ONLY the context.
If giving instructions, list bullets and cite the source filename in parentheses.

CONTEXT:
{json.dumps(context, ensure_ascii=False)}
"""
    resp = client.chat.completions.create(
        model="gpt-4o-mini", temperature=0.2,
        messages=[{"role":"system","content":ANSWER_SYSTEM},
                  {"role":"user","content":prompt}]
    )
    answer = resp.choices[0].message.content.strip()
    return {"parsed_intent": intent,
            "events_matched": len(selected),
            "sources_consulted": list({s["source"] for s in context["snippets"]})[:3],
            "answer": answer,
            "retrieval_method": "cohere_compressed"}

# -------- Minimal planner (single-call convenience) --------
def ensure_prepared(pdf_folder: str):
    """Run once per session or when files change."""
    # Check if already prepared for this folder
    if (AGENT_STATE.get("pdf_folder") == pdf_folder and 
        AGENT_STATE.get("all_events") and 
        len(AGENT_STATE["all_events"]) > 0):
        print("✅ Data already prepared for this folder")
        return
    
    print("🔄 Preparing data...")
    read_pdfs(pdf_folder)
    extract_events(pdf_folder)
    dedupe_tool()
    build_index_tool(pdf_folder)
    AGENT_STATE["pdf_folder"] = pdf_folder
    print("✅ Data preparation complete")

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

# Add this import at the top with other imports
from .data_processing import ExtractedEvent, ExtractionBundle, pdf_to_text, guess_newsletter_date, _coerce_dt, dedupe_events, list_upcoming, list_deadlines, to_ics

# Add this function after the other tool functions
def extract_from_folder(pdf_dir: Path) -> List[ExtractedEvent]:
    all_events: List[ExtractedEvent] = []
    for pdf in tqdm(sorted(pdf_dir.glob("*.pdf"))):
        try:
            bundle = extract_events_from_pdf(pdf)
            all_events.extend(bundle.events)
        except Exception as e:
            print(f"[WARN] {pdf.name}: {e}")
    return sorted(dedupe_events(all_events), key=lambda e: e.start)

def extract_events_from_pdf(pdf_path: Path) -> ExtractionBundle:
    from openai import OpenAI
    client = OpenAI()
    
    text = pdf_to_text(pdf_path)
    default_dt = datetime.fromtimestamp(pdf_path.stat().st_mtime, tz=tz.gettz(LOCAL_TZ))
    nl_date = guess_newsletter_date(text, default_dt)

    # Call LLM directly
    prompt = f"{build_user_prompt(text, nl_date, pdf_path.name)}\n\nSchema:\n{SCHEMA_HINT}\n\nReturn ONLY JSON."
    resp = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role":"system","content":EXTRACTION_SYSTEM},{"role":"user","content":prompt}],
        temperature=0.1,
    )
    raw_json = resp.choices[0].message.content.strip()
    
    # Strip markdown code blocks if present
    if raw_json.startswith("```json"):
        raw_json = raw_json[7:]
    if raw_json.endswith("```"):
        raw_json = raw_json[:-3]
    raw_json = raw_json.strip()
    
    payload = json.loads(raw_json)

    events = []
    for ev in payload.get("events", []):
        ev["start"]    = _coerce_dt(ev.get("start"))
        ev["end"]      = _coerce_dt(ev.get("end"))
        ev["deadline"] = _coerce_dt(ev.get("deadline"))
        ev["source_pdf"] = ev.get("source_pdf") or pdf_path.name
        try:
            events.append(ExtractedEvent(**ev))
        except ValidationError as ve:
            print("[skip] invalid event:", ve)
    return ExtractionBundle(events=events, warnings=payload.get("warnings"))

# Add these missing functions
EXTRACTION_SYSTEM = """You extract school-related events from newsletter text.
Resolve relative dates against the provided Newsletter-Date (local timezone).
Output ONLY valid JSON per the schema. Lower confidence if unsure and include the source sentence in notes."""
SCHEMA_HINT = """
Return JSON:
{"events":[
  {"title":str,"start":ISO-8601 tz,"end":ISO-8601 tz|null,"all_day":bool,
   "location":str|null,"grades":[str]|null,"audience":[str]|null,
   "actions":[str]|null,"deadline":ISO-8601 tz|null,"source_pdf":str,
   "source_span":str|null,"confidence":float,"notes":str|null}],
 "warnings":[str]|null}
"""

def build_user_prompt(text: str, newsletter_date: datetime, source_pdf: str) -> str:
    return f"""Newsletter-Date: {newsletter_date.isoformat()}
Timezone: America/Los_Angeles
Rules:
- If only a date, set all_day=true and omit time.
- If time window present, set start/end and all_day=false.
- Include RSVP/payment deadlines and "what to bring/wear".

SOURCE FILE: {source_pdf}
TEXT:
\"\"\"{text[:12000]}\"\"\""""

def llm_json(system: str, user: str, schema_hint: str, client=None) -> str:
    if client is None:
        from openai import OpenAI
        client = OpenAI()
    
    prompt = f"{user}\n\nSchema:\n{schema_hint}\n\nReturn ONLY JSON."
    resp = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role":"system","content":system},{"role":"user","content":prompt}],
        temperature=0.1,
    )
    raw_json = resp.choices[0].message.content.strip()
    
    # Strip markdown code blocks if present
    if raw_json.startswith("```json"):
        raw_json = raw_json[7:]  # Remove ```json
    if raw_json.endswith("```"):
        raw_json = raw_json[:-3]  # Remove ```
    raw_json = raw_json.strip()
    
    return raw_json