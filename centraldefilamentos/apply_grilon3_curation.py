from __future__ import annotations

import argparse
from datetime import datetime
import json
from pathlib import Path
import re
import shutil
import tempfile
from typing import Mapping, Sequence
from urllib.parse import urlsplit, urlunsplit

import requests

from centraldefilamentos.build_data import (
    GRILON3_METADATA_CACHE,
    _grilon3_metadata_for_fields,
    load_grilon3_metadata,
)
from centraldefilamentos.cache_grilon3_metadata import grilon3_asset_filename
from centraldefilamentos.grilon3_scan import _identity_fields
from centraldefilamentos.models import NormalizedFields
from centraldefilamentos.thumbnails import ensure_thumbnail_for_url, thumbnail_url_for


DEFAULT_SCAN_PATH = Path(".image-curation/grilon3-scan.json")
DEFAULT_REVIEWS_PATH = Path(".image-curation/selections.json")
DEFAULT_SELECTIONS_PATH = Path("centraldefilamentos/data/grilon3_image_selections.json")
DEFAULT_ASSETS_DIR = Path("public/assets/grilon3")
DEFAULT_STOCK_PATH = Path("public/data/stock.json")
VALID_REASONS = {"preferred_angle", "best_spool", "official_primary"}
VALID_PROVENANCE = {"human", "vision_llm"}
SELECTIONS_VERSION = 1


def build_apply_plan(
    scan: object,
    reviews: object,
    existing_selections: object,
    existing_metadata: object,
    *,
    stock: object | None = None,
) -> dict[str, object]:
    scan_data = _mapping(scan, "scan")
    if scan_data.get("complete") is not True:
        raise ValueError("No se puede aplicar un scan incompleto de Grilon3")
    products = scan_data.get("products")
    if not isinstance(products, list):
        raise ValueError("El scan debe contener una lista products")
    review_data = _canonical_review_mapping(reviews)
    current_metadata = _metadata_mapping(existing_metadata)
    current_selections = _selection_records(existing_selections)

    proposed_metadata: dict[str, dict[str, str]] = {
        product_id: dict(metadata) for product_id, metadata in current_metadata.items()
    }
    proposed_selections: dict[str, dict[str, str]] = {}
    asset_changes: list[dict[str, str]] = []
    review_context: dict[str, dict[str, object]] = {}
    seen_urls: set[str] = set()
    seen_product_ids: set[str] = set()
    stock_products = _stock_grilon3_products(stock) if stock is not None else []
    candidate_ids_by_url: dict[str, list[str]] = {}
    candidate_urls_by_id: dict[str, list[str]] = {}
    if stock is not None:
        for raw_product in products:
            product = _mapping(raw_product, "producto del scan")
            product_url = _canonical_product_url(product.get("product_url"))
            identity = official_product_identity(product)
            candidate_ids = sorted(
                item["id"] for item in stock_products if _stock_matches_identity(item, identity)
            )
            candidate_ids_by_url[product_url] = candidate_ids
            for candidate_id in candidate_ids:
                candidate_urls_by_id.setdefault(candidate_id, []).append(product_url)

    page_mappings: dict[str, dict[str, object]] = {}
    quarantine: list[dict[str, object]] = []

    for raw_product in products:
        product = _mapping(raw_product, "producto del scan")
        product_url = _canonical_product_url(product.get("product_url"))
        if product_url in seen_urls:
            raise ValueError(f"Producto duplicado o conflictivo en scan: {product_url}")
        seen_urls.add(product_url)
        product_id = _required_string(product.get("product_id"), "product_id")
        if product_id in seen_product_ids:
            raise ValueError(f"product_id duplicado o conflictivo: {product_id}")
        seen_product_ids.add(product_id)
        identity = official_product_identity(product)
        if stock is None:
            mapped_product_ids = [product_id]
            mapping_status = "exact"
        else:
            candidates = candidate_ids_by_url[product_url]
            conflicting = [
                candidate_id
                for candidate_id in candidates
                if len(candidate_urls_by_id.get(candidate_id, [])) > 1
            ]
            if conflicting:
                mapped_product_ids = []
                mapping_status = "ambiguous"
            elif candidates:
                mapped_product_ids = candidates
                mapping_status = "exact" if product_id in candidates else "alias"
            else:
                mapped_product_ids = []
                mapping_status = "no_match"
        page_mappings[product_url] = {
            "status": mapping_status,
            "scan_product_id": product_id,
            "product_ids": mapped_product_ids,
            "identity": identity,
        }
        if not mapped_product_ids:
            quarantine.append({
                "product_url": product_url,
                "scan_product_id": product_id,
                "status": mapping_status,
                "identity": identity,
            })
        gallery = _gallery(product.get("gallery_image_urls"))
        fingerprint = _fingerprint(product.get("gallery_fingerprint"), "scan")
        review_context[product_url] = {
            "product_id": product_id,
            "product_ids": mapped_product_ids,
            "product_url": product_url,
            "gallery_image_urls": gallery,
            "gallery_fingerprint": fingerprint,
            "identity": identity,
        }

        official_metadata = {
            "manufacturer_product_url": product_url,
            "sku": _official_field(product, "sku"),
            "ean": _official_field(product, "ean"),
            "pantone": _official_field(product, "pantone"),
        }

        if gallery:
            raw_review = review_data.get(product_url)
            if raw_review is None:
                raise ValueError(f"revision pendiente para {product_url}")
            selected = _validated_review(product_url, gallery, fingerprint, raw_review)
            proposed_selections[product_url] = selected
            filename = grilon3_asset_filename(selected["selected_image_remote_url"])
            local_url = f"assets/grilon3/{filename}"
            official_metadata["image_remote_url"] = selected["selected_image_remote_url"]
            official_metadata["image_url"] = local_url
            if mapped_product_ids:
                asset_changes.append({
                    "product_url": product_url,
                    "remote_url": selected["selected_image_remote_url"],
                    "image_url": local_url,
                    "thumbnail_url": thumbnail_url_for(local_url),
                })

        for mapped_product_id in mapped_product_ids:
            metadata = dict(current_metadata.get(mapped_product_id, {}))
            metadata.update(official_metadata)
            if not gallery:
                metadata.pop("image_remote_url", None)
                metadata.pop("image_url", None)
            proposed_metadata[mapped_product_id] = metadata

    unknown_review_keys = set(review_data) - seen_urls
    if unknown_review_keys:
        raise ValueError(f"revision de producto desconocido: {sorted(unknown_review_keys)[0]}")

    coverage = _coverage_report(current_metadata, proposed_metadata, stock_products)
    if coverage["proposed_effective"] < coverage["baseline_effective"]:
        raise ValueError("La propuesta reduce la cobertura efectiva de metadata Grilon3")
    selection_payload: dict[str, object] = {
        "version": SELECTIONS_VERSION,
        "selections": proposed_selections,
    }
    return {
        "version": 1,
        "metadata": proposed_metadata,
        "selections": selection_payload,
        "review_context": review_context,
        "page_mappings": page_mappings,
        "quarantine": sorted(quarantine, key=lambda item: str(item["product_url"])),
        "coverage": coverage,
        "coverage_context": {
            "baseline_metadata": current_metadata,
            "stock_products": [_stock_identity_record(product) for product in stock_products],
        },
        "metadata_changes": _changes(current_metadata, proposed_metadata),
        "selection_changes": _changes(current_selections, proposed_selections),
        "asset_changes": sorted(asset_changes, key=lambda item: item["product_url"]),
    }


