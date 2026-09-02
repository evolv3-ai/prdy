import json

import httpx
import pytest

from prdy.llm import DEFAULT_MODEL, OPENROUTER_URL, LlmError, LlmGrade, build_messages, grade_with_model, parse_reply


def reply(content: str) -> httpx.Response:
    return httpx.Response(200, json={"choices": [{"message": {"role": "assistant", "content": content}}]})


def make_http(handler) -> httpx.Client:
    return httpx.Client(transport=httpx.MockTransport(handler))


def test_build_messages_includes_rubric_and_document():
    messages = build_messages("# My PRD")
    assert messages[0]["role"] == "system" and "JSON" in messages[0]["content"]
    assert "Sections" in messages[1]["content"] and "# My PRD" in messages[1]["content"]


def test_build_messages_truncates_huge_documents():
    assert len(build_messages("x" * 200_000)[1]["content"]) < 70_000


def test_parse_reply_plain_and_fenced():
    assert parse_reply('{"score": 72, "critique": "ok"}') == (72, "ok")
    assert parse_reply('```json\n{"score": "80", "critique": "fine"}\n```') == (80, "fine")


@pytest.mark.parametrize("bad", ["not json", '{"score": 150, "critique": "x"}', '{"critique": "x"}', '{"score": "high", "critique": "x"}'])
def test_parse_reply_rejects_malformed(bad):
    with pytest.raises((ValueError, KeyError, TypeError)):
        parse_reply(bad)


def test_grade_with_model_happy_path():
    seen = {}

    def handler(request):
        seen["url"] = str(request.url)
        seen["auth"] = request.headers["authorization"]
        seen["body"] = json.loads(request.content)
        return reply('{"score": 77, "critique": "Solid but thin on metrics."}')

    result = grade_with_model("# PRD", model="test/model", http=make_http(handler), api_key="k")
    assert result == LlmGrade(77, "Solid but thin on metrics.", "test/model")
    assert seen["url"] == OPENROUTER_URL and seen["auth"] == "Bearer k"
    assert seen["body"]["model"] == "test/model" and seen["body"]["messages"][1]["content"].endswith("# PRD")


def test_grade_with_model_retries_once_on_malformed_reply():
    calls = []

    def handler(request):
        calls.append(1)
        return reply("garbage") if len(calls) == 1 else reply('{"score": 60, "critique": "c"}')

    assert grade_with_model("t", http=make_http(handler), api_key="k").score == 60
    assert len(calls) == 2


def test_grade_with_model_records_null_after_two_malformed_replies():
    result = grade_with_model("t", http=make_http(lambda r: reply("garbage")), api_key="k")
    assert result.score is None and result.critique.startswith("malformed reply") and result.model == DEFAULT_MODEL


def test_grade_with_model_records_null_on_http_failure():
    result = grade_with_model("t", http=make_http(lambda r: httpx.Response(500, text="down")), api_key="k")
    assert result.score is None and "request failed" in result.critique


def test_grade_with_model_requires_key(monkeypatch):
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    with pytest.raises(LlmError):
        grade_with_model("t", http=make_http(lambda r: reply("{}")))
