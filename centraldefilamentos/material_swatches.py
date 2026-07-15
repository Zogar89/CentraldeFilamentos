from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path
import random
import re
from typing import Callable, Mapping

from PIL import Image, ImageDraw

from centraldefilamentos.material_appearance import (
    MATERIAL_FINISHES,
    load_pantone_table,
    normalize_pantone_key,
    resolve_material_appearance,
)


RENDERER_VERSION = 1
SWATCH_SIZE = 160
SUPERSAMPLING = 2

FINISH_PROFILES: dict[str, dict[str, float]] = {
    "matte": {"roughness": 0.90, "metallic": 0.00, "clearcoat": 0.00},
    "satin": {"roughness": 0.55, "metallic": 0.00, "clearcoat": 0.10},
    "gloss": {"roughness": 0.22, "metallic": 0.00, "clearcoat": 0.55},
    "silk": {"roughness": 0.32, "metallic": 0.15, "clearcoat": 0.35},
    "metallic": {"roughness": 0.28, "metallic": 0.55, "clearcoat": 0.25},
    "pearl": {"roughness": 0.38, "metallic": 0.12, "clearcoat": 0.42},
    "glitter": {"roughness": 0.36, "metallic": 0.30, "clearcoat": 0.30},
    "translucent": {"roughness": 0.18, "metallic": 0.00, "clearcoat": 0.70},
    "fluorescent": {"roughness": 0.48, "metallic": 0.00, "clearcoat": 0.12},
    "wood": {"roughness": 0.82, "metallic": 0.00, "clearcoat": 0.02},
}


def _normalize(vector: tuple[float, float, float]) -> tuple[float, float, float]:
    length = math.sqrt(sum(component * component for component in vector))
    return tuple(component / length for component in vector)  # type: ignore[return-value]


def _dot(left: tuple[float, float, float], right: tuple[float, float, float]) -> float:
    return sum(a * b for a, b in zip(left, right))


def _mix(left: float, right: float, amount: float) -> float:
    return left * (1.0 - amount) + right * amount


def _clamp(value: float, minimum: float = 0.0, maximum: float = 1.0) -> float:
    return max(minimum, min(maximum, value))


def _srgb_to_linear(value: int) -> float:
    channel = value / 255.0
    return channel / 12.92 if channel <= 0.04045 else ((channel + 0.055) / 1.055) ** 2.4


def _linear_to_srgb(value: float) -> int:
    channel = _clamp(value)
    encoded = 12.92 * channel if channel <= 0.0031308 else 1.055 * (channel ** (1 / 2.4)) - 0.055
    return round(_clamp(encoded) * 255)


def _hex_to_linear(hex_color: str) -> tuple[float, float, float]:
    match = re.fullmatch(r"#?([0-9A-Fa-f]{6})", hex_color.strip())
    if not match:
        raise ValueError(f"Invalid RGB hex color: {hex_color}")
    value = match.group(1)
    return tuple(_srgb_to_linear(int(value[index : index + 2], 16)) for index in (0, 2, 4))  # type: ignore[return-value]


def material_swatch_url(pantone: str, finish: str) -> str:
    table = load_pantone_table()
    canonical = normalize_pantone_key(pantone, table.aliases) or str(pantone).strip().upper()
    slug = re.sub(r"[^a-z0-9]+", "-", canonical.lower()).strip("-")
    finish_slug = re.sub(r"[^a-z0-9]+", "-", finish.lower()).strip("-")
    return f"assets/material-swatches/pantone-{slug}-{finish_slug}-v{RENDERER_VERSION}.webp"


def estimated_material_swatch_url(product_id: str, finish: str) -> str:
    product_slug = re.sub(r"[^a-z0-9]+", "-", product_id.lower()).strip("-")
    finish_slug = re.sub(r"[^a-z0-9]+", "-", finish.lower()).strip("-")
    return f"assets/material-swatches/estimated-{product_slug}-{finish_slug}-v{RENDERER_VERSION}.webp"


