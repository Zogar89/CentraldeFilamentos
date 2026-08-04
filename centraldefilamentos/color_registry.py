from __future__ import annotations

import json
import re
import unicodedata
from dataclasses import dataclass, field, replace
from datetime import datetime
from pathlib import Path
from typing import Literal, Mapping

from centraldefilamentos.models import NormalizedFields, RawStockItem

COLOR_OPTIONAL_MATERIALS = frozenset({"PVA"})
REGISTRY_VERSION = 1
MAX_EXAMPLES = 5
ColorReviewStatus = Literal["", "provisional"]
CandidateStatus = Literal["provisional", "approved"]


@dataclass(frozen=True)
class ColorCandidate:
    display_color: str
    status: CandidateStatus
    source_id: str
    brand: str
    variant: str
    first_seen_at: str
    last_seen_at: str
    examples: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "display_color": self.display_color,
            "status": self.status,
            "source_id": self.source_id,
            "brand": self.brand,
            "variant": self.variant,
            "first_seen_at": self.first_seen_at,
            "last_seen_at": self.last_seen_at,
            "examples": list(self.examples),
        }


@dataclass(frozen=True)
class ColorResolution:
    key: str
    display_color: str
    review_status: ColorReviewStatus


@dataclass
class ColorRegistry:
    candidates: dict[str, ColorCandidate]
    observed_provisional_keys: set[str] = field(default_factory=set)

    @classmethod
    def empty(cls) -> ColorRegistry:
        return cls(candidates={})


def load_color_registry(path: str | Path) -> ColorRegistry:
    registry_path = Path(path)
    if not registry_path.exists():
        return ColorRegistry.empty()

    try:
        payload = json.loads(registry_path.read_text(encoding="utf-8"), object_pairs_hook=_unique_object)
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        raise ValueError(f"Invalid color registry at {registry_path}: {exc}") from exc

    if not isinstance(payload, Mapping):
        raise ValueError(f"Invalid color registry at {registry_path}: root must be an object")
    if payload.get("version") != REGISTRY_VERSION:
        raise ValueError(f"Invalid color registry at {registry_path}: version must be {REGISTRY_VERSION}")

    candidates_payload = payload.get("candidates")
    if not isinstance(candidates_payload, Mapping):
        raise ValueError(f"Invalid color registry at {registry_path}: candidates must be an object")

    candidates: dict[str, ColorCandidate] = {}
    for key, candidate_payload in candidates_payload.items():
        candidate_key = _required_string(key, "candidate key")
        candidates[candidate_key] = _candidate_from_payload(candidate_key, candidate_payload)
    return ColorRegistry(candidates=candidates)


def write_color_registry(registry: ColorRegistry, path: str | Path) -> None:
    payload = {
        "version": REGISTRY_VERSION,
        "candidates": {
            key: registry.candidates[key].to_dict()
            for key in sorted(registry.candidates)
        },
    }
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def resolve_provisional_color(
    item: RawStockItem,
    fields: NormalizedFields,
    registry: ColorRegistry,
    observed_at: str,
) -> ColorResolution | None:
    if fields.color != "Sin color" or fields.material in COLOR_OPTIONAL_MATERIALS:
        return None

    _validate_timestamp(observed_at, "observed_at")
    source_id = _provenance_value(item.source_id, "Sin fuente")
    brand = _provenance_value(fields.brand or item.brand_hint, "Sin marca")
    variant = _provenance_value(fields.variant or fields.material, "Sin variante")
    candidate_phrase = _candidate_phrase(item.original_name, fields)
    display_color = _display_color(candidate_phrase, item.original_name)
    key = _candidate_key(source_id, brand, variant, candidate_phrase, item.original_name)
    example = item.original_name.strip() or "Sin titulo del proveedor"
    candidate = registry.candidates.get(key)

    if candidate is None:
        candidate = ColorCandidate(
            display_color=display_color,
            status="provisional",
            source_id=source_id,
            brand=brand,
            variant=variant,
            first_seen_at=observed_at,
            last_seen_at=observed_at,
            examples=(example,),
        )
    else:
        candidate = replace(
            candidate,
            last_seen_at=observed_at,
            examples=_append_example(candidate.examples, example),
        )
    registry.candidates[key] = candidate

    if candidate.status == "provisional":
        registry.observed_provisional_keys.add(key)
        return ColorResolution(key=key, display_color=candidate.display_color, review_status="provisional")
    return ColorResolution(key=key, display_color=candidate.display_color, review_status="")


