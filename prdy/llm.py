"""Optional model grade through OpenRouter. Never replaces the rubric grade."""
from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass

import httpx

from prdy.grade import RUBRIC_TEXT

# Verify this id exists at https://openrouter.ai/models before the first live run; override with --model.
DEFAULT_MODEL = "anthropic/claude-sonnet-5"
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
MAX_CHARS = 60_000

_SYSTEM = (
    "You grade product requirements documents against a rubric. "
    'Reply with one JSON object only: {"score": <integer 0-100>, "critique": <two or three sentences>}.'
)
_FENCE = re.compile(r"^```(?:json)?\s*|\s*```$")


class LlmError(Exception):
    """Configuration problem (missing key). A usage error for the CLI."""


@dataclass(frozen=True)
class LlmGrade:
    score: int | None
    critique: str
    model: str


def build_messages(text: str) -> list[dict[str, str]]:
    return [
        {"role": "system", "content": _SYSTEM},
        {"role": "user", "content": f"Rubric:\n{RUBRIC_TEXT}\nDocument:\n{text[:MAX_CHARS]}"},
    ]


def parse_reply(content: str) -> tuple[int, str]:
    data = json.loads(_FENCE.sub("", content.strip()))
    score = int(data["score"])
    if not 0 <= score <= 100:
        raise ValueError(f"score out of range: {score}")
    return score, str(data["critique"])


def grade_with_model(
    text: str,
    model: str = DEFAULT_MODEL,
    http: httpx.Client | None = None,
    api_key: str | None = None,
) -> LlmGrade:
    key = api_key or os.environ.get("OPENROUTER_API_KEY")
    if not key:
        raise LlmError("OPENROUTER_API_KEY is not set")

    def _grade(http: httpx.Client) -> LlmGrade:
        payload = {"model": model, "messages": build_messages(text), "temperature": 0}
        headers = {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}
        last_error = "no reply"
        for _attempt in range(2):
            try:
                resp = http.post(OPENROUTER_URL, json=payload, headers=headers)
                resp.raise_for_status()
                content = resp.json()["choices"][0]["message"]["content"]
            except (httpx.HTTPError, KeyError, IndexError, TypeError, ValueError) as exc:
                last_error = f"request failed: {exc}"
                continue
            try:
                score, critique = parse_reply(content)
                return LlmGrade(score=score, critique=critique, model=model)
            except (ValueError, KeyError, TypeError) as exc:
                last_error = f"malformed reply: {exc}"
        return LlmGrade(score=None, critique=last_error, model=model)

    if http is not None:
        return _grade(http)
    with httpx.Client(timeout=120.0) as http:
        return _grade(http)
