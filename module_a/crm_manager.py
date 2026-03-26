"""Phase 3: Deduplication cache & Zoho CRM integration scaffolding.

Implements:
- SQLite dedup cache (composite PK: email_address + company_name)
- Mapping from SignalExtraction to Zoho payloads (Contacts, Deals, Notes, Tasks)
- Rate-limit guard (100 calls/min) with in-memory queue

Notes:
- Zoho API calls are stubbed; replace with real HTTP calls and auth.
- Action items map to Zoho Tasks explicitly.
"""

import sqlite3
import time
from collections import deque
from dataclasses import dataclass
from typing import Deque, Dict, List, Optional, TYPE_CHECKING
import logging
import json
from module_b.zoho_client_live import ZohoClientLive

if TYPE_CHECKING:
    from ai_processor import SignalExtraction
    from event_publisher import EventPublisher


# -----------------------------
# Dedup cache (SQLite)
# -----------------------------


class DedupCache:
    def __init__(self, db_path: str = "dedup_cache.sqlite") -> None:
        self.db_path = db_path
        self._ensure_table()

    def _ensure_table(self) -> None:
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS dedup_cache (
                    email_address TEXT NOT NULL,
                    company_name TEXT NOT NULL,
                    zoho_id TEXT NOT NULL,
                    PRIMARY KEY (email_address, company_name)
                );
                """
            )
            conn.commit()

    def get(self, email_address: str, company_name: str) -> Optional[str]:
        with sqlite3.connect(self.db_path) as conn:
            cur = conn.execute(
                "SELECT zoho_id FROM dedup_cache WHERE email_address = ? AND company_name = ?",
                (email_address, company_name),
            )
            row = cur.fetchone()
            return row[0] if row else None

    def upsert(self, email_address: str, company_name: str, zoho_id: str) -> None:
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                INSERT INTO dedup_cache (email_address, company_name, zoho_id)
                VALUES (?, ?, ?)
                ON CONFLICT(email_address, company_name)
                DO UPDATE SET zoho_id=excluded.zoho_id;
                """,
                (email_address, company_name, zoho_id),
            )
            conn.commit()


# -----------------------------
# Rate limiter (100 calls/min)
# -----------------------------


class RateLimiter:
    def __init__(self, max_calls: int = 100, per_seconds: int = 60) -> None:
        self.max_calls = max_calls
        self.per_seconds = per_seconds
        self.calls: Deque[float] = deque()

    def acquire(self) -> None:
        now = time.time()
        # drop old calls
        while self.calls and now - self.calls[0] > self.per_seconds:
            self.calls.popleft()
        if len(self.calls) >= self.max_calls:
            sleep_for = self.per_seconds - (now - self.calls[0])
            time.sleep(max(0, sleep_for))
            return self.acquire()
        self.calls.append(time.time())


# -----------------------------
# Zoho client stub (replace with real API calls)
# -----------------------------


@dataclass
class ZohoResult:
    id: str
    status: str
    payload: Dict


class MockZohoClient:
    def __init__(self, rate_limiter: RateLimiter) -> None:
        self.rate_limiter = rate_limiter
        self._counter = 0  # for stub IDs

    def _next_id(self) -> str:
        self._counter += 1
        return f"Z-{self._counter}"

    def _call(self, payload: Dict) -> ZohoResult:
        self.rate_limiter.acquire()
        # TODO: Replace with real HTTP request to Zoho CRM
        return ZohoResult(id=self._next_id(), status="ok", payload=payload)

    def create_contact(self, payload: Dict) -> ZohoResult:
        return self._call({"object": "contact", **payload})

    def update_contact(self, zoho_id: str, payload: Dict) -> ZohoResult:
        return self._call({"object": "contact", "id": zoho_id, **payload})

    def create_deal(self, payload: Dict) -> ZohoResult:
        return self._call({"object": "deal", **payload})

    def create_note(self, payload: Dict) -> ZohoResult:
        return self._call({"object": "note", **payload})

    def create_task(self, payload: Dict) -> ZohoResult:
        return self._call({"object": "task", **payload})


# -----------------------------
# Mapper utilities
# -----------------------------