def apply_grilon3_plan(
    plan: Mapping[str, object],
    *,
    apply: bool,
    metadata_path: str | Path,
    selections_path: str | Path,
    assets_dir: str | Path,
) -> dict[str, object]:
    metadata, selections, approved_selections, asset_changes = _validate_apply_plan(plan)
    report = {
        "mode": "apply" if apply else "dry-run",
        "metadata_changes": plan.get("metadata_changes", []),
        "selection_changes": plan.get("selection_changes", []),
        "asset_changes": asset_changes,
        "metadata": metadata,
        "selections": selections,
        "page_mappings": plan.get("page_mappings", {}),
        "quarantine": plan.get("quarantine", []),
        "coverage": plan.get("coverage", {}),
    }
    if not apply:
        return report

    metadata_target = Path(metadata_path)
    selections_target = Path(selections_path)
    production_assets = Path(assets_dir)
    public_dir = _public_dir_for_assets(production_assets)
    staging_parent = public_dir.parent if public_dir.parent.exists() else production_assets.parent
    staging = Path(tempfile.mkdtemp(prefix=".grilon3-apply-", dir=staging_parent))
    staged_public = staging / "public"
    replacements: list[tuple[Path, Path]] = []

    primary_error: BaseException | None = None
    try:
        for raw_change in asset_changes:
            change = _mapping(raw_change, "cambio de asset")
            product_url = _canonical_product_url(change.get("product_url"))
            remote_url = _official_image_url(change.get("remote_url"))
            if approved_selections.get(product_url, {}).get("selected_image_remote_url") != remote_url:
                raise ValueError("El cambio de asset no coincide con la seleccion aprobada")
            image_url = _required_string(change.get("image_url"), "image_url")
            if image_url != f"assets/grilon3/{grilon3_asset_filename(remote_url)}":
                raise ValueError("Ruta de asset inconsistente con la URL oficial")
            staged_image = staged_public.joinpath(*Path(image_url).parts)
            staged_image.parent.mkdir(parents=True, exist_ok=True)
            staged_image.write_bytes(_download_image_bytes(remote_url))
            thumb_url = ensure_thumbnail_for_url(image_url, public_dir=staged_public)
            if not thumb_url:
                raise RuntimeError(f"No se pudo generar thumbnail para {image_url}")
            staged_thumb = staged_public.joinpath(*Path(thumb_url).parts)
            if not staged_thumb.is_file() or not staged_thumb.stat().st_size:
                raise RuntimeError(f"Thumbnail vacío para {image_url}")
            replacements.extend([
                (staged_image, public_dir.joinpath(*Path(image_url).parts)),
                (staged_thumb, public_dir.joinpath(*Path(thumb_url).parts)),
            ])

        metadata_stage = staging / "metadata.json"
        selections_stage = staging / "selections.json"
        _write_json(metadata_stage, metadata)
        _write_json(selections_stage, selections)
        json.loads(metadata_stage.read_text(encoding="utf-8"))
        json.loads(selections_stage.read_text(encoding="utf-8"))
        replacements.extend([
            (metadata_stage, metadata_target),
            (selections_stage, selections_target),
        ])
        _commit_replacements(replacements)
    except BaseException as exc:
        primary_error = exc
        raise
    finally:
        try:
            _cleanup_staging(staging)
        except Exception as cleanup_error:
            if primary_error is None:
                raise
            primary_error.add_note(f"Tambien fallo la limpieza de staging: {cleanup_error}")

    return report


