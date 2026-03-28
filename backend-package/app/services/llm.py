from __future__ import annotations

import json
import re
from typing import Any

import httpx

from app.core.config import get_settings


class LLMClient:
    def __init__(self) -> None:
        self.settings = get_settings()

    @property
    def enabled(self) -> bool:
        return bool(self.settings.llm_api_key)

    @staticmethod
    def _extract_json(content: str) -> dict[str, Any]:
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            fenced_match = re.search(r"```(?:json)?\s*(\{.*\})\s*```", content, re.DOTALL)
            if fenced_match:
                return json.loads(fenced_match.group(1))
            brace_match = re.search(r"(\{.*\})", content, re.DOTALL)
            if brace_match:
                return json.loads(brace_match.group(1))
            raise

    async def json_completion(self, system_prompt: str, user_prompt: str) -> dict[str, Any] | None:
        if not self.enabled:
            return None

        payload = {
            "model": self.settings.llm_model,
            "response_format": {"type": "json_object"},
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "temperature": 0.2,
        }
        headers = {
            "Authorization": f"Bearer {self.settings.llm_api_key}",
            "Content-Type": "application/json",
        }

        async with httpx.AsyncClient(timeout=self.settings.llm_timeout_seconds) as client:
            response = await client.post(
                self.settings.llm_api_url,
                headers=headers,
                json=payload,
            )
            response.raise_for_status()
            data = response.json()
            content = data["choices"][0]["message"]["content"]
            return self._extract_json(content)


llm_client = LLMClient()
