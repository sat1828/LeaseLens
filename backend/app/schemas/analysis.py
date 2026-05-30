from pydantic import BaseModel, ConfigDict
from typing import Optional, List
from datetime import datetime
from uuid import UUID


class LeaseSummary(BaseModel):
    property_address: Optional[str] = None
    landlord_name: Optional[str] = None
    tenant_name: Optional[str] = None
    lease_start: Optional[str] = None
    lease_end: Optional[str] = None
    monthly_rent: Optional[float] = None
    currency: str = "INR"
    security_deposit: Optional[float] = None
    lease_type: str = "UNKNOWN"


class RiskSummary(BaseModel):
    critical_count: int = 0
    high_count: int = 0
    medium_count: int = 0
    low_count: int = 0
    missing_clauses: List[str] = []
    illegal_clauses: List[str] = []


class ClauseResult(BaseModel):
    clause_id: str
    clause_type: str
    verbatim_excerpt: Optional[str] = None
    risk_level: str
    legal_status: str
    plain_english: str
    legal_citation: Optional[str] = None
    negotiation_suggestion: Optional[str] = None
    fairness_weight: int = 5
    is_actionable: bool = True


class NegotiationPriority(BaseModel):
    priority: int
    clause_id: str
    reason: str
    suggested_response_letter_snippet: str


class AnalysisResult(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    analysis_id: UUID
    jurisdiction: str
    lease_summary: LeaseSummary
    fairness_score: int
    risk_summary: RiskSummary
    clauses: List[ClauseResult]
    top_3_negotiation_priorities: List[NegotiationPriority]
    counter_proposal_letter: str
    legal_disclaimer: str
    processing_time_ms: Optional[int] = None
    created_at: Optional[datetime] = None


class AnalysisListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    jurisdiction: str
    fairness_score: Optional[int] = None
    original_filename: Optional[str] = None
    lease_type: str
    created_at: datetime
