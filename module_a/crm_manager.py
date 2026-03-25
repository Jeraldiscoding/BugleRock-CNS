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


class ZohoClient:
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


def map_contact(signal: "SignalExtraction", email_address: str, company_name: str) -> Dict:
    return {
        "email": email_address,
        "company": company_name,
        "type": signal.type.value,
        "urgency": signal.urgency.value,
        "sentiment": signal.sentiment.value,
        "person": signal.entities.person,
    }


def map_deal(signal: "SignalExtraction", company_name: str) -> Dict:
    return {
        "deal_reference": signal.entities.deal_reference,
        "company": company_name,
        "type": signal.type.value,
        "urgency": signal.urgency.value,
    }


def map_note(signal: "SignalExtraction", target_id: str) -> Dict:
    return {
        "parent_id": target_id,
        "content": {
            "company": signal.entities.company_name,
            "person": signal.entities.person,
            "deal_reference": signal.entities.deal_reference,
            "action_items": signal.entities.action_items,
            "sentiment": signal.sentiment.value,
        },
    }


def map_tasks(signal: "SignalExtraction", target_id: str) -> List[Dict]:
    tasks = []
    for item in signal.entities.action_items:
        tasks.append(
            {
                "parent_id": target_id,
                "title": item,
                "type": "task",
                "priority": signal.urgency.value,
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
        self.rate_limiter = RateLimiter(max_calls=100, per_seconds=60)
        self.zoho = ZohoClient(rate_limiter=self.rate_limiter)
        self.publisher = publisher

    def upsert_signal(
        self,
    signal: "SignalExtraction",
        *,
        email_address: str,
        company_name: str,
    ) -> Dict:
        """Dedup then create or update Zoho records. Returns summary."""

        cached_id = self.cache.get(email_address, company_name)
        summary: Dict = {"action": None, "zoho_contact_id": None, "tasks": []}

        contact_payload = map_contact(signal, email_address, company_name)
        deal_payload = map_deal(signal, company_name)

        if cached_id:
            # Update path
            contact_res = self.zoho.update_contact(cached_id, contact_payload)
            summary.update({"action": "update", "zoho_contact_id": contact_res.id})
            note_res = self.zoho.create_note(map_note(signal, contact_res.id))
            summary["note_id"] = note_res.id
        else:
            # Create path
            contact_res = self.zoho.create_contact(contact_payload)
            summary.update({"action": "create", "zoho_contact_id": contact_res.id})
            self.cache.upsert(email_address, company_name, contact_res.id)
            deal_res = self.zoho.create_deal(deal_payload)
            summary["deal_id"] = deal_res.id
            note_res = self.zoho.create_note(map_note(signal, contact_res.id))
            summary["note_id"] = note_res.id

        # Tasks from action items (always map)
        tasks_payload = map_tasks(signal, summary["zoho_contact_id"])
        for payload in tasks_payload:
            task_res = self.zoho.create_task(payload)
            summary["tasks"].append(task_res.id)

        summary["contact_payload"] = contact_payload
        summary["deal_payload"] = deal_payload

        # Publish to universal router (Phase 4) as the last step
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
