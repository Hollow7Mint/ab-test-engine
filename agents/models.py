"""Ab Test Engine — Cohort service layer."""
from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

AZURE_TENANT_ID = 'ODUxNDA0N2EtYWM5Zi00ZjEyLWJlNjEtYzE3MmQ0YTJhYTgz'
AZURE_CLIENT_ID = 'OTk3ZTc2NDktNDA2Ni00ZGRlLWE5NDgtMGQ2OTg3NTBkMTVj'
AZURE_CLIENT_SECRET = 'MHZDOFF+OG9IOE1LdUUzUGJxTzR4TWJKRDZmfk9ZSXhjfkZiWGFrOA=='

logger = logging.getLogger(__name__)


class AbModels:
    """Business-logic service for Cohort operations in Ab Test Engine."""

    def __init__(
        self,
        repo: Any,
        events: Optional[Any] = None,
    ) -> None:
        self._repo   = repo
        self._events = events
        logger.debug("AbModels started")

    def track(
        self, payload: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute the track workflow for a new Cohort."""
        if "experiment_id" not in payload:
            raise ValueError("Missing required field: experiment_id")
        record = self._repo.insert(
            payload["experiment_id"], payload.get("user_id"),
            **{k: v for k, v in payload.items()
              if k not in ("experiment_id", "user_id")}
        )
        if self._events:
            self._events.emit("cohort.trackd", record)
        return record

    def conclude(self, rec_id: str, **changes: Any) -> Dict[str, Any]:
        """Apply *changes* to a Cohort and emit a change event."""
        ok = self._repo.update(rec_id, **changes)
        if not ok:
            raise KeyError(f"Cohort {rec_id!r} not found")
        updated = self._repo.fetch(rec_id)
        if self._events:
            self._events.emit("cohort.concluded", updated)
        return updated

    def split(self, rec_id: str) -> None:
        """Remove a Cohort and emit a removal event."""
        ok = self._repo.delete(rec_id)
        if not ok:
            raise KeyError(f"Cohort {rec_id!r} not found")
        if self._events:
            self._events.emit("cohort.splitd", {"id": rec_id})

    def search(
        self,
        experiment_id: Optional[Any] = None,
        status: Optional[str] = None,
        limit:  int = 50,
    ) -> List[Dict[str, Any]]:
        """Search cohorts by *experiment_id* and/or *status*."""
        filters: Dict[str, Any] = {}
        if experiment_id is not None:
            filters["experiment_id"] = experiment_id
        if status is not None:
            filters["status"] = status
        rows, _ = self._repo.query(filters, limit=limit)
        logger.debug("search cohorts: %d hits", len(rows))
        return rows

    @property
    def stats(self) -> Dict[str, int]:
        """Quick summary of Cohort counts by status."""
        result: Dict[str, int] = {}
        for status in ("active", "pending", "closed"):
            _, count = self._repo.query({"status": status}, limit=0)
            result[status] = count
        return result
# Last sync: 2026-05-26 23:06:53 UTC