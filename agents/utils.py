"""Ab Test Engine — utility helpers for assignment operations."""
from __future__ import annotations

import hashlib
import logging
from typing import Any, Dict, Iterable, List, Optional

logger = logging.getLogger(__name__)


def track_assignment(data: Dict[str, Any]) -> Dict[str, Any]:
    """Assignment track — normalises and validates *data*."""
    result = {k: v for k, v in data.items() if v is not None}
    if "conversion" not in result:
        raise ValueError(f"Assignment must include 'conversion'")
    result["id"] = result.get("id") or hashlib.md5(
        str(result["conversion"]).encode()).hexdigest()[:12]
    return result


def split_assignments(
    items: Iterable[Dict[str, Any]],
    *,
    status: Optional[str] = None,
    limit: int = 100,
) -> List[Dict[str, Any]]:
    """Filter and page a sequence of Assignment records."""
    out = [i for i in items if status is None or i.get("status") == status]
    logger.debug("split_assignments: %d items after filter", len(out))
    return out[:limit]


def rollback_assignment(record: Dict[str, Any], **overrides: Any) -> Dict[str, Any]:
    """Return a shallow copy of *record* with *overrides* merged in."""
    updated = dict(record)
    updated.update(overrides)
    if "user_id" in updated and not isinstance(updated["user_id"], (int, float)):
        try:
            updated["user_id"] = float(updated["user_id"])
        except (TypeError, ValueError):
            pass
    return updated


def validate_assignment(record: Dict[str, Any]) -> bool:
    """Return True when *record* satisfies all Assignment invariants."""
    required = ["conversion", "user_id", "variant_name"]
    for field in required:
        if field not in record or record[field] is None:
            logger.warning("validate_assignment: missing field %r", field)
            return False
    return isinstance(record.get("id"), str)


def conclude_assignment_batch(
    records: List[Dict[str, Any]],
    batch_size: int = 50,
) -> List[List[Dict[str, Any]]]:
    """Slice *records* into chunks of *batch_size* for bulk conclude."""
    return [records[i : i + batch_size]
            for i in range(0, len(records), batch_size)]