def _validate_apply_plan(
    plan: Mapping[str, object],
) -> tuple[dict[str, dict[str, str]], dict, dict[str, dict[str, str]], list[dict[str, str]]]:
    plan_data = _mapping(plan, "plan")
    if plan_data.get("version") != 1:
        raise ValueError("version invalida del plan de apply")
    for changes_key in ("metadata_changes", "selection_changes"):
        if not isinstance(plan_data.get(changes_key), list):
            raise ValueError(f"{changes_key} debe ser una lista")
    metadata = _metadata_mapping(plan_data.get("metadata"))
    coverage = _mapping(plan_data.get("coverage"), "coverage")
    baseline_effective = _non_negative_int(coverage.get("baseline_effective"), "baseline_effective")
    proposed_effective = _non_negative_int(coverage.get("proposed_effective"), "proposed_effective")
    if proposed_effective < baseline_effective:
        raise ValueError("El plan reduce la cobertura efectiva de metadata Grilon3")
    coverage_context = _mapping(plan_data.get("coverage_context"), "coverage_context")
    baseline_metadata = _metadata_mapping(coverage_context.get("baseline_metadata"))
    stock_products = _stock_grilon3_products({"products": coverage_context.get("stock_products")})
    recomputed_coverage = _coverage_report(baseline_metadata, metadata, stock_products)
    if dict(coverage) != recomputed_coverage:
        raise ValueError("El reporte de cobertura no coincide con la semantica efectiva del lookup")
    missing_baseline = sorted(set(baseline_metadata) - set(metadata))
    if missing_baseline:
        raise ValueError(f"El plan no preserva metadata baseline: {missing_baseline[0]}")
    selections_payload = _mapping(plan_data.get("selections"), "selections del plan")
    if selections_payload.get("version") != SELECTIONS_VERSION:
        raise ValueError("version invalida del manifiesto de selecciones")
    selections = _selection_records(selections_payload)
    context = _review_context(plan_data.get("review_context"))
    _validate_mapping_audit(plan_data, context)
    stock_by_id = {str(product["id"]): product for product in stock_products}
    mapped_ids = {
        product_id
        for product_context in context.values()
        for product_id in product_context["product_ids"]
    }
    for product_id, baseline_record in baseline_metadata.items():
        if product_id not in mapped_ids and metadata.get(product_id) != baseline_record:
            raise ValueError(f"El plan altera metadata legacy sin mapping oficial: {product_id}")

    validated_selections: dict[str, dict[str, str]] = {}
    for product_url, raw_selection in selections.items():
        product_context = context.get(product_url)
        if product_context is None:
            raise ValueError(f"Seleccion sin contexto de galeria actual: {product_url}")
        gallery = product_context["gallery_image_urls"]
        if not gallery:
            raise ValueError(f"Seleccion para producto sin galeria: {product_url}")
        validated_selections[product_url] = _validated_review(
            product_url,
            gallery,
            product_context["gallery_fingerprint"],
            raw_selection,
        )

    raw_asset_changes = plan_data.get("asset_changes")
    if not isinstance(raw_asset_changes, list):
        raise ValueError("asset_changes debe ser una lista")
    asset_by_product: dict[str, dict[str, str]] = {}
    for raw_change in raw_asset_changes:
        change = _mapping(raw_change, "cambio de asset")
        product_url = _canonical_product_url(change.get("product_url"))
        if product_url in asset_by_product:
            raise ValueError(f"asset duplicado o conflictivo: {product_url}")
        selection = validated_selections.get(product_url)
        if selection is None:
            raise ValueError(f"asset sin seleccion aprobada: {product_url}")
        remote_url = _official_image_url(change.get("remote_url"))
        if remote_url != selection["selected_image_remote_url"]:
            raise ValueError(f"asset no coincide con seleccion aprobada: {product_url}")
        image_url = _required_string(change.get("image_url"), "image_url")
        expected_image_url = f"assets/grilon3/{grilon3_asset_filename(remote_url)}"
        if image_url != expected_image_url:
            raise ValueError(f"asset local inconsistente: {product_url}")
        thumb_url = _required_string(change.get("thumbnail_url"), "thumbnail_url")
        if thumb_url != thumbnail_url_for(image_url):
            raise ValueError(f"thumbnail inconsistente: {product_url}")
        asset_by_product[product_url] = {
            "product_url": product_url,
            "remote_url": remote_url,
            "image_url": image_url,
            "thumbnail_url": thumb_url,
        }
    required_asset_urls = {
        product_url for product_url, product_context in context.items()
        if product_context["product_ids"] and product_context["gallery_image_urls"]
    }
    if set(asset_by_product) != required_asset_urls:
        missing = sorted(required_asset_urls - set(asset_by_product))
        if not missing:
            raise ValueError("El plan contiene assets fuera del mapping aprobado")
        raise ValueError(f"Falta asset requerido por seleccion aprobada: {missing[0]}")

    context_product_ids: set[str] = set()
    normalized_metadata: dict[str, dict[str, str]] = {
        product_id: dict(product_metadata) for product_id, product_metadata in metadata.items()
    }
    for product_url, product_context in context.items():
        product_ids = product_context["product_ids"]
        for product_id in product_ids:
            if product_id in context_product_ids:
                raise ValueError(f"product_id duplicado o conflictivo: {product_id}")
            context_product_ids.add(product_id)
            stock_product = stock_by_id.get(product_id)
            if stock_products and (
                stock_product is None
                or not _stock_matches_identity(stock_product, product_context["identity"])
            ):
                raise ValueError(f"El mapping mezcla una presentacion incompatible: {product_id}")
            product_metadata = metadata.get(product_id)
            if product_metadata is None:
                raise ValueError(f"Falta metadata para {product_id}")
            if _canonical_product_url(product_metadata.get("manufacturer_product_url")) != product_url:
                raise ValueError(f"Metadata y product_url no coinciden: {product_id}")
            normalized_product_metadata = dict(product_metadata)
            normalized_product_metadata["manufacturer_product_url"] = product_url
            normalized_metadata[product_id] = normalized_product_metadata
        selection = validated_selections.get(product_url)
        if selection is None:
            for product_id in product_ids:
                product_metadata = normalized_metadata[product_id]
                if product_metadata.get("image_url") or product_metadata.get("image_remote_url"):
                    raise ValueError(f"Producto sin galeria no puede publicar imagen: {product_url}")
                product_metadata.pop("image_url", None)
                product_metadata.pop("image_remote_url", None)
            continue
        if not product_ids:
            continue
        asset = asset_by_product[product_url]
        for product_id in product_ids:
            product_metadata = normalized_metadata[product_id]
            if product_metadata.get("image_remote_url") != selection["selected_image_remote_url"]:
                raise ValueError(f"Metadata y seleccion no coinciden: {product_url}")
            if product_metadata.get("image_url") != asset["image_url"]:
                raise ValueError(f"Metadata y asset no coinciden: {product_url}")
            product_metadata["image_remote_url"] = selection["selected_image_remote_url"]
            product_metadata["image_url"] = asset["image_url"]

    ordered_assets = [asset_by_product[url] for url in sorted(asset_by_product)]
    normalized_selections: dict[str, object] = {
        "version": SELECTIONS_VERSION,
        "selections": {
            product_url: validated_selections[product_url]
            for product_url in sorted(validated_selections)
        },
    }
    return normalized_metadata, normalized_selections, validated_selections, ordered_assets


