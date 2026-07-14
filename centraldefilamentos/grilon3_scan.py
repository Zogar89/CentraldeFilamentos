from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
import hashlib
import json
from pathlib import Path
from typing import Sequence

from centraldefilamentos.connectors.grilon3_catalog import (
    CatalogProduct,
    CatalogProductDetail,
    fetch_grilon3_active_catalog,
    fetch_grilon3_product_detail,
    fetch_grilon3_sitemap_catalog,
)
from centraldefilamentos.models import RawStockItem
from centraldefilamentos.normalize import normalize_record
from centraldefilamentos.providers import MANUFACTURERS

DEFAULT_OUTPUT_PATH = Path(".image-curation/grilon3-scan.json")


def scan_grilon3_catalog(
    timeout_seconds: int = 4,
    max_workers: int = 12,
    sitemap_classifications: dict[str, str] | None = None,
) -> dict[str, object]:
    if max_workers < 1:
        raise ValueError("max_workers debe ser al menos 1")

    active_catalog, reported_total = fetch_grilon3_active_catalog(
        timeout_seconds=timeout_seconds,
    )
    sitemap_catalog = fetch_grilon3_sitemap_catalog(
        timeout_seconds=timeout_seconds,
    )

    active_by_url = {
        _canonical_url(product.product_url): product
        for product in active_catalog.values()
    }
    sitemap_urls = {
        _canonical_url(product.product_url)
        for product in sitemap_catalog.values()
    }
    classifications = {
        _canonical_url(url): classification.strip() or "unclassified"
        for url, classification in (sitemap_classifications or {}).items()
    }

    details, detail_errors, detail_attempts = _fetch_details(
        active_by_url,
        timeout_seconds=timeout_seconds,
        max_workers=max_workers,
    )
    products = [
        _product_payload(product, details.get(product_url), product_url in detail_errors)
        for product_url, product in sorted(active_by_url.items())
    ]

    sitemap_only = [
        {
            "url": url,
            "classification": classifications.get(url, "unclassified"),
        }
        for url in sorted(sitemap_urls - set(active_by_url))
    ]
    unclassified_count = sum(
        item["classification"] == "unclassified"
        for item in sitemap_only
    )
    active_count = len(active_by_url)
    detail_success_count = len(details)
    detail_error_records = [
        detail_errors[url]
        for url in sorted(detail_errors)
    ]

    warnings: list[str] = []
    if reported_total is None:
        warnings.append("reported_total_missing")
    elif active_count != reported_total:
        warnings.append("active_count_mismatch")
    if detail_error_records:
        warnings.append("detail_requests_failed")
    if unclassified_count:
        warnings.append("unclassified_sitemap_only_urls")

    complete = (
        reported_total is not None
        and active_count == reported_total
        and detail_success_count == active_count
        and unclassified_count == 0
    )

    return {
        "summary": {
            "active_count": active_count,
            "reported_total": reported_total,
            "detail_success_count": detail_success_count,
            "detail_error_count": len(detail_error_records),
            "detail_initial_error_count": sum(
                attempts["attempts"][0]["status"] == "error"
                for attempts in detail_attempts
            ),
            "detail_retry_attempt_count": sum(
                len(attempts["attempts"]) == 2
                for attempts in detail_attempts
            ),
            "detail_retry_success_count": sum(
                len(attempts["attempts"]) == 2
                and attempts["attempts"][1]["status"] == "success"
                for attempts in detail_attempts
            ),
            "detail_retry_error_count": sum(
                len(attempts["attempts"]) == 2
                and attempts["attempts"][1]["status"] == "error"
                for attempts in detail_attempts
            ),
            "sitemap_count": len(sitemap_urls),
            "sitemap_only_count": len(sitemap_only),
            "unclassified_sitemap_only_count": unclassified_count,
        },
        "products": products,
        "sitemap_only": sitemap_only,
        "detail_errors": detail_error_records,
        "detail_attempts": detail_attempts,
        "warnings": warnings,
        "complete": complete,
    }