def _candidate_from_payload(key: str, payload: object) -> ColorCandidate:
    if not isinstance(payload, Mapping):
        raise ValueError(f"Invalid color registry candidate {key}: must be an object")
    _validate_candidate_key(key)
    display_color = _required_string(payload.get("display_color"), f"candidate {key} display_color")
    status = _required_string(payload.get("status"), f"candidate {key} status")
    if status not in {"provisional", "approved"}:
        raise ValueError(f"Invalid color registry candidate {key}: unsupported status {status!r}")
    source_id = _required_string(payload.get("source_id"), f"candidate {key} source_id")
    brand = _required_string(payload.get("brand"), f"candidate {key} brand")
    variant = _required_string(payload.get("variant"), f"candidate {key} variant")
    first_seen_at = _required_string(payload.get("first_seen_at"), f"candidate {key} first_seen_at")
    last_seen_at = _required_string(payload.get("last_seen_at"), f"candidate {key} last_seen_at")
    first_seen = _validate_timestamp(first_seen_at, f"candidate {key} first_seen_at")
    last_seen = _validate_timestamp(last_seen_at, f"candidate {key} last_seen_at")
    if last_seen < first_seen:
        raise ValueError(f"Invalid color registry candidate {key}: last_seen_at precedes first_seen_at")
    examples_payload = payload.get("examples")
    if not isinstance(examples_payload, list) or not examples_payload or len(examples_payload) > MAX_EXAMPLES:
        raise ValueError(f"Invalid color registry candidate {key}: examples must contain 1-{MAX_EXAMPLES} titles")
    examples = tuple(_required_string(example, f"candidate {key} example") for example in examples_payload)
    if len(set(examples)) != len(examples):
        raise ValueError(f"Invalid color registry candidate {key}: examples must be unique")
    _validate_display_color_for_key(key, display_color, examples)
    return ColorCandidate(
        display_color=display_color,
        status=status,  # type: ignore[arg-type]
        source_id=source_id,
        brand=brand,
        variant=variant,
        first_seen_at=first_seen_at,
        last_seen_at=last_seen_at,
        examples=examples,
    )


def _candidate_phrase(title: str, fields: NormalizedFields) -> str:
    ignored = {
        *_tokens(fields.material),
        *_tokens(fields.variant),
        *_tokens(fields.brand),
        "X",
        "MM",
        "KG",
        "G",
        "GR",
        "BOBINA",
        "BOB",
        "CARRETE",
        "SPOOL",
        "FILAMENTO",
        "FILAMENT",
        "BOX",
        "PACK",
    }
    words = _tokens(title)
    candidate_words = [word for word in words if word not in ignored and not word.isdigit()]
    return " ".join(candidate_words)


def _display_color(candidate_phrase: str, title: str) -> str:
    if candidate_phrase:
        return candidate_phrase.lower().title()
    source_title = title.strip()
    return f"Color del proveedor: {source_title}" if source_title else "Color del proveedor sin etiqueta"


def _candidate_key(source_id: str, brand: str, variant: str, candidate_phrase: str, title: str) -> str:
    candidate_slug = _slug(candidate_phrase)
    if not candidate_slug:
        candidate_slug = f"titulo-{_slug(title) or 'sin-etiqueta'}"
    return "|".join((_source_slug(source_id), _slug(brand), _slug(variant), candidate_slug))


def _append_example(examples: tuple[str, ...], example: str) -> tuple[str, ...]:
    if example in examples:
        return examples
    return (*examples, example)[-MAX_EXAMPLES:]


def _provenance_value(value: str, fallback: str) -> str:
    return value.strip() or fallback


def _tokens(value: str) -> list[str]:
    return re.findall(r"[A-Z0-9]+", _fold(value))


def _slug(value: str) -> str:
    return "-".join(_tokens(value)).lower()


def _source_slug(value: str) -> str:
    folded = _fold(value).lower()
    return re.sub(r"[^a-z0-9_]+", "-", folded).strip("-")


def _fold(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value)
    return "".join(char for char in normalized if not unicodedata.combining(char)).upper()


def _unique_object(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON key {key!r}")
        result[key] = value
    return result


def _required_string(value: object, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"Invalid color registry {label}: must be a non-empty string")
    return value.strip()


def _validate_candidate_key(key: str) -> None:
    parts = key.split("|")
    if (
        len(parts) != 4
        or not parts[0]
        or _source_slug(parts[0]) != parts[0]
        or any(not part or _slug(part) != part for part in parts[1:])
    ):
        raise ValueError(f"Invalid color registry candidate {key}: malformed immutable key")


def _validate_display_color_for_key(key: str, display_color: str, examples: tuple[str, ...]) -> None:
    candidate_slug = key.rsplit("|", 1)[-1]
    if candidate_slug.startswith("titulo-"):
        expected_display_color = _display_color("", examples[0])
        if display_color != expected_display_color:
            raise ValueError(f"Invalid color registry candidate {key}: display_color does not match immutable key")
        return
    if _slug(display_color) != candidate_slug:
        raise ValueError(f"Invalid color registry candidate {key}: display_color does not match immutable key")


def _validate_timestamp(value: str, label: str) -> datetime:
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError(f"Invalid color registry {label}: invalid ISO timestamp") from exc
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ValueError(f"Invalid color registry {label}: invalid ISO timestamp")
    return parsed
