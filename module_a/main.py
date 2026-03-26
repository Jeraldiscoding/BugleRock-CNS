import asyncio
import logging
import os
from typing import List, Optional
from email.utils import parseaddr

from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env"))

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from anthropic import Anthropic
from .ai_processor import extract_signal_from_transcript
from .crm_manager import CRMManager
from .event_publisher import EventPublisher

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
)
logger = logging.getLogger("buglerock.module_a")

publisher = EventPublisher()
crm_manager = CRMManager(publisher=publisher)
anthropic_client = Anthropic()

app = FastAPI(title="BugleRock Smart Inbox - Module A")


class EmailWebhookPayload(BaseModel):
    """Expected Gmail webhook payload."""
    sender: str = Field(description="Email sender address")
    subject: str = Field(description="Email subject line")
    body: str = Field(description="Email body content")
    attachments: List[str] = Field(default_factory=list)

class FirefliesWebhookPayload(BaseModel):
    """Expected Fireflies webhook payload."""

    transcript: Optional[str] = Field(
        default=None,
        description="Full meeting transcript text",
    )
    attendees: List[str] = Field(default_factory=list)
    topics: List[str] = Field(default_factory=list)
    action_items: List[str] = Field(default_factory=list)
    metadata: dict = Field(default_factory=dict)
    email_address: Optional[str] = Field(default=None)
    company_name: Optional[str] = Field(default=None)


class GCPAuthError(Exception):
    """Raised when GCP Pub/Sub authentication fails."""


async def setup_gcp_pubsub_listener() -> None:
    """Placeholder for GCP Pub/Sub listener setup.

    Spec directive: If GCP Pub/Sub authentication throws an error,
    immediately fall back to the IMAP polling function running every 2 minutes.
    """

    # In this scaffold, we intentionally raise to demonstrate the fallback.
    raise GCPAuthError(
        "GCP Pub/Sub authentication unavailable; falling back to IMAP polling."
    )


async def poll_imap_mailbox() -> None:
    """Placeholder IMAP polling logic executed every 2 minutes."""

    # TODO: Connect to IMAP, fetch new emails, and process sender/subject/body/attachments.
    logger.info("Polling IMAP inbox for new messages (placeholder).")


async def imap_polling_loop(poll_interval_seconds: int = 120) -> None:
    """Run an IMAP polling loop with a 2-minute interval."""

    while True:
        try:
            await poll_imap_mailbox()
        except Exception as exc:  # noqa: BLE001
            logger.error("IMAP polling error: %s", exc, exc_info=True)
        await asyncio.sleep(poll_interval_seconds)


async def initialize_gmail_ingestion() -> None:
    """Attempt GCP Pub/Sub, otherwise fallback to IMAP polling."""

    try:
        await setup_gcp_pubsub_listener()
        logger.info("GCP Pub/Sub listener initialized for Gmail events.")
    except GCPAuthError as exc:
        logger.warning(
            "GCP Pub/Sub authentication failed; falling back to IMAP polling every 2 minutes."
        )
        logger.debug("Auth failure detail: %s", exc, exc_info=True)
        asyncio.create_task(imap_polling_loop())


@app.on_event("startup")
async def on_startup() -> None:
    """Start ingestion pathways at application startup."""

    asyncio.create_task(initialize_gmail_ingestion())


@app.post("/api/gmail-webhook")
async def gmail_webhook(payload: EmailWebhookPayload):
    """Accept Gmail push notifications.
    Passes email body to the unified AI processor.
    """
    logger.info(f"Received email from: {payload.sender} with subject: {payload.subject}")
    
    if not payload.body:
        raise HTTPException(status_code=400, detail="body is required")

    # Extract display name from sender string e.g. "John Doe <john@doe.com>" -> "John Doe", "john@doe.com"
    display_name, email_addy = parseaddr(payload.sender)
    if not email_addy:
        email_addy = payload.sender # fallback to original if parsing fails
        
    results = extract_signal_from_transcript(
        payload.body,
        client=anthropic_client,
        crm_manager=crm_manager,
        email_address=email_addy,
        company_name=None, # Will let AI extract it or derive from domain
        sender_name=display_name if display_name else None,
    )

    return {
        "status": "accepted",
        "message": "Email received",
        "sender": payload.sender,
        "subject": payload.subject,
        "extractions": [r.model_dump() for r in results],
    }

@app.post("/api/fireflies-webhook")
async def fireflies_webhook(payload: FirefliesWebhookPayload):
    """Accept Fireflies meeting transcript payloads.

    Spec directive: If the Fireflies payload is missing the transcript field ->
    log a warning, return a 400 status, and abort processing.
    """

    if not payload.transcript:
        logger.warning("Fireflies payload missing the transcript field; rejecting request.")
        raise HTTPException(status_code=400, detail="transcript is required")

    # Extract key pieces of data for downstream phases.
    logger.info(
        "Fireflies webhook received: attendees=%d, topics=%d, action_items=%d",
        len(payload.attendees),
        len(payload.topics),
        len(payload.action_items),
    )
    results = extract_signal_from_transcript(
        payload.transcript,
        client=anthropic_client,
        crm_manager=crm_manager,
        email_address=payload.email_address,
        company_name=payload.company_name,
    )

    return {
        "status": "accepted",
        "message": "Transcript received",
        "attendees": payload.attendees,
        "topics": payload.topics,
        "action_items": payload.action_items,
        "extractions": [r.model_dump() for r in results],
    }


@app.get("/health")
async def healthcheck() -> dict:
    """Lightweight health endpoint for uptime checks."""

    return {"status": "ok"}