def write_grilon3_scan(
    payload: dict[str, object],
    output_path: str | Path = DEFAULT_OUTPUT_PATH,
) -> None:
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _fetch_details(
    active_by_url: dict[str, CatalogProduct],
    timeout_seconds: int,
    max_workers: int,
) -> tuple[
    dict[str, CatalogProductDetail],
    dict[str, dict[str, str]],
    list[dict[str, object]],
]:
    details: dict[str, CatalogProductDetail] = {}
    attempts: dict[str, list[dict[str, object]]] = {
        url: [] for url in active_by_url
    }

    def run_attempt(urls: Sequence[str], attempt_number: int) -> dict[str, dict[str, str]]:
        errors: dict[str, dict[str, str]] = {}
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {
                executor.submit(fetch_grilon3_product_detail, url, timeout_seconds): url
                for url in urls
            }
            for future in as_completed(futures):
                url = futures[future]
                try:
                    details[url] = future.result()
                except Exception as exc:
                    error = {
                        "url": url,
                        "error_type": type(exc).__name__,
                        "message": str(exc),
                    }
                    errors[url] = error
                    attempts[url].append({
                        "attempt": attempt_number,
                        "status": "error",
                        "error_type": error["error_type"],
                        "message": error["message"],
                    })
                else:
                    attempts[url].append({
                        "attempt": attempt_number,
                        "status": "success",
                    })
        return errors

    initial_errors = run_attempt(sorted(active_by_url), 1)
    final_errors = run_attempt(sorted(initial_errors), 2) if initial_errors else {}
    return details, final_errors, [
        {"url": url, "attempts": attempts[url]}
        for url in sorted(attempts)
    ]


def _product_payload(
    product: CatalogProduct,
    detail: CatalogProductDetail | None,
    detail_failed: bool,
) -> dict[str, object]:
    product_url = _canonical_url(product.product_url)
    fields = normalize_record(
        RawStockItem(
            source_id="grilon3_catalog",
            provider_name="Grilon3",
            provider_zone="",
            provider_url=MANUFACTURERS["grilon3"].official_site_url,
            original_name=product.title,
            stock_quantity=None,
            source_url=product_url,
            brand_hint="Grilon3",
        )
    )
    gallery_urls = list(detail.gallery_image_urls) if detail else []
    warnings: list[str] = []
    if detail_failed:
        warnings.append("detail_request_failed")
    if not gallery_urls:
        warnings.append("missing_gallery")

    sku = detail.sku if detail else ""
    ean = detail.ean if detail else ""
    pantone = detail.pantone if detail else ""
    for field_name, value in (("sku", sku), ("ean", ean), ("pantone", pantone)):
        if not value:
            warnings.append(f"missing_{field_name}")

    return {
        "product_id": product.product_id,
        "title": product.title,
        "product_url": product_url,
        "category_path": list(detail.category_path) if detail else [],
        "gallery_image_urls": gallery_urls,
        "gallery_fingerprint": _gallery_fingerprint(gallery_urls),
        "material": fields.material,
        "variant": fields.variant,
        "color": fields.color,
        "diameter_mm": fields.diameter_mm,
        "weight_g": fields.weight_g,
        "brand": fields.brand,
        "manufacturer_name": fields.manufacturer_name,
        "sku": sku,
        "ean": ean,
        "pantone": pantone,
        "warnings": warnings,
    }


def _gallery_fingerprint(gallery_image_urls: Sequence[str]) -> str:
    representation = "\n".join(gallery_image_urls)
    return hashlib.sha256(representation.encode("utf-8")).hexdigest()


def _canonical_url(url: str) -> str:
    return url.strip().rstrip("/") + "/"


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Escanea el catálogo oficial Grilon3 y escribe un draft auditable.",
    )
    parser.add_argument("--output", default=str(DEFAULT_OUTPUT_PATH))
    parser.add_argument("--timeout-seconds", type=int, default=4)
    parser.add_argument("--max-workers", type=int, default=12)
    args = parser.parse_args(argv)

    payload = scan_grilon3_catalog(
        timeout_seconds=args.timeout_seconds,
        max_workers=args.max_workers,
    )
    write_grilon3_scan(payload, args.output)
    summary = payload["summary"]
    print(
        f"Draft Grilon3 escrito en {args.output}: "
        f"{summary['active_count']} productos activos; complete={payload['complete']}"
    )
    return 0 if payload["complete"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
