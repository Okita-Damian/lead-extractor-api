import asyncio
import json
import random
import time

from groq import APIStatusError, APITimeoutError, Groq

from app.config import settings
from app.schemas import ExtractedLead
from app.system_prompt import SYSTEM_PROMPT

client = Groq(api_key=settings.groq_api_key)


RETRYABLE_STATUS_CODES = {429, 500, 502, 503, 504}

PROMPT = SYSTEM_PROMPT


async def extract_lead(text: str) -> tuple[ExtractedLead, dict]:
    started = time.perf_counter()
    last_error = None

    for attempt in range(settings.max_retries + 1):
        try:
            response = client.chat.completions.create(
                model=settings.groq_model,
                messages=[
                    {"role": "system", "content": PROMPT},
                    {"role": "user", "content": text},
                ],
                temperature=0,
                response_format={"type": "json_object"},
                timeout=settings.request_timeout_seconds,
            )

            raw = response.choices[0].message.content
            data = json.loads(raw)
            lead = ExtractedLead.model_validate(data)

            metadata = {
                "model": response.model,
                "latency_ms": int((time.perf_counter() - started) * 1000),
                "input_tokens": response.usage.prompt_tokens,
                "output_tokens": response.usage.completion_tokens,
            }

            return lead, metadata

        except (
            APITimeoutError,
            APIStatusError,
            json.JSONDecodeError,
            ValueError,
        ) as error:
            last_error = error

            if (
                isinstance(error, APIStatusError)
                and error.status_code not in RETRYABLE_STATUS_CODES
            ):
                raise

            if attempt < settings.max_retries:
                delay = (2**attempt) + random.uniform(0, 0.5)
                await asyncio.sleep(delay)

    raise RuntimeError(f"Lead extraction failed after retries: {last_error}")