def _finish_adjustment(
    finish: str,
    *,
    x: int,
    y: int,
    radius: float,
    angle: float,
    seed: int,
) -> tuple[float, tuple[float, float, float], float]:
    noise = random.Random(seed ^ (x * 73856093) ^ (y * 19349663)).random()
    multiplier = 1.0
    tint = (0.0, 0.0, 0.0)
    sparkle = 0.0
    if finish == "matte":
        multiplier = 0.965 + noise * 0.055
    elif finish == "silk":
        multiplier = 0.92 + 0.18 * (0.5 + 0.5 * math.cos(angle * 2.0 - 0.8))
        sparkle = max(0.0, math.cos(angle + 2.3)) ** 18 * 0.16
    elif finish == "metallic":
        multiplier = 0.88 + noise * 0.24
        sparkle = max(0.0, noise - 0.84) * 0.55
    elif finish == "pearl":
        tint = (0.035, 0.018, 0.055)
        sparkle = max(0.0, math.cos(angle + 2.15)) ** 10 * 0.22
    elif finish == "glitter":
        multiplier = 0.90 + noise * 0.20
        sparkle = 0.85 if noise > 0.992 else 0.0
    elif finish == "translucent":
        multiplier = 0.82 + 0.30 * radius
        tint = (0.025, 0.035, 0.045)
    elif finish == "fluorescent":
        multiplier = 1.15
        tint = (0.045, 0.045, 0.015)
    elif finish == "wood":
        grain = math.sin(radius * 82.0 + math.sin(angle * 3.0) * 1.8)
        multiplier = 0.91 + grain * 0.055 + (noise - 0.5) * 0.025
    return multiplier, tint, sparkle


def _shade_cone(hex_color: str, finish: str, size: int) -> Image.Image:
    profile = FINISH_PROFILES[finish]
    base = _hex_to_linear(hex_color)
    roughness = profile["roughness"]
    metallic = profile["metallic"]
    clearcoat = profile["clearcoat"]
    light = _normalize((-0.55, -0.55, 0.63))
    view = (0.0, 0.0, 1.0)
    halfway = _normalize(tuple(light[index] + view[index] for index in range(3)))  # type: ignore[arg-type]
    center = (size - 1) / 2.0
    cone_radius = size * 0.75
    seed = int.from_bytes(
        hashlib.sha256(f"{hex_color.upper()}:{finish}:v{RENDERER_VERSION}".encode()).digest()[:8],
        "big",
    )
    image = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    pixels = image.load()

    for y in range(size):
        dy = (y - center) / cone_radius
        for x in range(size):
            dx = (x - center) / cone_radius
            radius = math.sqrt(dx * dx + dy * dy)
            angle = math.atan2(dy, dx)
            radial_x = dx / radius if radius > 1e-6 else 0.0
            radial_y = dy / radius if radius > 1e-6 else 0.0
            inclination = 0.78 * (1.0 - math.exp(-radius * 35.0))
            normal = _normalize((radial_x * inclination, radial_y * inclination, 0.72))
            n_dot_l = max(0.0, _dot(normal, light))
            n_dot_v = max(0.001, _dot(normal, view))
            n_dot_h = max(0.0, _dot(normal, halfway))
            v_dot_h = max(0.0, _dot(view, halfway))

            alpha = max(0.035, roughness * roughness)
            alpha_squared = alpha * alpha
            denominator = n_dot_h * n_dot_h * (alpha_squared - 1.0) + 1.0
            distribution = alpha_squared / max(math.pi * denominator * denominator, 1e-5)
            geometry_k = ((roughness + 1.0) ** 2) / 8.0
            geometry_v = n_dot_v / (n_dot_v * (1.0 - geometry_k) + geometry_k)
            geometry_l = n_dot_l / (n_dot_l * (1.0 - geometry_k) + geometry_k)
            geometry = geometry_v * geometry_l

            multiplier, tint, sparkle = _finish_adjustment(
                finish,
                x=x,
                y=y,
                radius=radius,
                angle=angle,
                seed=seed,
            )
            channels: list[int] = []
            for index, base_channel in enumerate(base):
                f0 = _mix(0.04, base_channel, metallic)
                fresnel = f0 + (1.0 - f0) * ((1.0 - v_dot_h) ** 5)
                specular = distribution * geometry * fresnel / max(4.0 * n_dot_l * n_dot_v, 0.01)
                diffuse = base_channel * (1.0 - metallic) * (0.18 + n_dot_l * 0.92)
                coat = clearcoat * (n_dot_h ** max(6.0, 42.0 * (1.0 - roughness))) * 0.48
                ambient = base_channel * (0.13 + 0.08 * (1.0 - radius))
                value = (diffuse + ambient + specular * 0.55 + coat + tint[index] + sparkle) * multiplier
                channels.append(_linear_to_srgb(value))
            pixels[x, y] = (*channels, 255)
    return image