def _validate_mapping_audit(
    plan: Mapping[str, object],
    context: Mapping[str, Mapping[str, object]],
) -> None:
    raw_mappings = _mapping(plan.get("page_mappings"), "page_mappings")
    mappings: dict[str, Mapping[str, object]] = {}
    for raw_url, raw_mapping in raw_mappings.items():
        product_url = _canonical_product_url(raw_url)
        if product_url in mappings:
            raise ValueError(f"mapping de auditoria duplicado: {product_url}")
        mappings[product_url] = _mapping(raw_mapping, f"mapping {product_url}")
    if set(mappings) != set(context):
        raise ValueError("El audit de mapping no coincide con el contexto revisado")

    expected_quarantine: set[str] = set()
    for product_url, product_context in context.items():
        mapping = mappings[product_url]
        product_ids = _string_list(mapping.get("product_ids"), "product_ids de mapping")
        if product_ids != product_context["product_ids"]:
            raise ValueError(f"El audit de mapping no coincide con sus aliases: {product_url}")
        if _required_string(mapping.get("scan_product_id"), "scan_product_id") != product_context["product_id"]:
            raise ValueError(f"El audit de mapping no coincide con el scan: {product_url}")
        if _identity_mapping(mapping.get("identity")) != product_context["identity"]:
            raise ValueError(f"El audit de mapping altera la identidad oficial: {product_url}")
        status = _required_string(mapping.get("status"), "status de mapping")
        if status not in {"exact", "alias", "no_match", "ambiguous"}:
            raise ValueError(f"status de mapping invalido: {status}")
        if bool(product_ids) != (status in {"exact", "alias"}):
            raise ValueError(f"status de mapping inconsistente: {product_url}")
        if not product_ids:
            expected_quarantine.add(product_url)

    raw_quarantine = plan.get("quarantine")
    if not isinstance(raw_quarantine, list):
        raise ValueError("quarantine debe ser una lista")
    quarantine_urls = {
        _canonical_product_url(_mapping(item, "item de quarantine").get("product_url"))
        for item in raw_quarantine
    }
    if quarantine_urls != expected_quarantine or len(quarantine_urls) != len(raw_quarantine):
        raise ValueError("El audit de quarantine no coincide con los no-match")


