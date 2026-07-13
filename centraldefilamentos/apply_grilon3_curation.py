from __future__ import annotations

import argparse
from datetime import datetime
import json
from pathlib import Path
import shutil
import tempfile
from typing import Mapping, Sequence
from urllib.parse import urlparse

import requests

from centraldefilamentos.build_data import GRILON3_METADATA_CACHE, load_grilon3_metadata
from centraldefilamentos.cache_grilon3_metadata import grilon3_asset_filename
from centraldefilamentos.thumbnails import ensure_thumbnail_for_url, thumbnail_url_for


DEFAULT_SCAN_PATH = Path(".image-curation/grilon3-scan.json")
DEFAULT_REVIEWS_PATH = Path(".image-curation/selections.json")
DEFAULT_SELECTIONS_PATH = Path("centraldefilamentos/data/grilon3_image_selections.json")
DEFAULT_ASSETS_DIR = Path("public/assets/grilon3")
VALID_REASONS = {"preferred_angle", "best_spool", "official_primary"}
SELECTIONS_VERSION = 1


def build_apply_plan(
    scan: object,
    reviews: object,
    existing_selections: object,
    existing_metadata: object,
) -> dict[str, object]:
    scan_data = _mapping(scan, "scan")
    if scan_data.get("complete") is not True:
        raise ValueError("No se puede aplicar un scan incompleto de Grilon3")
    products = scan_data.get("products")
    if not isinstance(products, list):
        raise ValueError("El scan debe contener una lista products")
    review_data = _mapping(reviews, "revisiones")
    current_metadata = _metadata_mapping(existing_metadata)
    current_selections = _selection_records(existing_selections)

    proposed_metadata: dict[str, dict[str, str]] = {}
    proposed_selections: dict[str, dict[str, str]] = {}
    asset_changes: list[dict[str, str]] = []
    seen_urls: set[str] = set()
    seen_product_ids: set[str] = set()

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
        gallery = _gallery(product.get("gallery_image_urls"))

        metadata = dict(current_metadata.get(product_id, {}))
        metadata.update({
            "manufacturer_product_url": product_url,
            "sku": _official_field(product, "sku"),
            "ean": _official_field(product, "ean"),
            "pantone": _official_field(product, "pantone"),
        })

        if gallery:
            fingerprint = _fingerprint(product.get("gallery_fingerprint"), "scan")
            raw_review = review_data.get(product_url)
            if raw_review is None:
                raise ValueError(f"revision pendiente para {product_url}")
            selected = _validated_review(product_url, gallery, fingerprint, raw_review)
            proposed_selections[product_url] = selected
            filename = grilon3_asset_filename(selected["selected_image_remote_url"])
            local_url = f"assets/grilon3/{filename}"
            metadata["image_remote_url"] = selected["selected_image_remote_url"]
            metadata["image_url"] = local_url
            previous = current_selections.get(product_url, {})
            if (
                previous.get("selected_image_remote_url") != selected["selected_image_remote_url"]
                or current_metadata.get(product_id, {}).get("image_url") != local_url
            ):
                asset_changes.append({
                    "product_url": product_url,
                    "remote_url": selected["selected_image_remote_url"],
                    "image_url": local_url,
                    "thumbnail_url": thumbnail_url_for(local_url),
                })
        else:
            metadata.pop("image_remote_url", None)
            metadata.pop("image_url", None)

        proposed_metadata[product_id] = metadata

    unknown_review_keys = set(review_data) - seen_urls
    if unknown_review_keys:
        raise ValueError(f"revision de producto desconocido: {sorted(unknown_review_keys)[0]}")

    selection_payload: dict[str, object] = {
        "version": SELECTIONS_VERSION,
        "selections": proposed_selections,
    }
    return {
        "version": 1,
        "metadata": proposed_metadata,
        "selections": selection_payload,
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
    report = {
        "mode": "apply" if apply else "dry-run",
        "metadata_changes": plan.get("metadata_changes", []),
        "selection_changes": plan.get("selection_changes", []),
        "asset_changes": plan.get("asset_changes", []),
    }
    if not apply:
        return report

    metadata = _metadata_mapping(plan.get("metadata"))
    selections = _mapping(plan.get("selections"), "selections del plan")
    if selections.get("version") != SELECTIONS_VERSION:
        raise ValueError("version invalida del manifiesto de selecciones")
    approved_selections = _selection_records(selections)
    asset_changes = plan.get("asset_changes")
    if not isinstance(asset_changes, list):
        raise ValueError("asset_changes debe ser una lista")

    metadata_target = Path(metadata_path)
    selections_target = Path(selections_path)
    production_assets = Path(assets_dir)
    public_dir = _public_dir_for_assets(production_assets)
    staging_parent = public_dir.parent if public_dir.parent.exists() else production_assets.parent
    staging = Path(tempfile.mkdtemp(prefix=".grilon3-apply-", dir=staging_parent))
    staged_public = staging / "public"
    replacements: list[tuple[Path, Path]] = []

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
    finally:
        shutil.rmtree(staging, ignore_errors=True)

    return report


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
            temp_path.replace(target)
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
    return {
        "product_url": product_url,
        "selected_image_remote_url": selected_url,
        "selection_reason": reason,
        "gallery_fingerprint": fingerprint,
        "reviewed_at": reviewed_at,
    }


def _gallery(value: object) -> list[str]:
    if not isinstance(value, list):
        raise ValueError("gallery_image_urls debe ser una lista")
    gallery = [_official_image_url(url) for url in value]
    if len(gallery) != len(set(gallery)):
        raise ValueError("La galería oficial contiene URLs duplicadas")
    return gallery


def _canonical_product_url(value: object) -> str:
    url = _required_string(value, "product_url").strip().rstrip("/") + "/"
    parsed = urlparse(url)
    if parsed.scheme != "https" or parsed.hostname not in {"grilon3.com.ar", "www.grilon3.com.ar"}:
        raise ValueError(f"URL de producto Grilon3 inválida: {url}")
    if not parsed.path.startswith("/producto/"):
        raise ValueError(f"URL de producto Grilon3 inválida: {url}")
    return url


def _official_image_url(value: object) -> str:
    url = _required_string(value, "URL de imagen")
    parsed = urlparse(url)
    if parsed.scheme != "https" or parsed.hostname not in {"grilon3.com.ar", "www.grilon3.com.ar"}:
        raise ValueError(f"URL de imagen oficial invalida: {url}")
    return url


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
        clean[str(key)] = {str(field): str(field_value) for field, field_value in data.items()}
    return clean


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
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args(argv)

    metadata_path = Path(args.metadata)
    selections_path = Path(args.selections)
    plan = build_apply_plan(
        _read_json(Path(args.scan), None),
        _read_json(Path(args.reviews), {}),
        _read_json(selections_path, {}),
        _read_json(metadata_path, {}),
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
