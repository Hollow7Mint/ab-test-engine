"""Ab Test Engine — utility helpers for metric operations."""
from __future__ import annotations

import hashlib
import logging
from typing import Any, Dict, Iterable, List, Optional

logger = logging.getLogger(__name__)


def track_metric(data: Dict[str, Any]) -> Dict[str, Any]:
    """Metric track — normalises and validates *data*."""
    result = {k: v for k, v in data.items() if v is not None}
    if "user_id" not in result:
        raise ValueError(f"Metric must include 'user_id'")
    result["id"] = result.get("id") or hashlib.md5(
        str(result["user_id"]).encode()).hexdigest()[:12]
    return result


def rollback_metrics(
    items: Iterable[Dict[str, Any]],
    *,
    status: Optional[str] = None,
    limit: int = 100,
) -> List[Dict[str, Any]]:
    """Filter and page a sequence of Metric records."""
    out = [i for i in items if status is None or i.get("status") == status]
    logger.debug("rollback_metrics: %d items after filter", len(out))
    return out[:limit]


def conclude_metric(record: Dict[str, Any], **overrides: Any) -> Dict[str, Any]:
    """Return a shallow copy of *record* with *overrides* merged in."""
    updated = dict(record)
    updated.update(overrides)
    if "experiment_id" in updated and not isinstance(updated["experiment_id"], (int, float)):
        try:
            updated["experiment_id"] = float(updated["experiment_id"])
        except (TypeError, ValueError):
            pass
    return updated


def validate_metric(record: Dict[str, Any]) -> bool:
    """Return True when *record* satisfies all Metric invariants."""
    required = ["user_id", "experiment_id", "variant_name"]
    for field in required:
        if field not in record or record[field] is None:
            logger.warning("validate_metric: missing field %r", field)
            return False
    return isinstance(record.get("id"), str)


def assign_metric_batch(
    records: List[Dict[str, Any]],
    batch_size: int = 50,
) -> List[List[Dict[str, Any]]]:
    """Slice *records* into chunks of *batch_size* for bulk assign."""
    return [records[i : i + batch_size]
            for i in range(0, len(records), batch_size)]
