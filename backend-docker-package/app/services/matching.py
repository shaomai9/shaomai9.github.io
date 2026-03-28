from __future__ import annotations

import re

from app.models.schemas import KeywordAnalysis, MatchBreakdown, ResumeExtractionResult
from app.services.llm import llm_client
from app.utils.text import extract_keywords


def _ensure_list(value) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    if isinstance(value, str):
        return [part.strip() for part in value.replace("|", ",").split(",") if part.strip()]
    return [str(value).strip()]


async def analyze_job_description(job_description: str) -> KeywordAnalysis:
    payload = None
    if llm_client.enabled:
        payload = await llm_client.json_completion(
            "你是招聘分析助手。请从岗位描述中提取关键词并总结岗位要求。"
            "返回严格 JSON，字段只有 keywords 和 summary。"
            "keywords 必须是数组，summary 必须使用中文。",
            job_description[:8000],
        )
    if payload:
        return KeywordAnalysis(
            keywords=_ensure_list(payload.get("keywords")),
            summary=payload.get("summary") or "",
        )
    keywords = extract_keywords(job_description, limit=15)
    return KeywordAnalysis(keywords=keywords, summary=job_description[:200])


def _normalize_items(items: list[str]) -> set[str]:
    return {item.strip().lower() for item in items if item and item.strip()}


def _has_chinese(text: str) -> bool:
    return bool(re.search(r"[\u4e00-\u9fff]", text or ""))


async def _translate_to_chinese_if_needed(text: str) -> str:
    if not text or _has_chinese(text) or not llm_client.enabled:
        return text

    payload = await llm_client.json_completion(
        "你是翻译助手。请把用户给出的内容翻译成自然、简洁的简体中文。"
        "返回严格 JSON，字段只有 text。",
        text[:4000],
    )
    translated = (payload or {}).get("text")
    return translated or text


async def match_resume_with_job(
    extracted: ResumeExtractionResult,
    job_description: str,
) -> tuple[KeywordAnalysis, MatchBreakdown]:
    job_analysis = await analyze_job_description(job_description)

    resume_keywords = _normalize_items(extracted.basics.skills + extract_keywords(extracted.cleaned_text, limit=20))
    job_keywords = _normalize_items(job_analysis.keywords)
    matched = sorted(resume_keywords & job_keywords)
    missing = sorted(job_keywords - resume_keywords)

    skill_match_score = round((len(matched) / max(len(job_keywords), 1)) * 100, 2)

    resume_text = extracted.cleaned_text.lower()
    job_text = job_description.lower()
    experience_hits = sum(
        1
        for token in ["项目", "架构", "系统设计", "python", "java", "管理", "ai", "机器学习"]
        if token in resume_text and token in job_text
    )
    experience_relevance_score = round(min(100.0, 45.0 + experience_hits * 8.0), 2)

    has_education = 100.0 if extracted.basics.education else 60.0
    overall = round(skill_match_score * 0.5 + experience_relevance_score * 0.35 + has_education * 0.15, 2)

    rationale = (
        f"简历命中 {len(matched)} 个岗位关键词，技能匹配度为 {skill_match_score} 分；"
        f"经验相关性为 {experience_relevance_score} 分；"
        f"教育背景得分为 {has_education} 分。"
    )

    if llm_client.enabled:
        payload = await llm_client.json_completion(
            "你是中文招聘评估助手。请根据简历与岗位描述给出匹配评分。"
            "返回严格 JSON，字段只有 overall_score 和 rationale。"
            "overall_score 必须是 0 到 100 的数字，rationale 必须使用简体中文，"
            "长度控制在 2 到 4 句话，说明技能、经验和岗位匹配情况。",
            f"简历摘要：{extracted.summary}\n"
            f"简历技能：{', '.join(extracted.basics.skills)}\n"
            f"简历教育：{'；'.join(extracted.basics.education)}\n"
            f"岗位描述：{job_description[:6000]}",
        )
        if payload:
            overall = float(payload.get("overall_score", overall))
            rationale = payload.get("rationale") or rationale

    rationale = await _translate_to_chinese_if_needed(rationale)

    return job_analysis, MatchBreakdown(
        overall_score=overall,
        skill_match_score=skill_match_score,
        experience_relevance_score=experience_relevance_score,
        education_score=has_education,
        matched_keywords=matched,
        missing_keywords=missing[:15],
        rationale=rationale,
    )
