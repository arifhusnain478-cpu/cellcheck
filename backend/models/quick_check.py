"""Pydantic models for the Quick Check mode.

Shapes follow the API Contract in PRD.md (source of truth).
"""
from typing import Literal, Optional

from pydantic import BaseModel

Verdict = Literal["green", "yellow", "red"]


class QuickCheckRequest(BaseModel):
    query: str  # cell line name, catalog #, or RRID


class Identity(BaseModel):
    correct_name: str
    rrid: Optional[str] = None
    true_origin: Optional[str] = None
    species: Optional[str] = None
    synonyms: list[str] = []
    source_lab: Optional[str] = None


class Retraction(BaseModel):
    title: str
    journal: Optional[str] = None
    year: Optional[int] = None
    reason: Optional[str] = None
    url: Optional[str] = None


class QuickCheckResponse(BaseModel):
    query: str
    verdict: Verdict
    identity: Identity
    retractions: list[Retraction] = []
    next_steps: list[str] = []
    sources: list[str] = []  # e.g. ["cellosaurus", "iclac", "semantic_scholar"]
