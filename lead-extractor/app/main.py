import logging
import uuid

from fastapi import FastAPI, HTTPException

from app.llm import extract_lead
from app.logging_config import configure_logging
from app.schemas import LeadExtractionRequest, LeadExtractionResponse

configure_logging()
logger = logging.getLogger("lead_extractor")

app = FastAPI(title="Lead Extractor API")


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.post("/extract-lead", response_model=LeadExtractionResponse)
async def extract_lead_endpoint(request: LeadExtractionRequest):
    request_id = str(uuid.uuid4())

    try:
        lead, metadata = await extract_lead(request.text)
    except Exception:
        logger.exception("Lead extraction failed", extra={"request_id": request_id})
        raise HTTPException(status_code=502, detail="Could not extract lead")

    logger.info(
        "Lead extracted",
        extra={
            "request_id": request_id,
            "model": metadata["model"],
            "latency_ms": metadata["latency_ms"],
            "input_tokens": metadata["input_tokens"],
            "output_tokens": metadata["output_tokens"],
        },
    )

    return LeadExtractionResponse(
        lead=lead,
        **metadata,
    )