def _review_context(value: object) -> dict[str, dict[str, object]]:
    mapping = _mapping(value, "review_context")
    context: dict[str, dict[str, object]] = {}
    for raw_key, raw_context in mapping.items():
        product_url = _canonical_product_url(raw_key)
        if product_url in context:
            raise ValueError(f"Contexto duplicado o conflictivo: {product_url}")
        data = _mapping(raw_context, f"contexto {raw_key}")
        if _canonical_product_url(data.get("product_url")) != product_url:
            raise ValueError(f"Key y product_url no coinciden: {product_url}")
        context[product_url] = {
            "product_id": _required_string(data.get("product_id"), "product_id"),
            "product_ids": _string_list(data.get("product_ids"), "product_ids"),
            "product_url": product_url,
            "gallery_image_urls": _gallery(data.get("gallery_image_urls")),
            "gallery_fingerprint": _fingerprint(data.get("gallery_fingerprint"), "contexto"),
            "identity": _identity_mapping(data.get("identity")),
        }
    return context


def official_product_identity(product: Mapping[str, object]) -> dict[str, object]:
    fields = _identity_fields(dict(product))
    diameter_mm = fields.diameter_mm
    category_path = product.get("category_path", [])
    labels = category_path if isinstance(category_path, list) else []
    presentation_text = " ".join([str(product.get("title", "")), *map(str, labels)])
    if re.search(r"(?:2[,.]85|\b285\s*mm\b)", presentation_text, re.IGNORECASE):
        diameter_mm = 2.85
    return {
        "material": fields.material,
        "variant": fields.variant,
        "color": fields.color,
        "diameter_mm": diameter_mm,
        "weight_g": fields.weight_g,
        "brand": fields.brand,
    }


def _stock_grilon3_products(stock: object) -> list[dict[str, object]]:
    stock_data = _mapping(stock, "stock")
    products = stock_data.get("products")
    if not isinstance(products, list):
        raise ValueError("El stock debe contener una lista products")
    result: list[dict[str, object]] = []
    seen: set[str] = set()
    for raw_product in products:
        product = _mapping(raw_product, "producto de stock")
        if product.get("brand") != "Grilon3":
            continue
        product_id = _required_string(product.get("id"), "id de stock")
        if product_id in seen:
            raise ValueError(f"id de stock duplicado: {product_id}")
        seen.add(product_id)
        result.append({**product, "id": product_id})
    return result


