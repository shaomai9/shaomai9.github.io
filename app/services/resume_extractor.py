from __future__ import annotations

import re

from app.models.schemas import ContactInfo, ResumeBasics, ResumeExtractionResult
from app.services.llm import llm_client
from app.utils.text import extract_keywords, split_paragraphs


PHONE_PATTERN = re.compile(r"(?<!\d)(?:\+?86[- ]?)?1[3-9]\d{9}(?!\d)")
EMAIL_PATTERN = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")

SKILL_HINTS = {
    "python",
    "java",
    "golang",
    "go",
    "javascript",
    "typescript",
    "react",
    "vue",
    "fastapi",
    "flask",
    "django",
    "mysql",
    "postgresql",
    "redis",
    "docker",
    "kubernetes",
    "linux",
    "算法",
    "机器学习",
    "深度学习",
    "nlp",
    "llm",
    "ai",
}


def _ensure_list(value) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    if isinstance(value, str):
        parts = re.split(r"[,/;\n|、，；]+", value)
        return [part.strip() for part in parts if part.strip()]
    return [str(value).strip()]


def _find_line_by_label(text: str, labels: list[str]) -> str | None:
    for line in text.splitlines():
        normalized = line.strip()
        if any(label in normalized for label in labels):
            return normalized
    return None


def _extract_name(text: str) -> str | None:
    for label in ["姓名", "Name", "name"]:
        line = _find_line_by_label(text, [label])
        if line:
            parts = re.split(r"[:：\s]+", line, maxsplit=1)
            if len(parts) > 1 and parts[1].strip():
                return parts[1].strip()

    first_lines = [line.strip() for line in text.splitlines() if line.strip()][:5]
    for line in first_lines:
        if 1 < len(line) <= 20 and not PHONE_PATTERN.search(line) and not EMAIL_PATTERN.search(line):
            if re.fullmatch(r"[\u4e00-\u9fffA-Za-z·\s]{2,20}", line):
                return line
    return None


def heuristic_extract(text: str) -> ResumeExtractionResult:
    phone_match = PHONE_PATTERN.search(text)
    email_match = EMAIL_PATTERN.search(text)
    address_line = _find_line_by_label(text, ["地址", "现居", "居住地", "location", "Address"])
    target_line = _find_line_by_label(text, ["求职意向", "意向岗位", "目标岗位", "Job Target"])
    salary_line = _find_line_by_label(text, ["期望薪资", "薪资要求", "Expected Salary"])
    years_line = _find_line_by_label(text, ["工作年限", "工作经验", "Years of Experience"])

    paragraphs = split_paragraphs(text)
    education = [p for p in paragraphs if any(token in p for token in ["大学", "学院", "硕士", "本科", "博士", "学历"])]
    projects = [p for p in paragraphs if any(token in p for token in ["项目", "负责", "上线", "优化", "Project"])]
    keywords = extract_keywords(text, limit=20)
    skills = [token for token in keywords if token.lower() in SKILL_HINTS or token in SKILL_HINTS]

    contact = ContactInfo(
        name=_extract_name(text),
        phone=phone_match.group(0) if phone_match else None,
        email=email_match.group(0) if email_match else None,
        address=address_line,
    )
    basics = ResumeBasics(
        target_position=target_line,
        expected_salary=salary_line,
        work_years=years_line,
        education=education[:3],
        projects=projects[:3],
        skills=skills[:12],
    )
    summary = paragraphs[0][:300] if paragraphs else text[:300]

    return ResumeExtractionResult(
        contact=contact,
        basics=basics,
        summary=summary,
        raw_text=text,
        cleaned_text=text,
        extraction_source="heuristic",
    )


async def ai_extract(text: str) -> ResumeExtractionResult | None:
    system_prompt = (
        "You extract structured resume data. "
        "Return strict JSON with keys: "
        "contact{name,phone,email,address}, basics{target_position,expected_salary,work_years,education,projects,skills}, summary."
    )
    user_prompt = f"Resume text:\n{text[:12000]}"
    payload = await llm_client.json_completion(system_prompt, user_prompt)
    if not payload:
        return None

    contact_payload = payload.get("contact", {})
    basics_payload = payload.get("basics", {})
    return ResumeExtractionResult(
        contact=ContactInfo(
            name=contact_payload.get("name"),
            phone=contact_payload.get("phone"),
            email=contact_payload.get("email"),
            address=contact_payload.get("address"),
        ),
        basics=ResumeBasics(
            target_position=basics_payload.get("target_position"),
            expected_salary=basics_payload.get("expected_salary"),
            work_years=basics_payload.get("work_years"),
            education=_ensure_list(basics_payload.get("education")),
            projects=_ensure_list(basics_payload.get("projects")),
            skills=_ensure_list(basics_payload.get("skills")),
        ),
        summary=payload.get("summary") or "",
        raw_text=text,
        cleaned_text=text,
        extraction_source="llm",
    )


async def extract_resume_info(text: str) -> ResumeExtractionResult:
    ai_result = await ai_extract(text)
    if ai_result:
        return ai_result
    return heuristic_extract(text)
