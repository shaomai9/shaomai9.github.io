from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class ContactInfo(BaseModel):
    name: str | None = None
    phone: str | None = None
    email: str | None = None
    address: str | None = None


class ResumeBasics(BaseModel):
    target_position: str | None = None
    expected_salary: str | None = None
    work_years: str | None = None
    education: list[str] = Field(default_factory=list)
    projects: list[str] = Field(default_factory=list)
    skills: list[str] = Field(default_factory=list)


class ResumeExtractionResult(BaseModel):
    contact: ContactInfo
    basics: ResumeBasics
    summary: str = ""
    raw_text: str = ""
    cleaned_text: str = ""
    extraction_source: str = "heuristic"


class KeywordAnalysis(BaseModel):
    keywords: list[str] = Field(default_factory=list)
    summary: str = ""


class MatchBreakdown(BaseModel):
    overall_score: float
    skill_match_score: float
    experience_relevance_score: float
    education_score: float
    matched_keywords: list[str] = Field(default_factory=list)
    missing_keywords: list[str] = Field(default_factory=list)
    rationale: str = ""


class ResumeAnalyzeResponse(BaseModel):
    resume_id: str
    file_name: str
    pages: int
    cache_hit: bool = False
    extracted: ResumeExtractionResult
    job_analysis: KeywordAnalysis | None = None
    match: MatchBreakdown | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class JobMatchRequest(BaseModel):
    resume_text: str | None = None
    cleaned_resume_text: str | None = None
    extracted: ResumeExtractionResult | None = None
    job_description: str = Field(min_length=1)