def _rounded_mask(size: int) -> Image.Image:
    mask = Image.new("L", (size, size), 0)
    ImageDraw.Draw(mask).rounded_rectangle(
        (0, 0, size - 1, size - 1),
        radius=round(size * 0.22),
        fill=255,
    )
    return mask


def render_material_swatch(hex_color: str, finish: str, output_path: Path) -> None:
    if finish not in FINISH_PROFILES:
        raise ValueError(f"Unknown material finish: {finish}")
    render_size = SWATCH_SIZE * SUPERSAMPLING
    image = _shade_cone(hex_color, finish, render_size)
    image.putalpha(_rounded_mask(render_size))
    image = image.resize((SWATCH_SIZE, SWATCH_SIZE), Image.Resampling.LANCZOS)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    image.save(output_path, "WEBP", lossless=True, quality=100, method=6, exact=True)


def _write_json_if_changed(path: Path, payload: Mapping[str, object]) -> None:
    serialized = json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    if path.exists() and path.read_text(encoding="utf-8") == serialized:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(serialized, encoding="utf-8")


def _offer_names(product: Mapping[str, object]) -> list[str]:
    offers = product.get("offers", [])
    if not isinstance(offers, list):
        return []
    return [
        str(offer.get("original_name", ""))
        for offer in offers
        if isinstance(offer, Mapping)
    ]


def apply_material_swatches_to_stock(
    stock_json: Path,
    public_dir: Path,
    progress: Callable[[int, int], None] | None = None,
) -> int:
    payload = json.loads(stock_json.read_text(encoding="utf-8"))
    products = payload.get("products", [])
    product_rows = [product for product in products if isinstance(product, dict)] if isinstance(products, list) else []
    estimated_total = sum(
        1
        for product in product_rows
        if not resolve_material_appearance(
            product_id=str(product.get("id", "")),
            pantone=str(product.get("pantone", "")),
            variant=str(product.get("variant", "")),
            color=str(product.get("color", "")),
            original_names=_offer_names(product),
        ).pantone_hex
        and bool(product.get("estimated_color_hex"))
    )
    estimated_completed = 0
    generated = 0
    for product in product_rows:
        appearance = resolve_material_appearance(
            product_id=str(product.get("id", "")),
            pantone=str(product.get("pantone", "")),
            variant=str(product.get("variant", "")),
            color=str(product.get("color", "")),
            original_names=_offer_names(product),
        )
        pantone_hex = appearance.pantone_hex
        finish = appearance.finish
        product["pantone_hex"] = pantone_hex
        product["material_finish"] = finish
        if pantone_hex and finish in MATERIAL_FINISHES:
            url = material_swatch_url(str(product.get("pantone", "")), finish)
            output_path = public_dir / url
            if not output_path.exists():
                render_material_swatch(pantone_hex, finish, output_path)
                generated += 1
            product["material_swatch_url"] = url
            continue

        estimated_hex = str(product.get("estimated_color_hex", ""))
        if not estimated_hex or finish not in MATERIAL_FINISHES:
            product["material_swatch_url"] = ""
            continue

        url = estimated_material_swatch_url(str(product.get("id", "")), finish)
        output_path = public_dir / url
        temporary_path = output_path.with_suffix(".tmp.webp")
        render_material_swatch(estimated_hex, finish, temporary_path)
        if not output_path.exists() or output_path.read_bytes() != temporary_path.read_bytes():
            temporary_path.replace(output_path)
            generated += 1
        else:
            temporary_path.unlink()
        product["material_swatch_url"] = url
        estimated_completed += 1
        if progress:
            progress(estimated_completed, estimated_total)
    _write_json_if_changed(stock_json, payload)
    return generated
