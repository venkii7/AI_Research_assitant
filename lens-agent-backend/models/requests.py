"""Request bodies using Pydantic v2 validation."""
from pydantic import BaseModel, field_validator
from typing import Optional, Literal
import re


class ProcessPaperRequest(BaseModel):
    """Submit a paper for Smart Brief generation."""

    source: str  # ArXiv ID, URL, or "upload" (file comes via multipart)
    user_preferences: Optional[dict] = {}

    @field_validator("source")
    @classmethod
    def validate_source(cls, v: str) -> str:
        v = v.strip()
        # Accept: bare ArXiv ID, arxiv.org URL, doi.org URL, http(s) URL
        patterns = [
            r"^\d{4}\.\d{4,5}(v\d+)?$",  # bare ArXiv ID
            r"^https?://arxiv\.org/(abs|pdf)/",  # ArXiv URL
            r"^https?://doi\.org/",  # DOI URL
            r"^https?://",  # any URL
            r"^upload$",  # file upload via multipart
        ]
        if not any(re.match(p, v) for p in patterns):
            raise ValueError("source must be an ArXiv ID, URL, DOI, or 'upload'")
        return v


class QueryRequest(BaseModel):
    """Ask the agent a question about a specific paper."""

    paper_id: str
    question: str
    conversation_history: list[dict] = []  # [{role, content}] for multi-turn

    @field_validator("question")
    @classmethod
    def validate_question(cls, v: str) -> str:
        if len(v.strip()) < 5:
            raise ValueError("question must be at least 5 characters")
        if len(v) > 1000:
            raise ValueError("question must be under 1000 characters")
        return v.strip()


class ExportRequest(BaseModel):
    """Generate a specific export format from a Smart Brief."""

    paper_id: str
    format: Literal["podcast_script", "tweet_thread", "slide_deck", "eli12", "investor_memo"]


class ConceptRequest(BaseModel):
    """Get a concept explanation at a specific depth."""

    concept: str
    paper_id: str
    depth: Literal["simple", "standard", "expert"] = "standard"
