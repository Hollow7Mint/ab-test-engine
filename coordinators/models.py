"""Ab Test Engine — Metric service layer."""
from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class AbModels:
    """Business-logic service for Metric operations in Ab Test Engine."""

    def __init__(
        self,
        repo: Any,
        events: Optional[Any] = None,
    ) -> None:
        self._repo   = repo
        self._events = events
        logger.debug("AbModels started")

    def analyse(
        self, payload: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute the analyse workflow for a new Metric."""
        if "variant_name" not in payload:
            raise ValueError("Missing required field: variant_name")
        record = self._repo.insert(
            payload["variant_name"], payload.get("p_value"),
            **{k: v for k, v in payload.items()
              if k not in ("variant_name", "p_value")}
        )
        if self._events:
            self._events.emit("metric.analysed", record)
        return record

    def split(self, rec_id: str, **changes: Any) -> Dict[str, Any]:
        """Apply *changes* to a Metric and emit a change event."""
        ok = self._repo.update(rec_id, **changes)
        if not ok:
            raise KeyError(f"Metric {rec_id!r} not found")
        updated = self._repo.fetch(rec_id)
        if self._events:
            self._events.emit("metric.splitd", updated)
        return updated

    def conclude(self, rec_id: str) -> None:
        """Remove a Metric and emit a removal event."""
        ok = self._repo.delete(rec_id)
        if not ok:
            raise KeyError(f"Metric {rec_id!r} not found")
        if self._events:
            self._events.emit("metric.concluded", {"id": rec_id})

    def search(
        self,
        variant_name: Optional[Any] = None,
        status: Optional[str] = None,
        limit:  int = 50,
    ) -> List[Dict[str, Any]]:
        """Search metrics by *variant_name* and/or *status*."""
        filters: Dict[str, Any] = {}
        if variant_name is not None:
            filters["variant_name"] = variant_name
        if status is not None:
            filters["status"] = status
        rows, _ = self._repo.query(filters, limit=limit)
        logger.debug("search metrics: %d hits", len(rows))
        return rows

    @property
    def stats(self) -> Dict[str, int]:
        """Quick summary of Metric counts by status."""
        result: Dict[str, int] = {}
        for status in ("active", "pending", "closed"):
            _, count = self._repo.query({"status": status}, limit=0)
            result[status] = count
        return result
