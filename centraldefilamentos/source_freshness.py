from __future__ import annotations

import hashlib
import json
from collections import defaultdict
from datetime import datetime
from typing import Iterable, Mapping

from centraldefilamentos.models import RawStockItem


def stock_signature(items: Iterable[RawStockItem]) -> str:
    rows = [(item.original_name, item.stock_quantity) for item in items]
    rows.sort(key=lambda row: (row[0], row[1] is not None, row[1] or 0))
    inventory = json.dumps(rows, ensure_ascii=False, separators=(",", ":"))
    return hashlib.sha256(inventory.encode("utf-8")).hexdigest()


def apply_source_freshness(
    payload: dict[str, object],
    raw_items: Iterable[RawStockItem],
    previous_payload: Mapping[str, object] | None = None,
) -> None:
    generated_at = payload.get("generated_at", "")
    observed_at = _parse_timestamp(generated_at)
    current_timestamp = str(generated_at) if observed_at else ""
    previous_sources = (previous_payload or {}).get("sources", [])
    previous_by_id = {
        source["id"]: source
        for source in previous_sources
        if isinstance(source, dict) and source.get("id")
    } if isinstance(previous_sources, list) else {}
    items_by_source: dict[str, list[RawStockItem]] = defaultdict(list)
    for item in raw_items:
        items_by_source[item.source_id].append(item)

    for source in payload.get("sources", []):
        previous = previous_by_id.get(source["id"], {})
        previous_signature = previous.get("stock_signature", "")
        previous_since = _known_timestamp(previous.get("stock_unchanged_since"), observed_at)
        if source.get("status") != "ok":
            source["last_success_at"] = _known_timestamp(previous.get("last_success_at"), observed_at)
            source["stock_signature"] = previous_signature if isinstance(previous_signature, str) else ""
            source["stock_unchanged_since"] = previous_since
            continue

        signature = stock_signature(items_by_source[source["id"]])
        unchanged = (
            signature == previous_signature
            and source.get("source_url") == previous.get("source_url")
            and previous_since
        )
        source["last_success_at"] = current_timestamp
        source["stock_signature"] = signature
        source["stock_unchanged_since"] = previous_since if unchanged else current_timestamp


def _parse_timestamp(value: object) -> datetime | None:
    if not isinstance(value, str) or not value:
        return None
    try:
        timestamp = datetime.fromisoformat(value)
    except ValueError:
        return None
    if timestamp.tzinfo is None or timestamp.utcoffset() is None:
        return None
    return timestamp


def _known_timestamp(value: object, observed_at: datetime | None) -> str:
    timestamp = _parse_timestamp(value)
    return value if timestamp and observed_at and timestamp <= observed_at else ""
