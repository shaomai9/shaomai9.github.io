from __future__ import annotations

import hashlib
import re


STOPWORDS = {
    "负责",
    "进行",
    "相关",
    "熟悉",
    "能够",
    "以及",
    "工作",
    "项目",
    "经验",
    "岗位",
    "要求",
    "职位",
    "描述",
    "简历",
    "以上",
    "优先",
    "具有",
    "掌握",
    "能力",
    "系统",
    "开发",
    "设计",
    "实现",
}


def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def clean_text(text: str) -> str:
    text = text.replace("\x00", " ")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = re.sub(r"[^\S\n]+", " ", text)
    return text.strip()


def split_paragraphs(text: str) -> list[str]:
    return [part.strip() for part in re.split(r"\n{2,}", text) if part.strip()]


def extract_keywords(text: str, limit: int = 12) -> list[str]:
    normalized = text.lower()
    english_tokens = re.findall(r"[a-zA-Z][a-zA-Z0-9\+\#\.\-]{1,20}", normalized)
    chinese_tokens = re.findall(r"[\u4e00-\u9fff]{2,8}", text)
    tokens = english_tokens + chinese_tokens
    counts: dict[str, int] = {}
    for token in tokens:
        if token in STOPWORDS:
            continue
        counts[token] = counts.get(token, 0) + 1
    ranked = sorted(counts.items(), key=lambda item: (-item[1], item[0]))
    return [token for token, _ in ranked[:limit]]
