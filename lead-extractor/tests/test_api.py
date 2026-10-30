from app.main import app
from fastapi.testclient import TestClient

client = TestClient(app)


VALID_LEAD = {
    "name": "Ada Obi",
    "email": "ada@example.com",
    "phone": "+2348031234567",
    "company": "Obi Logistics",
    "interest": "Enterprise plan",
    "confidence": 0.95,
    "phone_status": "Valid",
}

VALID_METADATA = {
    "model": "fake-groq-model",
    "latency_ms": 123,
    "input_tokens": 100,
    "output_tokens": 50,
}


def test_health_endpoint():
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_extract_lead_returns_200(monkeypatch):
    async def fake_extract_lead(text):
        return VALID_LEAD, VALID_METADATA

    monkeypatch.setattr(
        "app.main.extract_lead",
        fake_extract_lead,
    )

    response = client.post(
        "/extract-lead",
        json={
            "text": "My name is Ada Obi from Obi Logistics. "
            "Email ada@example.com. Phone 08031234567. "
            "I want the enterprise plan."
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["lead"] == VALID_LEAD
    assert data["model"] == "fake-groq-model"
    assert data["latency_ms"] == 123
    assert data["input_tokens"] == 100
    assert data["output_tokens"] == 50


def test_extract_lead_returns_502_when_llm_fails(monkeypatch):
    async def fake_extract_lead(text):
        raise RuntimeError("Groq failed")

    monkeypatch.setattr(
        "app.main.extract_lead",
        fake_extract_lead,
    )

    response = client.post(
        "/extract-lead",
        json={
            "text": "My name is Ada Obi from Obi Logistics. " "Email ada@example.com."
        },
    )

    assert response.status_code == 502
    assert response.json() == {"detail": "Could not extract lead"}


def test_extract_lead_rejects_short_text():
    response = client.post(
        "/extract-lead",
        json={"text": "hi"},
    )

    assert response.status_code == 422


def test_extract_lead_rejects_missing_text():
    response = client.post(
        "/extract-lead",
        json={},
    )

    assert response.status_code == 422


def test_extract_lead_rejects_missing_body():
    response = client.post("/extract-lead")

    assert response.status_code == 422
