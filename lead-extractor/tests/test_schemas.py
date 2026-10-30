import pytest
from app.schemas import ExtractedLead
from pydantic import ValidationError


def make_lead_data(**overrides):
    data = {
        "name": "Ada Obi",
        "email": "ada@example.com",
        "phone": None,
        "company": "Obi Logistics",
        "interest": "Enterprise plan",
        "confidence": 0.95,
    }
    data.update(overrides)
    return data


def test_valid_local_nigerian_phone_is_normalized():
    lead = ExtractedLead(**make_lead_data(phone="08031234567"))

    assert lead.phone == "+2348031234567"
    assert lead.phone_status == "Valid"


def test_valid_international_nigerian_phone_is_accepted():
    lead = ExtractedLead(**make_lead_data(phone="+2348031234567"))

    assert lead.phone == "+2348031234567"
    assert lead.phone_status == "Valid"


def test_phone_with_spaces_and_dashes_is_cleaned():
    lead = ExtractedLead(**make_lead_data(phone="0803-123-4567"))

    assert lead.phone == "+2348031234567"


def test_invalid_phone_becomes_null():
    lead = ExtractedLead(**make_lead_data(phone="111111"))

    assert lead.phone is None
    assert (
        lead.phone_status
        == "Phone number was found but is not a valid Nigerian mobile number."
    )


def test_missing_phone_is_allowed():
    lead = ExtractedLead(**make_lead_data(phone=None))

    assert lead.phone is None
    assert (
        lead.phone_status
        == "Phone number was found but is not a valid Nigerian mobile number."
    )


def test_invalid_email_raises_validation_error():
    with pytest.raises(ValidationError):
        ExtractedLead(**make_lead_data(email="not-an-email"))


def test_confidence_above_one_raises_validation_error():
    with pytest.raises(ValidationError):
        ExtractedLead(**make_lead_data(confidence=1.5))


def test_confidence_below_zero_raises_validation_error():
    with pytest.raises(ValidationError):
        ExtractedLead(**make_lead_data(confidence=-0.2))
