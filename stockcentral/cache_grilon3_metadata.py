from __future__ import annotations

import argparse
import json
from pathlib import Path

from stockcentral.build_data import GRILON3_METADATA_CACHE
from stockcentral.connectors.grilon3_catalog import (
    enrich_grilon3_catalog_details,
    fetch_grilon3_catalog,
    fetch_grilon3_sitemap_catalog,
)
from stockcentral.models import RawStockItem
from stockcentral.normalize import normalize_record
from stockcentral.providers import MANUFACTURERS


def build_grilon3_metadata_cache(timeout_seconds: int = 4, max_workers: int = 12) -> dict[str, dict[str, str]]:
    catalog = fetch_grilon3_catalog(MANUFACTURERS["grilon3"].products_url)
    catalog.update(fetch_grilon3_sitemap_catalog())
    enriched = enrich_grilon3_catalog_details(
        catalog,
        timeout_seconds=timeout_seconds,
        max_workers=max_workers,
    )
    cache: dict[str, dict[str, str]] = {}
    for _, product in sorted(enriched.items()):
        data = {
            "pantone": product.pantone,
            "sku": product.sku,
            "ean": product.ean,
            "image_url": product.image_url,
        }
        clean = {key: value for key, value in data.items() if value}
        if clean:
            cache[grilon3_metadata_cache_key(product.title)] = clean
    return cache


def write_grilon3_metadata_cache(
    output_path: str | Path = GRILON3_METADATA_CACHE,
    timeout_seconds: int = 4,
    max_workers: int = 12,
) -> dict[str, dict[str, str]]:
    cache = build_grilon3_metadata_cache(timeout_seconds=timeout_seconds, max_workers=max_workers)
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(cache, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return cache


def grilon3_metadata_cache_key(title: str) -> str:
    fields = normalize_record(
        RawStockItem(
            source_id="grilon3_catalog",
            provider_name="Grilon3",
            provider_zone="",
            provider_url=MANUFACTURERS["grilon3"].official_site_url,
            original_name=title,
            stock_quantity=None,
            source_url=MANUFACTURERS["grilon3"].products_url,
            brand_hint="Grilon3",
        )
    )
    parts = [fields.material, fields.variant, fields.color, fields.brand]
    return "-".join(slug(part) for part in parts if part)


def slug(value: str) -> str:
    import re
    import unicodedata

    normalized = unicodedata.normalize("NFKD", value)
    without_marks = "".join(char for char in normalized if not unicodedata.combining(char))
    folded = without_marks.lower()
    return re.sub(r"[^a-z0-9]+", "-", folded).strip("-")


def main() -> None:
    parser = argparse.ArgumentParser(description="Actualiza la cache local de metadatos desde fichas Grilon3.")
    parser.add_argument("--output", default=str(GRILON3_METADATA_CACHE))
    parser.add_argument("--timeout-seconds", type=int, default=4)
    parser.add_argument("--max-workers", type=int, default=12)
    args = parser.parse_args()

    cache = write_grilon3_metadata_cache(
        output_path=args.output,
        timeout_seconds=args.timeout_seconds,
        max_workers=args.max_workers,
    )
    print(f"Cache Grilon3 actualizada: {len(cache)} productos")


if __name__ == "__main__":
    main()
