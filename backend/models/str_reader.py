"""Pydantic models for the STR Test Reader mode.

Shapes follow the API Contract in PRD.md (source of truth).
"""
from typing import Literal, Optional

from pydantic import BaseModel

MatchVerdict = Literal["green", "yellow", "red"]


class STRReaderRequest(BaseModel):
    claimed_identity: str
    # locus -> allele pair(s), e.g. {"D5S818": ["11", "12"], "Amelogenin": ["X", "X"]}
    str_profile: dict[str, list[str]]


class MatchedLine(BaseModel):
    name: str
    rrid: Optional[str] = None


class LociAnalysis(BaseModel):
    total_loci: int
    matching_loci: int
    anomalous_loci: list[str] = []


class STRReaderResponse(BaseModel):
    match_verdict: MatchVerdict
    match_percentage: float  # 0–100
    matched_line: MatchedLine
    loci_analysis: LociAnalysis
    interpretation: str
    recommendation: str
    sources: list[str] = []  # e.g. ["clastr", "cellosaurus"]
