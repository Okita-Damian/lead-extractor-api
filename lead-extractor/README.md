# Lead Extractor API

A small AI-powered REST API that extracts structured lead information from unstructured text such as emails, contact-form messages, and support requests.

It uses **FastAPI**, **Pydantic**, and the **Groq API** to turn messy text into clean, validated JSON.

## Features

- Extract name, email, phone, company, interest, and confidence from text
- Built with FastAPI and Pydantic v2
- Uses Groq’s `openai/gpt-oss-20b` model
- Validates LLM output before returning it
- Validates Nigerian mobile numbers
- Normalizes local Nigerian numbers to international format
- Handles invalid JSON, timeouts, rate limits, and provider errors
- Retries temporary Groq failures with exponential backoff
- Logs request ID, latency, model, and token usage
- Includes offline unit tests with mocked Groq responses

## API Endpoints

### `GET /health`

Checks that the service is running.

**Response:**

```json
{
  "status": "ok"
}
```

### `POST /extract-lead`

Extracts lead information from a text message.

#### Request

```json
{
  "text": "Hello, my name is Ada Obi from Obi Logistics. My email is ada@example.com. I am interested in your enterprise plan."
}
```

#### Successful response

```json
{
  "lead": {
    "name": "Ada Obi",
    "email": "ada@example.com",
    "phone": null,
    "company": "Obi Logistics",
    "interest": "Enterprise plan",
    "confidence": 0.95,
    "phone_status": "Phone number was found but is not a valid Nigerian mobile number."
  },
  "model": "openai/gpt-oss-20b",
  "latency_ms": 545,
  "input_tokens": 237,
  "output_tokens": 151,
  "estimated_cost_usd": null
}
```

#### Validation error

If `text` is missing, empty, or shorter than 10 characters:

```json
{
  "detail": [
    {
      "type": "string_too_short",
      "loc": ["body", "text"],
      "msg": "String should have at least 10 characters",
      "input": "hi"
    }
  ]
}
```

#### LLM failure

If Groq fails after retries:

```json
{
  "detail": "Could not extract lead"
}
```

## Nigerian Phone Validation

The API accepts Nigerian mobile numbers in these formats:

```text
08031234567
07031234567
08101234567
09012345678
09123456789
+2348031234567
```

Local numbers are normalized to international format:

```text
08031234567 -> +2348031234567
```

Invalid numbers such as `111111` are returned as `null`.

## Project Structure

```text
lead-extractor/
├── app/
│   ├── __init__.py
│   ├── main.py
│   ├── schemas.py
│   ├── llm.py
│   ├── config.py
│   ├── system_prompt.py
│   └── logging_config.py
├── tests/
│   ├── __init__.py
│   ├── test_api.py
│   ├── test_llm.py
│   ├── test_schemas.py
│
├── .env
├── .gitignore
├── requirements.txt
└── README.md
```

## Tech Stack

| Layer            | Technology           |
| ---------------- | -------------------- |
| Language         | Python 3.12+         |
| API framework    | FastAPI              |
| Data validation  | Pydantic v2          |
| LLM provider     | Groq                 |
| Model            | `openai/gpt-oss-20b` |
| Testing          | pytest               |
| API testing      | FastAPI TestClient   |
| Configuration    | pydantic-settings    |
| Containerization | Docker               |

## Setup

### 1. Clone the repository

```bash
git clone <your-repository-url>
cd lead-extractor
```

### 2. Create a virtual environment

```bash
python -m venv .venv
```

Activate it:

**Windows Command Prompt:**

```cmd
.venv\Scripts\activate
```

**macOS/Linux:**

```bash
source .venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment variables

Create a `.env` file in the project root:

```env
GROQ_API_KEY=your_groq_api_key_here
GROQ_MODEL=openai/gpt-oss-20b
```

Get a Groq API key from the [Groq Console](https://console.groq.com/keys).

Never commit your real `.env` file.

## Run the API

```bash
uvicorn app.main:app --reload
```

Open the interactive API documentation:

```text
http://127.0.0.1:8000/docs
```

Health check:

```text
http://127.0.0.1:8000/health
```

## Run Tests

Run all tests:

```bash
python -m pytest
```

Run only schema tests:

```bash
python -m pytest tests/test_schemas.py
```

Run only LLM tests:

```bash
python -m pytest tests/test_llm.py
```

Run only API tests:

```bash
python -m pytest tests/test_api.py
```

The LLM tests use mocked Groq responses, so they do not consume API quota or require internet access.

## Run with Docker

Build the image:

```bash
docker build -t lead-extractor .
```

Run the container:

```bash
docker run --env-file .env -p 8000:8000 lead-extractor
```

Then open:

```text
http://localhost:8000/docs
```

## Error Handling

| Error case                                     | Behavior                                          |
| ---------------------------------------------- | ------------------------------------------------- |
| Missing or invalid request body                | `422 Validation Error`                            |
| Groq returns invalid JSON                      | Retries, then raises an internal extraction error |
| Groq returns invalid lead schema               | Retries, then raises an internal extraction error |
| Groq timeout                                   | Retries                                           |
| Groq rate limit (`429`)                        | Retries                                           |
| Groq server error (`500`, `502`, `503`, `504`) | Retries                                           |
| Invalid API key (`401`)                        | Fails immediately                                 |
| LLM extraction fails after retries             | API returns `502`                                 |

## Design Decisions

- The LLM extracts data, but Pydantic decides whether the data is valid.
- Missing information is returned as `null`, never invented.
- Invalid Nigerian phone numbers are rejected and returned as `null`.
- Temporary provider failures are retried; client errors such as invalid API keys fail immediately.
- Token usage and latency are logged for observability.
- Tests mock Groq so the test suite is fast, repeatable, and free.

## Future Improvements

- Add request-rate limiting
- Add persistent lead storage with PostgreSQL
- Add authentication and API keys for callers
- Add streaming responses
- Add a simple frontend
- Add evaluation datasets for extraction accuracy
- Add support for multiple LLM providers and fallback models
- Deploy to Railway, Render, or a cloud platform

## License

MIT
