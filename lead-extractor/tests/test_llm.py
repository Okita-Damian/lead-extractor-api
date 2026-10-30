import asyncio
import json

import httpx
import pytest
from app.llm import extract_lead
from groq import APIStatusError


class FakeMessage:
    def __init__(self, content):
        self.content = content


class FakeChoice:
    def __init__(self, content):
        self.message = FakeMessage(content)


class FakeUsage:
    def __init__(self, prompt_tokens, completion_tokens):
        self.prompt_tokens = prompt_tokens
        self.completion_tokens = completion_tokens


class FakeResponse:
    def __init__(self, content, prompt_tokens=100, completion_tokens=50):
        self.choices = [FakeChoice(content)]
        self.usage = FakeUsage(prompt_tokens, completion_tokens)
        self.model = "fake-groq-model"


VALID_RESPONSE = json.dumps(
    {
        "name": "Ada Obi",
        "email": "ada@example.com",
        "phone": "08031234567",
        "company": "Obi Logistics",
        "interest": "Enterprise plan",
        "confidence": 0.95,
    }
)


def make_groq_error(status_code: int) -> APIStatusError:
    request = httpx.Request(
        "POST",
        "https://api.groq.com/openai/v1/chat/completions",
    )

    response = httpx.Response(
        status_code=status_code,
        request=request,
        json={"error": {"message": "Fake Groq error"}},
    )

    return APIStatusError(
        message="Fake Groq error",
        response=response,
        body=None,
    )


def test_extract_lead_returns_valid_lead_and_metadata(monkeypatch):
    fake_response = FakeResponse(VALID_RESPONSE)

    def fake_create(**kwargs):
        return fake_response

    monkeypatch.setattr(
        "app.llm.client.chat.completions.create",
        fake_create,
    )

    lead, metadata = asyncio.run(extract_lead("My name is Ada Obi."))

    assert lead.name == "Ada Obi"
    assert lead.email == "ada@example.com"
    assert lead.phone == "+2348031234567"
    assert lead.company == "Obi Logistics"
    assert lead.interest == "Enterprise plan"
    assert lead.confidence == 0.95

    assert metadata["model"] == "fake-groq-model"
    assert metadata["input_tokens"] == 100
    assert metadata["output_tokens"] == 50
    assert metadata["latency_ms"] >= 0


def test_extract_lead_retries_on_invalid_json(monkeypatch):
    calls = []

    async def fake_sleep(delay):
        return None

    def fake_create(**kwargs):
        calls.append(1)

        if len(calls) == 1:
            return FakeResponse("this is not json")

        return FakeResponse(VALID_RESPONSE)

    monkeypatch.setattr(
        "app.llm.client.chat.completions.create",
        fake_create,
    )

    monkeypatch.setattr(
        "app.llm.asyncio.sleep",
        fake_sleep,
    )

    lead, metadata = asyncio.run(extract_lead("My name is Ada Obi."))

    assert len(calls) == 2
    assert lead.name == "Ada Obi"
    assert metadata["model"] == "fake-groq-model"


def test_extract_lead_retries_on_rate_limit(monkeypatch):
    calls = []

    async def fake_sleep(delay):
        return None

    def fake_create(**kwargs):
        calls.append(1)

        if len(calls) == 1:
            raise make_groq_error(429)

        return FakeResponse(VALID_RESPONSE)

    monkeypatch.setattr(
        "app.llm.client.chat.completions.create",
        fake_create,
    )

    monkeypatch.setattr(
        "app.llm.asyncio.sleep",
        fake_sleep,
    )

    lead, metadata = asyncio.run(extract_lead("My name is Ada Obi."))

    assert len(calls) == 2
    assert lead.name == "Ada Obi"


def test_extract_lead_raises_immediately_on_invalid_api_key(monkeypatch):
    calls = []

    async def fake_sleep(delay):
        return None

    def fake_create(**kwargs):
        calls.append(1)
        raise make_groq_error(401)

    monkeypatch.setattr(
        "app.llm.client.chat.completions.create",
        fake_create,
    )

    monkeypatch.setattr(
        "app.llm.asyncio.sleep",
        fake_sleep,
    )

    with pytest.raises(APIStatusError):
        asyncio.run(extract_lead("My name is Ada Obi."))

    assert len(calls) == 1
