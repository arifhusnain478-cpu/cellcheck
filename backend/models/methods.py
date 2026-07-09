"""Pydantic models for the Methods Section Generator mode.

Shapes follow the API Contract in PRD.md (source of truth).
"""
from typing import Optional

from pydantic import BaseModel


class MethodsRequest(BaseModel):
    cell_line: str
    source: Optional[str] = None                 # e.g. "ATCC HTB-22"
    authentication_date: Optional[str] = None    # ISO date string
    authentication_service: Optional[str] = None
    mycoplasma_test_date: Optional[str] = None
    passage_range: Optional[str] = None          # e.g. "8-15"
    target_journal: Optional[str] = None


class ComplianceStatus(BaseModel):
    journal: Optional[str] = None
    compliant: bool = False
    missing_fields: list[str] = []


class MethodsResponse(BaseModel):
    methods_paragraph: str
    compliance_status: ComplianceStatus
    rrid_used: Optional[str] = None
    sources: list[str] = []  # e.g. ["cellosaurus", "journal_policy_reference"]
