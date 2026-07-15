from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
import re
from typing import Literal, Mapping, cast

from centraldefilamentos.material_appearance import MATERIAL_FINISHES, MaterialFinish


ConfidenceBand = Literal["high", "medium", "low"]
EstimateSource = Literal["image_and_name", "name_only"]

COLOR_ESTIMATES_PATH = Path(__file__).resolve().parent / "data" / "color_estimates.json"
CONFIDENCE_INTERVALS: dict[ConfidenceBand, tuple[float, float]] = {
    "high": (0.8, 1.0),
    "medium": (0.5, 0.79),
    "low": (0.2, 0.49),
}
HEX_PATTERN = re.compile(r"^#[0-9A-F]{6}$")


@dataclass(frozen=True)
class ColorEstimate:
    estimated_hex: str
    confidence_band: ConfidenceBand
    confidence_interval: tuple[float, float]
    source: EstimateSource
    material_finish: MaterialFinish
    evidence: str
    warning: str


def _parse_record(product_id: str, payload: object) -> ColorEstimate:
    if not isinstance(payload, dict):
        raise ValueError(f"{product_id}: estimate must be an object")

    estimated_hex = str(payload.get("estimated_hex", ""))
    if not HEX_PATTERN.fullmatch(estimated_hex):
        raise ValueError(f"{product_id}: estimated_hex must use uppercase #RRGGBB")

    confidence_band = str(payload.get("confidence_band", ""))
    if confidence_band not in CONFIDENCE_INTERVALS:
        raise ValueError(f"{product_id}: invalid confidence_band")
    band = cast(ConfidenceBand, confidence_band)

    interval_payload = payload.get("confidence_interval")
    if not isinstance(interval_payload, list) or len(interval_payload) != 2:
        raise ValueError(f"{product_id}: invalid confidence_interval")
    confidence_interval = (float(interval_payload[0]), float(interval_payload[1]))
    if confidence_interval != CONFIDENCE_INTERVALS[band]:
        raise ValueError(f"{product_id}: confidence_interval does not match confidence_band")

    source = str(payload.get("source", ""))
    if source not in {"image_and_name", "name_only"}:
        raise ValueError(f"{product_id}: invalid source")
    if source == "name_only" and band != "low":
        raise ValueError(f"{product_id}: name_only estimates must have low confidence")

    material_finish = str(payload.get("material_finish", ""))
    if material_finish not in MATERIAL_FINISHES:
        raise ValueError(f"{product_id}: invalid material_finish")

    evidence = str(payload.get("evidence", "")).strip()
    if not evidence:
        raise ValueError(f"{product_id}: evidence is required")
    warning = str(payload.get("warning", "")).strip()
    if not warning:
        raise ValueError(f"{product_id}: warning is required")

    return ColorEstimate(
        estimated_hex=estimated_hex,
        confidence_band=band,
        confidence_interval=confidence_interval,
        source=cast(EstimateSource, source),
        material_finish=cast(MaterialFinish, material_finish),
        evidence=evidence,
        warning=warning,
    )


def load_color_estimates(path: Path = COLOR_ESTIMATES_PATH) -> dict[str, ColorEstimate]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("color estimates must be a JSON object")
    return {str(product_id): _parse_record(str(product_id), record) for product_id, record in payload.items()}


def resolve_color_estimate(
    *,
    product_id: str,
    pantone_hex: str,
    image_url: str,
    material_finish: str,
    estimates: Mapping[str, ColorEstimate],
    public_dir: Path = Path("public"),
) -> ColorEstimate | None:
    if pantone_hex:
        return None
    estimate = estimates.get(product_id)
    if estimate is None:
        return None
    if estimate.material_finish != material_finish:
        raise ValueError(f"{product_id}: material_finish does not match product")
    if estimate.source == "image_and_name":
        image_path = public_dir / image_url.lstrip("/")
        if not image_url or not image_path.is_file():
            raise ValueError(f"{product_id}: image_and_name requires a local image")
    return estimate


def estimate_public_fields(estimate: ColorEstimate) -> dict[str, object]:
    return {
        "estimated_color_hex": estimate.estimated_hex,
        "estimated_color_confidence_band": estimate.confidence_band,
        "estimated_color_confidence_interval": list(estimate.confidence_interval),
        "estimated_color_source": estimate.source,
        "estimated_color_warning": estimate.warning,
    }


def apply_color_estimates_to_stock(
    stock_json: Path,
    estimates: Mapping[str, ColorEstimate],
    public_dir: Path = Path("public"),
) -> int:
    payload = json.loads(stock_json.read_text(encoding="utf-8"))
    applied = 0
    for product in payload.get("products", []):
        for key in tuple(product):
            if key.startswith("estimated_color_"):
                product.pop(key)
        estimate = resolve_color_estimate(
            product_id=str(product.get("id", "")),
            pantone_hex=str(product.get("pantone_hex", "")),
            image_url=str(product.get("image_url", "")),
            material_finish=str(product.get("material_finish", "")),
            estimates=estimates,
            public_dir=public_dir,
        )
        if estimate is None:
            continue
        product.update(estimate_public_fields(estimate))
        applied += 1

    serialized = json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    if stock_json.read_text(encoding="utf-8") != serialized:
        stock_json.write_text(serialized, encoding="utf-8")
    return applied
