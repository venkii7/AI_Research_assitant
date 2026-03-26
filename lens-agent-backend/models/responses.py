"""Response shapes using Pydantic v2."""
from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class StatCard(BaseModel):
    """A single stat card in the Smart Brief."""

    label: str
    value: str
    sub: str


class StorySection(BaseModel):
    """The 4-part narrative structure of a paper."""

    problem: str
    method: str
    results: str
    significance: str


class SmartBrief(BaseModel):
    """Complete Smart Brief JSON schema."""

    title: str
    authors: str
    institution: str
    year: str
    paper_category: str
    tldr: str
    stat_cards: list[StatCard]
    story: StorySection
    concepts: list[str]
    concept_explanations: dict[str, str] = {}
    removed_sections: list[str] = []
    quality_score: Optional[float] = None


class PaperResponse(BaseModel):
    """Response for a paper record."""

    id: str
    user_id: str
    arxiv_id: Optional[str] = None
    title: Optional[str] = None
    authors: Optional[str] = None
    status: str  # queued | processing | done | failed
    smart_brief: Optional[SmartBrief] = None
    processing_time_ms: Optional[int] = None
    created_at: datetime
    updated_at: datetime


class JobResponse(BaseModel):
    """Response when submitting a paper for processing."""

    job_id: str
    paper_id: str
    status: str
    stream_url: str  # full URL to the SSE endpoint


class QueryResponse(BaseModel):
    """Response from a query."""

    answer: str
    sources: list[str] = []  # section references from the paper
    model_used: str


class ExportResponse(BaseModel):
    """Response from export generation."""

    paper_id: str
    format: str
    content: str
    word_count: int
    created_at: datetime


class ConceptExplanation(BaseModel):
    """Response for a concept explanation."""

    concept: str
    depth: str
    explanation: str
    analogy: Optional[str] = None
    sources: list[str] = []
    cached: bool


class HealthResponse(BaseModel):
    """Health check response."""

    status: str
    environment: str
    redis: str
    supabase: str
    version: str = "1.0.0"
