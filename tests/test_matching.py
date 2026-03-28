import asyncio

from app.models.schemas import ContactInfo, ResumeBasics, ResumeExtractionResult
from app.services.llm import llm_client
from app.services.matching import match_resume_with_job


def build_resume() -> ResumeExtractionResult:
    return ResumeExtractionResult(
        contact=ContactInfo(name="张三"),
        basics=ResumeBasics(
            target_position="Python后端工程师",
            work_years="3年",
            education=["本科 - 计算机科学"],
            projects=["负责 AI 招聘平台后端开发"],
            skills=["python", "fastapi", "redis", "mysql"],
        ),
        summary="3年 Python 后端经验，参与 AI 平台建设。",
        raw_text="python fastapi redis mysql ai",
        cleaned_text="python fastapi redis mysql ai",
        extraction_source="heuristic",
    )


def test_match_resume_with_job():
    original_key = llm_client.settings.llm_api_key
    llm_client.settings.llm_api_key = None
    try:
        job_analysis, match = asyncio.run(
            match_resume_with_job(
                build_resume(),
                "负责 Python 后端开发，熟悉 FastAPI、Redis、MySQL，有 AI 项目经验优先。",
            )
        )
    finally:
        llm_client.settings.llm_api_key = original_key
    assert "python" in [item.lower() for item in job_analysis.keywords]
    assert match.overall_score > 0
    assert "python" in match.matched_keywords