def _stock_matches_identity(product: Mapping[str, object], identity: Mapping[str, object]) -> bool:
    return all(product.get(key) == identity.get(key) for key in (
        "material", "variant", "color", "diameter_mm", "weight_g", "brand"
    ))


def _stock_identity_record(product: Mapping[str, object]) -> dict[str, object]:
    return {
        "id": str(product["id"]),
        "material": str(product.get("material", "")),
        "variant": str(product.get("variant", "")),
        "color": str(product.get("color", "")),
        "diameter_mm": product.get("diameter_mm"),
        "weight_g": product.get("weight_g"),
        "brand": str(product.get("brand", "")),
        "manufacturer_name": str(product.get("manufacturer_name", "")),
        "subrange": str(product.get("subrange", "")),
        "finish": str(product.get("finish", "")),
    }


def _identity_mapping(value: object) -> dict[str, object]:
    identity = _mapping(value, "identidad oficial")
    result: dict[str, object] = {}
    for key in ("material", "variant", "color", "brand"):
        raw_value = identity.get(key, "")
        if not isinstance(raw_value, str):
            raise ValueError(f"{key} oficial invalido")
        result[key] = raw_value
    diameter = identity.get("diameter_mm")
    if diameter is not None and (isinstance(diameter, bool) or not isinstance(diameter, (int, float))):
        raise ValueError("diameter_mm oficial invalido")
    weight = identity.get("weight_g")
    if weight is not None and (isinstance(weight, bool) or not isinstance(weight, int)):
        raise ValueError("weight_g oficial invalido")
    result["diameter_mm"] = diameter
    result["weight_g"] = weight
    return result


def _coverage_report(
    baseline: Mapping[str, dict[str, str]],
    proposed: Mapping[str, dict[str, str]],
    stock_products: Sequence[Mapping[str, object]],
) -> dict[str, int]:
    stock_ids = {str(product["id"]) for product in stock_products}
    return {
        "stock_product_count": len(stock_products),
        "baseline_exact": len(stock_ids & set(baseline)),
        "proposed_exact": len(stock_ids & set(proposed)),
        "baseline_effective": _effective_coverage(baseline, stock_products),
        "proposed_effective": _effective_coverage(proposed, stock_products),
    }


def _effective_coverage(
    metadata: Mapping[str, dict[str, str]],
    stock_products: Sequence[Mapping[str, object]],
) -> int:
    return sum(
        bool(_grilon3_metadata_for_fields(metadata, _fields_from_stock(product)))
        for product in stock_products
    )


def _fields_from_stock(product: Mapping[str, object]) -> NormalizedFields:
    return NormalizedFields(
        material=str(product.get("material", "")),
        variant=str(product.get("variant", "")),
        color=str(product.get("color", "")),
        diameter_mm=product.get("diameter_mm") if isinstance(product.get("diameter_mm"), (int, float)) else None,
        weight_g=product.get("weight_g") if isinstance(product.get("weight_g"), int) else None,
        brand=str(product.get("brand", "")),
        manufacturer_name=str(product.get("manufacturer_name", "")),
        subrange=str(product.get("subrange", "")),
        finish=str(product.get("finish", "")),
    )


def _string_list(value: object, label: str) -> list[str]:
    if not isinstance(value, list) or any(not isinstance(item, str) or not item for item in value):
        raise ValueError(f"{label} debe ser una lista de strings")
    if len(value) != len(set(value)):
        raise ValueError(f"{label} contiene duplicados")
    return list(value)


