import json
import logging
from typing import List, Optional

from anthropic import Anthropic
from pydantic import BaseModel, Field

# We use a try-except to handle scenarios where chromadb is not yet installed
try:
    import chromadb
except ImportError:
    chromadb = None

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

# ==========================================
# PHASE 1: Deep Analysis & Follow-Up Gen
# ==========================================

class MeetingInsights(BaseModel):
    """Pydantic schema for Claude to extract meeting insights and draft an email."""
    decisions_made: List[str] = Field(description="Key decisions made during the meeting")
    commitments_given: List[str] = Field(description="Action items or commitments promised to the client")
    risk_flags: List[str] = Field(description="Any risks identified, e.g., churn risk, compliance issues")
    sentiment_shift: str = Field(description="Description of how the client's sentiment evolved during the call")
    follow_up_email_draft: str = Field(description="A fully written, professional follow-up email draft based on the meeting")

def analyze_meeting_transcript(
    transcript: str, 
    client: Optional[Anthropic] = None, 
    model: str = "claude-haiku-4-5-20251001"
) -> MeetingInsights:
    """Analyze the transcript using Claude structured outputs."""
    _client = client or Anthropic()
    
    schema = MeetingInsights.model_json_schema()
    tool = {
        "name": "extract_meeting_insights",
        "description": "Extracts meeting insights and drafts a follow-up email",
        "input_schema": schema,
    }
    
    logger.info("Calling Claude to extract meeting insights...")
    response = _client.messages.create(
        model=model,
        max_tokens=1500,
        messages=[
            {
                "role": "user",
                "content": (
                    "You are an expert financial advisor AI assistant. Analyze the following meeting "
                    "transcript, extract the key insights, and draft a professional follow-up email "
                    "to the client. Make sure to call the tool to output the structured JSON.\n\n"
                    f"<transcript>\n{transcript}\n</transcript>"
                )
            }
        ],
        tools=[tool],
        tool_choice={"type": "tool", "name": "extract_meeting_insights"}
    )
    
    tool_calls = [c for c in response.content if getattr(c, "type", None) == "tool_use" or (isinstance(c, dict) and c.get("type") == "tool_use")]
    if not tool_calls:
        raise ValueError("Claude did not return a tool_use block.")
        
    tool_call = tool_calls[0]
    raw_input = getattr(tool_call, "input", None) or tool_call.get("input")
    data = raw_input if isinstance(raw_input, dict) else json.loads(raw_input)
    
    return MeetingInsights.model_validate(data)

# ==========================================
# PHASE 2: Vector Knowledge Base (RAG)
# ==========================================

def chunk_text(text: str, words_per_chunk: int = 100) -> List[str]:
    """Semantic/word-based chunking for the transcript."""
    words = text.split()
    chunks = []
    for i in range(0, len(words), words_per_chunk):
        chunks.append(" ".join(words[i:i + words_per_chunk]))
    return chunks

class KnowledgeBase:
    def __init__(self, db_path: str = "./chroma_db"):
        self.db_path = db_path
        if chromadb is None:
            logger.warning("chromadb is not installed. Fallback to sqlite strictly not implemented yet. Please pip install chromadb.")
            self.client = None
            self.collection = None
        else:
            self.client = chromadb.PersistentClient(
                path=self.db_path,
                settings=chromadb.Settings(anonymized_telemetry=False)
            )
            self.collection = self.client.get_or_create_collection(name="meeting_transcripts")
            logger.info("ChromaDB initialized at %s with collection 'meeting_transcripts'", self.db_path)

    def embed_transcript(self, transcript: str, metadata: dict):
        """Chunk and embed a transcript into ChromaDB."""
        if not self.collection:
            logger.error("ChromaDB not initialized, skipping embedding.")
            return
            
        chunks = chunk_text(transcript, words_per_chunk=50) # Smaller chunks for better semantic search
        
        # Prepare data for insertion
        documents = []
        metadatas = []
        ids = []
        
        base_id = metadata.get("zoho_contact_id", "unknown_contact") + "_" + metadata.get("meeting_date", "unknown_date")
        
        for i, chunk in enumerate(chunks):
            documents.append(chunk)
            # Add chunk index to metadata
            chunk_meta = metadata.copy()
            chunk_meta["chunk_index"] = i
            metadatas.append(chunk_meta)
            ids.append(f"{base_id}_chunk_{i}")
            
        if documents:
            self.collection.add(
                documents=documents,
                metadatas=metadatas,
                ids=ids
            )
            logger.info("Successfully embedded %d chunks for meeting.", len(documents))

# ==========================================
# TEST BLOCK
# ==========================================
if __name__ == "__main__":
    # Mock Fireflies data from earlier tests
    mock_payload = {
        "transcript": "Meeting with Acme about renewal. We discussed the Q3 performance. Client was happy but frustrated with recent billing delays. Action items: send proposal, schedule pricing call, and review the billing audit. We promised a 10% discount for next quarter to make up for the delays. Bob from Acme said they will renew if we fix it.",
        "attendees": ["alice@example.com", "bob@example.com"],
        "topics": ["renewal", "pricing", "billing issues"],
        "action_items": ["send proposal", "schedule pricing call", "billing audit"],
        "email_address": "bob@example.com",
        "company_name": "Acme Corp"
    }
    
    transcript_text = mock_payload["transcript"]
    
    print("\n--- PHASE 1: Extracting Insights ---")
    try:
        insights = analyze_meeting_transcript(transcript_text)
        print(json.dumps(insights.model_dump(), indent=2))
    except Exception as e:
        logger.error(f"Failed extraction: {e}")
        
    print("\n--- PHASE 2: Embedding in Knowledge Base ---")
    kb = KnowledgeBase()
    meta = {
        "client_name": mock_payload["company_name"],
        "zoho_contact_id": "Z-1",  # Mock ID from Module A tests
        "meeting_date": "2026-03-26"
    }
    
    kb.embed_transcript(transcript_text, metadata=meta)
    
    if kb.collection:
        print(f"\nTotal documents in Knowledge Base: {kb.collection.count()}")
