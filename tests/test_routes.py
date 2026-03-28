from fastapi.testclient import TestClient

from app.main import app
from app.models.schemas import ContactInfo, MatchBreakdown, KeywordAnalysis, ResumeBasics, ResumeExtractionResult


def test_resume_analyze_accepts_job_description_form(monkeypatch):
    def fake_parse_pdf_bytes(file_bytes: bytes):
        return "John Doe python fastapi redis", 1

    async def fake_extract_resume_info(text: str):
        return ResumeExtractionResult(
            contact=ContactInfo(name="John Doe", email="john@example.com"),
            basics=ResumeBasics(
                target_position="Backend Engineer",
                work_years="3 years",
                education=["BS Computer Science"],
                skills=["python", "fastapi", "redis"],
            ),
            summary="Backend engineer with Python experience.",
            raw_text=text,
            cleaned_text=text,
            extraction_source="heuristic",
        )

    async def fake_match_resume_with_job(extracted, job_description: str):
        assert "FastAPI" in job_description
        return (
            KeywordAnalysis(keywords=["python", "fastapi"], summary="backend role"),
            MatchBreakdown(
                overall_score=88.0,
                skill_match_score=90.0,
                experience_relevance_score=85.0,
                education_score=100.0,
                matched_keywords=["python", "fastapi"],
                missing_keywords=[],
                rationale="Strong backend match.",
            ),
        )

    monkeypatch.setattr("app.api.routes.parse_pdf_bytes", fake_parse_pdf_bytes)
    monkeypatch.setattr("app.api.routes.extract_resume_info", fake_extract_resume_info)
    monkeypatch.setattr("app.api.routes.match_resume_with_job", fake_match_resume_with_job)

    client = TestClient(app)
    response = client.post(
        "/api/v1/resumes/analyze",
        files={"file": ("resume.pdf", b"%PDF-1.4 fake pdf", "application/pdf")},
        data={"job_description": "Need Python and FastAPI experience."},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["match"]["overall_score"] == 88.0
    assert body["job_analysis"]["keywords"] == ["python", "fastapi"]
