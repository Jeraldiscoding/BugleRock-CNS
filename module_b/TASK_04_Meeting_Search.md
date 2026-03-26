# TASK 04: Implement Meeting Knowledge Base Search (Feature 4)

## 1. Context & Objectives
Module C requires a searchable meeting knowledge base allowing natural language queries like "What did we discuss with Client X last quarter?".

## 2. Strict Workflow Rules
1. **Mock RAG Implementation:** Instead of a full Vector DB, use a hardcoded transcript dictionary to simulate the retrieval process for the demo.
2. **AI Integration:** Pass the mock transcript and the user's query to the Claude API to extract decisions and commitments.

## 3. Detailed Implementation Steps

### A. Mock Transcript Data
Add this to `api_bridge.py`:
```python
mock_transcripts = {
    "Bruce Wayne": "Meeting Date: March 20th. Discussed shifting 15% of portfolio from tech equities to private credit to mitigate Q3 volatility. Client committed to signing documents by Friday. Risk flag: Client seemed anxious about inflation.",
    "Apex Corp": "Meeting Date: March 22nd. CFO requested an automated KYC pipeline. We agreed to send the UBO declaration forms by Wednesday."
}