"""AI Processing for Module A: Structured extraction via Anthropic Claude.

Phase 2 scope: chunk Fireflies transcripts, call Claude with structured outputs
(Pydantic), handle rate limits with exponential backoff (2s, 4s, 8s).
"""

import json
import time
from enum import Enum
from typing import List, Optional, TYPE_CHECKING

from anthropic import Anthropic, APIStatusError
from pydantic import BaseModel, Field

if TYPE_CHECKING:
    from crm_manager import CRMManager

# -----------------------------
# Pydantic schemas (structured outputs)
# -----------------------------


class SignalType(str, Enum):
    client_email = "client email"
    prospect_inquiry = "prospect inquiry"
    internal = "internal"
    marketing = "marketing"
    vendor = "vendor"


class Urgency(str, Enum):
    high = "high"
    medium = "medium"
    low = "low"


class Sentiment(str, Enum):
    positive = "Positive"
    neutral = "Neutral"
    frustrated = "Frustrated"


class Entities(BaseModel):
    company_name: Optional[str] = Field(default=None)
    person: Optional[str] = Field(default=None)
    deal_reference: Optional[str] = Field(default=None)
    action_items: List[str] = Field(default_factory=list)


class SignalExtraction(BaseModel):
    type: SignalType
    urgency: Urgency
    entities: Entities
    sentiment: Sentiment


# -----------------------------
# Chunking
# -----------------------------


def chunk_transcript(transcript: str, max_tokens: int = 4000) -> List[str]:
    """Split transcript into sequential chunks ~max_tokens words/tokens each.

    Assumes ~1 word ≈ 1 token; good enough for pre-chunking before Claude.
    """

    if not transcript:
        return []

    words = transcript.split()
    if len(words) <= max_tokens:
        return [transcript]

    chunks: List[str] = []
    for start in range(0, len(words), max_tokens):
        chunk_words = words[start : start + max_tokens]
        chunks.append(" ".join(chunk_words))
    return chunks


# -----------------------------
# Claude client helper
# -----------------------------


def _call_claude_structured(
    client: Anthropic,
    *,
    model: str,
    content: str,
    max_tokens: int = 1024,
) -> SignalExtraction:
    """Call Claude with tool-based structured outputs + exponential backoff for 429.

    Uses Anthropic tools API to enforce a JSON schema derived from Pydantic.
    """

    backoff_schedule = [2, 4, 8]
    attempt = 0
    schema = SignalExtraction.model_json_schema()

    tool = {
        "name": "extract_signal",
        "description": "Extracts structured signal fields",
        "input_schema": schema,
    }

    while True:
        try:
            response = client.messages.create(
                model=model,
                max_tokens=max_tokens,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": (
                                    "You are an extraction engine. Given a meeting transcript "
                                    "or email text, classify and extract strictly into the schema "
                                    "provided via the tool input_schema. Call the tool once."
                                ),
                            },
                            {"type": "text", "text": content},
                        ],
                    }
                ],
                tools=[tool],
                tool_choice={"type": "tool", "name": "extract_signal"},
            )

            # Find the first tool_use content block
            tool_calls = [c for c in response.content if getattr(c, "type", None) == "tool_use" or c.get("type") == "tool_use"]
            if not tool_calls:
                raise ValueError("Claude response missing tool_use block")

            tool_call = tool_calls[0]
            raw_input = getattr(tool_call, "input", None) or tool_call.get("input")
            data = raw_input if isinstance(raw_input, dict) else json.loads(raw_input)
            return SignalExtraction.model_validate(data)
        except APIStatusError as exc:  # type: ignore[match]
            attempt += 1
            if exc.status_code == 429 and attempt <= len(backoff_schedule):
                wait_for = backoff_schedule[attempt - 1]
                time.sleep(wait_for)
                continue
            raise


def extract_signal_from_transcript(
    transcript: str,
    *,
    client: Optional[Anthropic] = None,
    model: str = "claude-haiku-4-5-20251001", 
    max_completion_tokens: int = 1024,
    crm_manager: Optional["CRMManager"] = None,
    email_address: Optional[str] = None,
    company_name: Optional[str] = None,
) -> List[SignalExtraction]:
    """Process a transcript (chunked if needed) and return per-chunk extractions."""

    _client = client or Anthropic()
    chunks = chunk_transcript(transcript, max_tokens=4000)
    results: List[SignalExtraction] = []
    crm_summaries: List[dict] = []

    for chunk in chunks:
        extraction = _call_claude_structured(
            _client,
            model=model,
            content=chunk,
            max_tokens=max_completion_tokens,
        )
        results.append(extraction)

        if crm_manager:
            # Prefer provided email/company; fall back to extracted company if present.
            company = company_name or extraction.entities.company_name or ""
            if email_address and company:
                summary = crm_manager.upsert_signal(
                    extraction,
                    email_address=email_address,
                    company_name=company,
                )
                crm_summaries.append(summary)

    return results
