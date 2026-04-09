"""Ab Test Engine — Assignment service layer."""
from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class AbProcessor:
    """Business-logic service for Assignment operations in Ab Test Engine."""

    def __init__(
        self,
        repo: Any,
        events: Optional[Any] = None,
    ) -> None:
        self._repo   = repo
        self._events = events
        logger.debug("AbProcessor started")

    def assign(
        self, payload: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute the assign workflow for a new Assignment."""
        if "conversion" not in payload:
            raise ValueError("Missing required field: conversion")
        record = self._repo.insert(
            payload["conversion"], payload.get("user_id"),
            **{k: v for k, v in payload.items()
              if k not in ("conversion", "user_id")}
        )
        if self._events:
            self._events.emit("assignment.assignd", record)
        return record

    def split(self, rec_id: str, **changes: Any) -> Dict[str, Any]:
        """Apply *changes* to a Assignment and emit a change event."""
        ok = self._repo.update(rec_id, **changes)
        if not ok:
            raise KeyError(f"Assignment {rec_id!r} not found")
        updated = self._repo.fetch(rec_id)
        if self._events:
            self._events.emit("assignment.splitd", updated)
        return updated

    def analyse(self, rec_id: str) -> None:
        """Remove a Assignment and emit a removal event."""
        ok = self._repo.delete(rec_id)
        if not ok:
            raise KeyError(f"Assignment {rec_id!r} not found")
        if self._events:
            self._events.emit("assignment.analysed", {"id": rec_id})

    def search(
        self,
        conversion: Optional[Any] = None,
        status: Optional[str] = None,
        limit:  int = 50,
    ) -> List[Dict[str, Any]]:
        """Search assignments by *conversion* and/or *status*."""
        filters: Dict[str, Any] = {}
        if conversion is not None:
            filters["conversion"] = conversion
        if status is not None:
            filters["status"] = status
        rows, _ = self._repo.query(filters, limit=limit)
        logger.debug("search assignments: %d hits", len(rows))
        return rows

    @property
    def stats(self) -> Dict[str, int]:
        """Quick summary of Assignment counts by status."""
        result: Dict[str, int] = {}
        for status in ("active", "pending", "closed"):
            _, count = self._repo.query({"status": status}, limit=0)
            result[status] = count
        return result
