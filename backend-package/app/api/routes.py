from __future__ import annotations

from fastapi import APIRouter, File, Form, HTTPException, UploadFile

from app.core.cache import cache_client
from app.core.config import get_settings
from app.models.schemas import JobMatchRequest, ResumeAnalyzeResponse
from app.services.matching import match_resume_with_job
from app.services.pdf_parser import parse_pdf_bytes
from app.services.resume_extractor import extract_resume_info
from app.utils.text import sha256_bytes, sha256_text

router = APIRouter(prefix="/api/v1", tags=["resume"])
CACHE_VERSION = "v3"


@router.get("/health")
async def healthcheck() -> dict[str, str]:
    return {"status": "ok"}


@router.post("/resumes/analyze", response_model=ResumeAnalyzeResponse)
async def analyze_resume(
    file: UploadFile = File(...),
    job_description: str | None = Form(None),
) -> ResumeAnalyzeResponse:
    settings = get_settings()
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only single PDF uploads are supported.")

    file_bytes = await file.read()
    if len(file_bytes) > settings.max_upload_size_mb * 1024 * 1024:
        raise HTTPException(status_code=413, detail="Uploaded PDF exceeds the configured size limit.")
    if not file_bytes:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")

    cache_seed = sha256_text(file.filename + ":" + sha256_bytes(file_bytes) + ":" + (job_description or ""))
    cache_key = f"resume-analysis:{CACHE_VERSION}:{cache_seed}"
    cached = cache_client.get(cache_key)
    if cached:
        return ResumeAnalyzeResponse(**cached, cache_hit=True)

    try:
        cleaned_text, pages = parse_pdf_bytes(file_bytes)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Failed to parse PDF: {exc}") from exc
    extracted = await extract_resume_info(cleaned_text)

    job_analysis = None
    match = None
    if job_description:
        job_analysis, match = await match_resume_with_job(extracted, job_description)

    response = ResumeAnalyzeResponse(
        resume_id=cache_seed[:16],
        file_name=file.filename,
        pages=pages,
        extracted=extracted,
        job_analysis=job_analysis,
        match=match,
        metadata={
            "llm_enabled": bool(settings.llm_api_key),
            "cache_backend": "redis" if settings.redis_url else "memory",
        },
    )
    cache_client.set(cache_key, response.model_dump(mode="json"), settings.cache_ttl_seconds)
    return response


@router.post("/jobs/match")
async def match_job(request: JobMatchRequest):
    extracted = request.extracted
    if not extracted:
        text = request.cleaned_resume_text or request.resume_text
        if not text:
            raise HTTPException(status_code=400, detail="Resume text or extracted result is required.")
        extracted = await extract_resume_info(text)

    job_analysis, match = await match_resume_with_job(extracted, request.job_description)
    return {
        "job_analysis": job_analysis.model_dump(),
        "match": match.model_dump(),
        "resume_summary": extracted.summary,
    }