def _non_negative_int(value: object, label: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise ValueError(f"{label} debe ser un entero no negativo")
    return value


def _commit_replacements(replacements: list[tuple[Path, Path]]) -> None:
    snapshots: dict[Path, bytes | None] = {}
    committed: list[Path] = []
    sibling_temps: list[Path] = []
    try:
        for source, target in replacements:
            snapshots.setdefault(target, target.read_bytes() if target.exists() else None)
            target.parent.mkdir(parents=True, exist_ok=True)
            handle = tempfile.NamedTemporaryFile(
                prefix=f".{target.name}.", suffix=".tmp", dir=target.parent, delete=False
            )
            temp_path = Path(handle.name)
            sibling_temps.append(temp_path)
            with handle:
                handle.write(source.read_bytes())
                handle.flush()
            _replace_path(temp_path, target)
            sibling_temps.remove(temp_path)
            committed.append(target)
    except Exception:
        for target in reversed(committed):
            original = snapshots[target]
            if original is None:
                target.unlink(missing_ok=True)
            else:
                _replace_bytes(target, original)
        raise
    finally:
        for temp_path in sibling_temps:
            temp_path.unlink(missing_ok=True)


def _replace_bytes(target: Path, value: bytes) -> None:
    handle = tempfile.NamedTemporaryFile(
        prefix=f".{target.name}.rollback.", suffix=".tmp", dir=target.parent, delete=False
    )
    temp_path = Path(handle.name)
    try:
        with handle:
            handle.write(value)
            handle.flush()
        temp_path.replace(target)
    finally:
        temp_path.unlink(missing_ok=True)


def _replace_path(source: Path, target: Path) -> Path:
    return source.replace(target)


def _cleanup_staging(staging: Path) -> None:
    shutil.rmtree(staging)


def _download_image_bytes(remote_url: str, timeout_seconds: int = 12) -> bytes:
    url = _official_image_url(remote_url)
    response = requests.get(url, timeout=timeout_seconds)
    response.raise_for_status()
    if not response.content:
        raise ValueError(f"La imagen oficial está vacía: {url}")
    return response.content


def _validated_review(
    product_url: str,
    gallery: list[str],
    fingerprint: str,
    raw_review: object,
) -> dict[str, str]:
    review = _mapping(raw_review, "revisión")
    review_url = _canonical_product_url(review.get("product_url"))
    if review_url != product_url:
        raise ValueError(f"La URL de la revision no coincide: {product_url}")
    review_fingerprint = _fingerprint(review.get("gallery_fingerprint"), "revisión")
    if review_fingerprint != fingerprint:
        raise ValueError(f"El fingerprint de la revision esta desactualizado: {product_url}")
    selected_url = _official_image_url(review.get("selected_image_remote_url"))
    if selected_url not in gallery:
        raise ValueError(f"La imagen elegida no pertenece a la galeria oficial: {product_url}")
    reason = _required_string(review.get("selection_reason"), "selection_reason")
    if reason not in VALID_REASONS:
        raise ValueError(f"motivo de seleccion invalido: {reason}")
    reviewed_at = _required_string(review.get("reviewed_at"), "reviewed_at")
    try:
        datetime.fromisoformat(reviewed_at.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError("reviewed_at debe ser una fecha ISO valida") from exc
    normalized = {
        "product_url": product_url,
        "selected_image_remote_url": selected_url,
        "selection_reason": reason,
        "gallery_fingerprint": fingerprint,
        "reviewed_at": reviewed_at,
    }
    if "provenance" in review:
        provenance = review.get("provenance")
        if not isinstance(provenance, str) or provenance not in VALID_PROVENANCE:
            raise ValueError("procedencia de revision invalida")
        normalized["provenance"] = provenance
    return normalized


def _gallery(value: object) -> list[str]:
    if not isinstance(value, list):
        raise ValueError("gallery_image_urls debe ser una lista")
    gallery = [_official_image_url(url) for url in value]
    if len(gallery) != len(set(gallery)):
        raise ValueError("La galería oficial contiene URLs duplicadas")
    return gallery


def _canonical_product_url(value: object) -> str:
    raw_url = _required_string(value, "product_url")
    parsed = _strict_official_url(raw_url, "producto")
    path = parsed.path.rstrip("/")
    match = re.fullmatch(r"/producto/([a-z0-9]+(?:-[a-z0-9]+)*)", path)
    if not match:
        raise ValueError(f"URL de producto Grilon3 invalida: {raw_url}")
    return f"https://grilon3.com.ar/producto/{match.group(1)}/"


def _official_image_url(value: object) -> str:
    raw_url = _required_string(value, "URL de imagen")
    try:
        parsed = _strict_official_url(raw_url, "imagen")
    except ValueError as exc:
        raise ValueError(f"URL de imagen oficial invalida: {raw_url}") from exc
    if not parsed.path.startswith("/") or parsed.path.endswith("/"):
        raise ValueError(f"URL de imagen oficial invalida: {raw_url}")
    return urlunsplit(("https", "grilon3.com.ar", parsed.path, "", ""))


def _strict_official_url(raw_url: str, kind: str):
    try:
        parsed = urlsplit(raw_url)
        port = parsed.port
    except ValueError as exc:
        raise ValueError(f"URL de {kind} Grilon3 invalida: {raw_url}") from exc
    host = (parsed.hostname or "").lower()
    if (
        parsed.scheme != "https"
        or host not in {"grilon3.com.ar", "www.grilon3.com.ar"}
        or parsed.username is not None
        or parsed.password is not None
        or port is not None
        or parsed.query
        or parsed.fragment
        or "?" in raw_url
        or "#" in raw_url
        or "%" in parsed.path
        or "\\" in parsed.path
        or any(segment in {".", ".."} for segment in parsed.path.split("/"))
    ):
        raise ValueError(f"URL de {kind} Grilon3 invalida: {raw_url}")
    return parsed


def _fingerprint(value: object, source: str) -> str:
    fingerprint = _required_string(value, f"fingerprint de {source}").lower()
    if len(fingerprint) != 64 or any(char not in "0123456789abcdef" for char in fingerprint):
        raise ValueError(f"Fingerprint inválido en {source}")
    return fingerprint


def _official_field(product: Mapping[str, object], key: str) -> str:
    value = product.get(key, "")
    if value is None:
        return ""
    if not isinstance(value, str):
        raise ValueError(f"{key} oficial debe ser texto")
    return value


def _metadata_mapping(value: object) -> dict[str, dict[str, str]]:
    mapping = _mapping(value, "metadata")
    clean: dict[str, dict[str, str]] = {}
    for key, raw_data in mapping.items():
        data = _mapping(raw_data, f"metadata {key}")
        product_id = _required_string(key, "product_id de metadata")
        clean_data: dict[str, str] = {}
        for field, field_value in data.items():
            if not isinstance(field, str) or not isinstance(field_value, str):
                raise ValueError(f"metadata {product_id}.{field} debe ser texto")
            clean_data[field] = field_value
        clean[product_id] = clean_data
    return clean


def _canonical_review_mapping(value: object) -> dict[str, object]:
    mapping = _mapping(value, "revisiones")
    reviews: dict[str, object] = {}
    for raw_key, review in mapping.items():
        product_url = _canonical_product_url(raw_key)
        if product_url in reviews:
            raise ValueError(f"Revision duplicada o conflictiva: {product_url}")
        reviews[product_url] = review
    return reviews


def _selection_records(value: object) -> dict[str, dict[str, str]]:
    mapping = _mapping(value, "selecciones existentes")
    if "version" in mapping or "selections" in mapping:
        if mapping.get("version") != SELECTIONS_VERSION:
            raise ValueError("version invalida del manifiesto de selecciones")
        mapping = _mapping(mapping.get("selections"), "selections")
    records: dict[str, dict[str, str]] = {}
    for key, raw_record in mapping.items():
        canonical = _canonical_product_url(key)
        if canonical in records:
            raise ValueError(f"Selección duplicada o conflictiva: {canonical}")
        record = _mapping(raw_record, f"selección {key}")
        records[canonical] = {str(field): str(field_value) for field, field_value in record.items()}
    return records


def _mapping(value: object, label: str) -> dict:
    if not isinstance(value, dict):
        raise ValueError(f"{label} debe ser un objeto JSON")
    return value


def _required_string(value: object, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"Falta {label}")
    return value.strip()


def _changes(before: Mapping, after: Mapping) -> list[dict[str, object]]:
    changes = []
    for key in sorted(set(before) | set(after)):
        if before.get(key) == after.get(key):
            continue
        changes.append({"key": key, "before": before.get(key), "after": after.get(key)})
    return changes


def _write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _read_json(path: Path, fallback: object) -> object:
    if not path.exists():
        return fallback
    return json.loads(path.read_text(encoding="utf-8"))


def _public_dir_for_assets(assets_dir: Path) -> Path:
    if assets_dir.name != "grilon3" or assets_dir.parent.name != "assets":
        raise ValueError("assets_dir debe terminar en public/assets/grilon3")
    return assets_dir.parent.parent


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Valida y aplica la curación oficial Grilon3.")
    parser.add_argument("--scan", default=str(DEFAULT_SCAN_PATH))
    parser.add_argument("--reviews", default=str(DEFAULT_REVIEWS_PATH))
    parser.add_argument("--metadata", default=str(GRILON3_METADATA_CACHE))
    parser.add_argument("--selections", default=str(DEFAULT_SELECTIONS_PATH))
    parser.add_argument("--assets-dir", default=str(DEFAULT_ASSETS_DIR))
    parser.add_argument("--stock", default=str(DEFAULT_STOCK_PATH))
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args(argv)

    metadata_path = Path(args.metadata)
    selections_path = Path(args.selections)
    plan = build_apply_plan(
        _read_json(Path(args.scan), None),
        _read_json(Path(args.reviews), {}),
        _read_json(selections_path, {}),
        _read_json(metadata_path, {}),
        stock=_read_json(Path(args.stock), None),
    )
    report = apply_grilon3_plan(
        plan,
        apply=args.apply,
        metadata_path=metadata_path,
        selections_path=selections_path,
        assets_dir=args.assets_dir,
    )
    print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