def map_contact(signal: "SignalExtraction", email_address: str, company_name: str, fallback_name: Optional[str] = None) -> Dict:
    # Use fallback_name (from email header) if AI couldn't extract a person's name
    best_name = signal.entities.person or fallback_name or "Unknown Contact"
    
    # Split person into First and Last name roughly
    name_parts = best_name.split(" ", 1)
    
    # Zoho requires Last_Name. If only one word is given, it must be the Last_Name.
    if len(name_parts) > 1:
        first_name = name_parts[0]
        last_name = name_parts[1]
    else:
        first_name = ""
        last_name = name_parts[0] if name_parts[0] else "Unknown"

    contact_payload = {
        "Email": email_address,
        "First_Name": first_name,
        "Last_Name": last_name,
        "Description": f"Company/Account: {company_name}\nRole/Details: Pulled from email\nType: {signal.type.value}\nUrgency: {signal.urgency.value}\nSentiment: {signal.sentiment.value}",
        "person": best_name,  # Kept for internal caching
    }
    
    if company_name and len(company_name.strip()) > 0:
        contact_payload["Account_Name"] = company_name.strip()
    
    if signal.entities.phone_number:
        contact_payload["Phone"] = signal.entities.phone_number
        contact_payload["Mobile"] = signal.entities.phone_number # Map to mobile as well just in case
    if signal.entities.job_title:
        contact_payload["Title"] = signal.entities.job_title
        
    return contact_payload

def map_deal(signal: "SignalExtraction", company_name: str, contact_id: Optional[str] = None) -> Dict:
    deal_title = signal.entities.deal_reference or "New Proposal"
    deal = {
        "Deal_Name": f"[{signal.urgency.value.upper()}] {deal_title} ({company_name})",
        "Stage": "Needs Analysis",
        "Closing_Date": "2026-12-31",
        "Description": f"Type: {signal.type.value}\nUrgency: {signal.urgency.value}\nGenerated by BugleRock AI",
    }
    
    if company_name:
        deal["Account_Name"] = company_name.strip()
        
    if contact_id:
        deal["Contact_Name"] = contact_id
        
    return deal

def map_note(signal: "SignalExtraction", target_id: str) -> Dict:
    # Not using notes for now since Zoho Client doesn't have it natively,
    # or we can pass it using a mapped structure if added later.
    return {
        "Parent_Id": target_id,
        "Note_Title": "Signal Extraction Summary",
        "Note_Content": f"Company: {signal.entities.company_name}\nPerson: {signal.entities.person}\nDeal Reference: {signal.entities.deal_reference}\nAction Items: {', '.join(signal.entities.action_items)}\nSentiment: {signal.sentiment.value}"
    }

def map_tasks(signal: "SignalExtraction", target_id: str) -> List[Dict]:
    tasks = []
    for item in signal.entities.action_items:
        tasks.append(
            {
                "Subject": f"{item[:50]}...",
                "Description": item,
                "Status": "Not Started",
                "Who_Id": target_id, # Associates to contact
            }
        )
    return tasks

# -----------------------------
# CRM Manager
# -----------------------------


class CRMManager:
    def __init__(
        self,
        db_path: str = "dedup_cache.sqlite",
        publisher: Optional["EventPublisher"] = None,
    ) -> None:
        self.cache = DedupCache(db_path=db_path)
        self.zoho = ZohoClientLive()
        self.publisher = publisher

    def upsert_signal(
        self,
        signal: "SignalExtraction",
        *,
        email_address: str,
        company_name: str,
        sender_name: Optional[str] = None,
    ) -> Dict:
        """Dedup then create or update Zoho records. Returns summary."""

        cached_id = self.cache.get(email_address, company_name)
        summary: Dict = {"action": None, "zoho_contact_id": None, "tasks": []}

        contact_payload = map_contact(signal, email_address, company_name, fallback_name=sender_name)

        if cached_id:
            # Update path
            # In live client, upsert_contact handles it or we re-push it
            contact_id = self.zoho.upsert_contact(contact_payload) or cached_id
            summary.update({"action": "update", "zoho_contact_id": contact_id})
        else:
            # Create path
            contact_id = self.zoho.upsert_contact(contact_payload)
            if contact_id:
                summary.update({"action": "create", "zoho_contact_id": contact_id})
                self.cache.upsert(email_address, company_name, contact_id)
                
                # Create deal
                deal_payload = map_deal(signal, company_name, contact_id=contact_id)
                deal_id = self.zoho.create_deal(deal_payload)
                summary["deal_id"] = deal_id
            else:
                 summary.update({"action": "failed", "zoho_contact_id": None})

        # Tasks from action items
        if summary.get("zoho_contact_id"):
            tasks_payload = map_tasks(signal, summary["zoho_contact_id"])
            for payload in tasks_payload:
                task_id = self.zoho.create_task(payload)
                if task_id:
                    summary["tasks"].append(task_id)

        summary["contact_payload"] = contact_payload

        # Publish to universal router
        if self.publisher:
            event_payload = {
                "signal": signal.model_dump(),
                "crm_summary": summary,
            }
            self.publisher.publish_new_signal_classified(event_payload)

        return summary


__all__ = [
    "CRMManager",
    "DedupCache",
    "RateLimiter",
    "ZohoClient",
    "map_contact",
    "map_deal",
    "map_note",
    "map_tasks",
]
