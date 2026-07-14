from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
import json
from pathlib import Path
import re
from typing import Iterable, Literal, Mapping, cast
import unicodedata


MaterialFinish = Literal[
    "matte",
    "satin",
    "gloss",
    "silk",
    "metallic",
    "pearl",
    "glitter",
    "translucent",
    "fluorescent",
    "wood",
]

MATERIAL_FINISHES = frozenset(
    {
        "matte",
        "satin",
        "gloss",
        "silk",
        "metallic",
        "pearl",
        "glitter",
        "translucent",
        "fluorescent",
        "wood",
    }
)
DATA_DIR = Path(__file__).resolve().parent / "data"
PANTONE_TABLE_PATH = DATA_DIR / "pantone_srgb.json"
FINISH_OVERRIDES_PATH = DATA_DIR / "material_finish_overrides.json"

NAMED_PANTONE_PATTERN = re.compile(
    r"^(?:BLACK|YELLOW|VIOLET|REFLEX BLUE|ORANGE 021|COOL GRAY \d+)(?:\s*([CU]))?$"
)
NUMERIC_PANTONE_PATTERN = re.compile(r"^(\d{2,4})(?:\s*([CU]))?$")

VARIANT_RULES: tuple[tuple[tuple[str, ...], MaterialFinish], ...] = (
    (("transluc", "cristal"), "translucent"),
    (("fluor", "neon", "uv glow"), "fluorescent"),
    (("glitter", "brillantina"), "glitter"),
    (("metal",), "metallic"),
    (("silk", "seda", "astra"), "silk"),
    (("perla", "pearl"), "pearl"),
    (("madera", "wood"), "wood"),
    (("gloss", "brillante"), "gloss"),
    (("mate", "matte", "opaco"), "matte"),
)


@dataclass(frozen=True)
class PantoneTable:
    aliases: dict[str, str]
    colors: dict[str, str]
    source_name: str


@dataclass(frozen=True)
class MaterialAppearance:
    pantone_key: str
    pantone_hex: str
    finish: MaterialFinish
    pantone_source: str
    finish_source: str


def _plain_text(value: object) -> str:
    normalized = unicodedata.normalize("NFKD", str(value or ""))
    return "".join(character for character in normalized if not unicodedata.combining(character)).lower()


@lru_cache(maxsize=1)
def load_pantone_table(path: Path = PANTONE_TABLE_PATH) -> PantoneTable:
    payload = json.loads(path.read_text(encoding="utf-8"))
    source = payload.get("source", {})
    return PantoneTable(
        aliases={str(key).upper(): str(value).upper() for key, value in payload["aliases"].items()},
        colors={str(key).upper(): str(value).upper() for key, value in payload["colors"].items()},
        source_name=str(source.get("name", "")),
    )


@lru_cache(maxsize=1)
def load_finish_overrides(path: Path = FINISH_OVERRIDES_PATH) -> dict[str, MaterialFinish]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    return {
        str(product_id): cast(MaterialFinish, finish)
        for product_id, finish in payload.items()
        if str(finish) in MATERIAL_FINISHES
    }


def normalize_pantone_key(pantone: object, aliases: Mapping[str, str]) -> str:
    value = re.sub(r"\s+", " ", str(pantone or "").strip().upper())
    value = re.sub(r"^PANTONE\s+", "", value)
    if not value:
        return ""
    if value in aliases:
        return aliases[value]

    numeric_match = NUMERIC_PANTONE_PATTERN.fullmatch(value)
    if numeric_match:
        return f"{numeric_match.group(1)} {numeric_match.group(2) or 'C'}"

    named_match = NAMED_PANTONE_PATTERN.fullmatch(value)
    if named_match:
        suffix = named_match.group(1) or "C"
        name = re.sub(r"\s*[CU]$", "", value).strip()
        return f"{name} {suffix}"
    return ""


def _finish_from_text(value: str) -> MaterialFinish | None:
    plain_value = _plain_text(value)
    for keywords, finish in VARIANT_RULES:
        if any(keyword in plain_value for keyword in keywords):
            return finish
    return None


def resolve_material_finish(
    *,
    product_id: str,
    variant: str,
    color: str,
    original_names: Iterable[str],
    overrides: Mapping[str, str] | None = None,
) -> tuple[MaterialFinish, str]:
    resolved_overrides = overrides if overrides is not None else load_finish_overrides()
    override = str(resolved_overrides.get(product_id, ""))
    if override in MATERIAL_FINISHES:
        return cast(MaterialFinish, override), "override"

    variant_finish = _finish_from_text(variant)
    if variant_finish:
        return variant_finish, "variant"

    keyword_finish = _finish_from_text(" ".join([color, *original_names]))
    if keyword_finish:
        return keyword_finish, "keyword"
    return "satin", "default"


def resolve_material_appearance(
    *,
    product_id: str,
    pantone: str,
    variant: str,
    color: str,
    original_names: Iterable[str],
    overrides: Mapping[str, str] | None = None,
) -> MaterialAppearance:
    table = load_pantone_table()
    pantone_key = normalize_pantone_key(pantone, table.aliases)
    pantone_hex = table.colors.get(pantone_key, "")
    finish, finish_source = resolve_material_finish(
        product_id=product_id,
        variant=variant,
        color=color,
        original_names=original_names,
        overrides=overrides,
    )
    return MaterialAppearance(
        pantone_key=pantone_key,
        pantone_hex=pantone_hex,
        finish=finish,
        pantone_source=table.source_name if pantone_hex else "",
        finish_source=finish_source,
    )
