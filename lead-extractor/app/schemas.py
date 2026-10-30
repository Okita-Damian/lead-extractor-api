import re

from pydantic import (
    BaseModel,
    EmailStr,
    Field,
    field_validator,
    model_validator,
)


class LeadExtractionRequest(BaseModel):
    text: str = Field(min_length=10, max_length=8000)


class ExtractedLead(BaseModel):
    name: str | None = None
    email: EmailStr | None = None
    phone: str | None = None
    company: str | None = None
    interest: str | None = None
    confidence: float = Field(ge=0, le=1)
    phone_status: str | None = None

    @field_validator("phone")
    @classmethod
    def validate_nigerian_phone(cls, value: str | None) -> str | None:
        if value is None:
            return None

        cleaned = re.sub(r"[^\d+]", "", value)

        local_pattern = r"^(070|080|081|090|091)\d{8}$"
        international_pattern = r"^\+234\d{10}$"

        if re.fullmatch(local_pattern, cleaned):
            return "+234" + cleaned[1:]

        if re.fullmatch(international_pattern, cleaned):
            return cleaned

        return None

    @model_validator(mode="after")
    def set_phone_status(self):
        if self.phone:
            self.phone_status = "Valid"
        else:
            self.phone_status = (
                "Phone number was found but is not a valid Nigerian mobile number."
            )

        return self


class LeadExtractionResponse(BaseModel):
    lead: ExtractedLead
    model: str
    latency_ms: int
    input_tokens: int
    output_tokens: int
    estimated_cost_usd: float | None = None
