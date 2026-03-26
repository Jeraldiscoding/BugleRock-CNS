import uuid
import logging
import chromadb

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

# ==========================================
# ChromaDB Local Setup
# ==========================================
# Initialize a PersistentClient pointing to a local directory.
# (This ensures the data survives server restarts.)
CHROMA_DATA_DIR = "./chroma_db"
client = chromadb.PersistentClient(
    path=CHROMA_DATA_DIR,
    settings=chromadb.Settings(anonymized_telemetry=False)
)

# Create or get the collection
# By not specifying an embedding_function, we rely on ChromaDB's default
# built-in embedding function (Sentence Transformers)
collection = client.get_or_create_collection(name="meeting_transcripts")


# ==========================================
# Chunking & Storage Logic
# ==========================================
def chunk_transcript(text: str, chunk_size: int = 800) -> list[str]:
    """
    Splits a massive transcript string into smaller chunks of roughly 
    500 to 1000 characters each, splitting by words to avoid word truncation.
    """
    words = text.split()
    chunks = []
    current_chunk = []
    current_length = 0
    
    for word in words:
        # +1 for the space character
        if current_length + len(word) > chunk_size and current_chunk:
            chunks.append(" ".join(current_chunk))
            current_chunk = [word]
            current_length = len(word) + 1
        else:
            current_chunk.append(word)
            current_length += len(word) + 1
            
    if current_chunk:
        chunks.append(" ".join(current_chunk))
        
    return chunks

def store_transcript(transcript_text: str, metadata_dict: dict):
    """
    Splits the massive transcript string into smaller chunks and inserts them
    into the ChromaDB collection, attaching the metadata_dict to every chunk.
    metadata_dict should include fields like 'client_name', 'date', 'zoho_id'.
    """
    if not transcript_text or not transcript_text.strip():
        logger.warning("Empty transcript provided. Nothing to store.")
        return

    chunks = chunk_transcript(transcript_text)
    
    documents = []
    metadatas = []
    ids = []
    
    # Generate a base ID using the required metadata elements or a fallback
    base_id = (
        metadata_dict.get("zoho_id", "unknown_user") + "_" + 
        metadata_dict.get("date", "unknown_date") + "_" + 
        str(uuid.uuid4())[:8]
    )
    
    for i, chunk in enumerate(chunks):
        documents.append(chunk)
        
        # Attach the exact same metadata to every single chunk
        chunk_metadata = metadata_dict.copy()
        chunk_metadata["chunk_index"] = i
        metadatas.append(chunk_metadata)
        
        # Unique ID for each chunk
        ids.append(f"{base_id}_chunk_{i}")
        
    if documents:
        collection.add(
            documents=documents,
            metadatas=metadatas,
            ids=ids
        )
        logger.info(f"Stored {len(chunks)} chunks in ChromaDB for client: {metadata_dict.get('client_name')}")


# ==========================================
# Retrieval Logic
# ==========================================
def query_knowledge_base(user_query: str, n_results: int = 3) -> list[str]:
    """
    Takes a natural language string, queries the ChromaDB collection,
    and returns the top `n_results` most relevant text chunks.
    """
    logger.info(f"Querying knowledge base for: '{user_query}'")
    
    results = collection.query(
        query_texts=[user_query],
        n_results=n_results
    )
    
    # Chroma returns results["documents"] as a list of lists (one list of chunks per query)
    if results and "documents" in results and results["documents"]:
        top_chunks = results["documents"][0]
        return top_chunks
        
    return []

# Quick test if run directly
if __name__ == "__main__":
    # Test data
    sample_text = "Meeting with Acme about renewal. We discussed the Q3 performance. " * 20
    sample_metadata = {
        "client_name": "Acme Corp",
        "date": "2026-03-26",
        "zoho_id": "Z-100"
    }

    print("--- Storing Transcript ---")
    store_transcript(sample_text, sample_metadata)
    
    print("\n--- Querying KB ---")
    retrieved_chunks = query_knowledge_base("Q3 performance", n_results=2)
    for idx, chunk in enumerate(retrieved_chunks):
        print(f"\nResult {idx+1}: {chunk[:100]}...")
