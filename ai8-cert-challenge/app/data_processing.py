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

from config import LOCAL_TZ, PDF_DIR

# ---------- Event schema ----------
class ExtractedEvent(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str
    start: datetime
    end: Optional[datetime] = None
    all_day: bool = False
    location: Optional[str] = None
    grades: Optional[List[str]] = None
    audience: Optional[List[str]] = None
    actions: Optional[List[str]] = None
    deadline: Optional[datetime] = None
    source_pdf: str
    source_span: Optional[str] = None
    confidence: float = 0.0
    notes: Optional[str] = None

class ExtractionBundle(BaseModel):
    events: List[ExtractedEvent]
    warnings: Optional[List[str]] = None

# ---------- PDF → text ----------
def pdf_to_text(pdf_path: Path) -> str:
    reader = PdfReader(str(pdf_path))
    return "\n".join([p.extract_text() or "" for p in reader.pages]).strip()

DATE_PAT = re.compile(r"(?:\b[A-Za-z]{3,9}\b \d{1,2}, \d{4})")
def guess_newsletter_date(text: str, default: datetime) -> datetime:
    m = DATE_PAT.search(text)
    if m:
        d = dateparser.parse(m.group(0), settings={"TIMEZONE":"UTC"})
        if d:
            return d.astimezone(tz.gettz(LOCAL_TZ)).replace(hour=9, minute=0, second=0, microsecond=0)
    return default

def _coerce_dt(x):
    if not x: return None
    d = dateparser.parse(x)
    if not d: return None
    if not d.tzinfo: d = d.replace(tzinfo=tz.gettz(LOCAL_TZ))
    return d.astimezone(tz.gettz(LOCAL_TZ))

# ---------- Helpers ----------
def dedupe_events(events: List[ExtractedEvent]) -> List[ExtractedEvent]:
    seen: Dict[tuple, ExtractedEvent] = {}
    for ev in events:
        k = (ev.title.strip().lower(),
             ev.start.date().isoformat() if ev.start else "none",
             (ev.location or "").strip().lower())
        prev = seen.get(k)
        if not prev or ev.confidence > prev.confidence:
            seen[k] = ev
    return list(seen.values())

def list_upcoming(events: List[ExtractedEvent], days: int = 14, grade: Optional[str] = None):
    now = datetime.now(tz=tz.gettz(LOCAL_TZ)); until = now + timedelta(days=days)
    out = []
    for e in events:
        if not e.start: continue
        if now <= e.start <= until and (not grade or (e.grades and grade in e.grades)):
            out.append(e)
    return out

def list_deadlines(events: List[ExtractedEvent], days:int=14):
    now = datetime.now(tz=tz.gettz(LOCAL_TZ)); until = now + timedelta(days=days)
    return [e for e in events if e.deadline and now <= e.deadline <= until]

def to_ics(events: List[ExtractedEvent], calendar_name="School Events") -> bytes:
    cal = Calendar(); cal.add("prodid","-//ParentHelper//School Calendar//EN"); cal.add("version","2.0")
    cal.add("X-WR-CALNAME", calendar_name)
    for e in events:
        ve = ICS(); ve.add("uid", e.id); ve.add("summary", e.title)
        if e.all_day:
            ve.add("dtstart", e.start.date())
            if e.end: ve.add("dtend", e.end.date())
        else:
            ve.add("dtstart", e.start); ve.add("dtend", e.end or (e.start + timedelta(hours=1)))
        if e.location: ve.add("location", e.location)
        desc = []
        if e.actions:  desc.append("Actions: " + ", ".join(e.actions))
        if e.grades:   desc.append("Grades: " + ", ".join(e.grades))
        if e.audience: desc.append("Audience: " + ", ".join(e.audience))
        if e.deadline: desc.append("Deadline: " + e.deadline.isoformat())
        desc.append("Source: " + e.source_pdf)
        if e.notes:    desc.append("Notes: " + e.notes)
        ve.add("description", "\n".join(desc)); cal.add_component(ve)
    return cal.to_ical()