from copy import deepcopy
from dataclasses import replace

import pytest

from centraldefilamentos.build_data import build_payload
from centraldefilamentos.models import RawStockItem
from centraldefilamentos.providers import SOURCES
from centraldefilamentos.source_freshness import apply_source_freshness, stock_signature

FIRST_CAPTURE = "2026-10-20T12:00:00-03:00"
NEXT_CAPTURE = "2026-10-27T12:00:00-03:00"


def item(color: str, quantity: int | None, source_id: str = "mundoinsumos") -> RawStockItem:
    source = SOURCES[source_id]
    return RawStockItem(
        source_id=source.id,
        provider_name=source.name,
        provider_zone=source.zone,
        provider_url=source.homepage_url,
        original_name=f"GRILON3 PLA {color} 1.75 MM X 1 KG",
        stock_quantity=quantity,
        source_url=source.source_url,
        updated_at=FIRST_CAPTURE,
    )


def capture(items, generated_at=FIRST_CAPTURE, previous=None, **options):
    payload = build_payload(items, generated_at=generated_at, **options)
    apply_source_freshness(payload, items, previous)
    return payload


def source_state(payload, source_id="mundoinsumos"):
    return next(source for source in payload["sources"] if source["id"] == source_id)


@pytest.mark.parametrize("legacy_payload", [False, True])
def test_first_observation_starts_now_without_inventing_historical_changes(legacy_payload):
    items = [item("Negro", 3)]
    legacy = build_payload(items, generated_at="2026-09-01T12:00:00-03:00")
    assert source_state(legacy)["stock_signature"] == ""
    assert source_state(legacy)["stock_unchanged_since"] == ""
    for source in legacy["sources"]:
        source.pop("stock_signature")
        source.pop("stock_unchanged_since")

    current = capture(items, previous=legacy if legacy_payload else None)

    state = source_state(current)
    assert len(state["stock_signature"]) == 64
    assert state["stock_unchanged_since"] == FIRST_CAPTURE
    assert state["last_success_at"] == FIRST_CAPTURE


def test_identical_stock_keeps_baseline_despite_reordering_time_and_metadata_changes():
    items = [item("Negro", 3), item("Blanco", 0), item("Rojo", None)]
    previous = capture(items)
    previous_copy = deepcopy(previous)
    reordered = [
        replace(
            raw,
            updated_at=NEXT_CAPTURE,
            provider_name="Nombre actualizado",
            provider_zone="Zona nueva",
            provider_url="https://example.com/",
            source_url="https://example.com/raw-metadata",
            brand_hint="Grilon3",
        )
        for raw in reversed(items)
    ]

    current = capture(
        reordered,
        NEXT_CAPTURE,
        previous,
        enrichments={"pla-negro-175-1000-grilon3": {"image_url": "assets/changed-photo.jpg"}},
    )

    state = source_state(current)
    assert state["stock_signature"] == source_state(previous)["stock_signature"]
    assert state["stock_unchanged_since"] == FIRST_CAPTURE
    assert state["last_success_at"] == NEXT_CAPTURE
    assert state["last_attempt_at"] == NEXT_CAPTURE
    assert previous == previous_copy


@pytest.mark.parametrize(
    "changed_items",
    [
        [item("Negro", 5), item("Blanco", 5)],
        [item("Negro", 4), item("Blanco", 6), item("Rojo", 0)],
        [item("Negro", 4)],
        [item("Azul", 4), item("Blanco", 6)],
        [item("Negro", 4), item("Blanco", 6), item("Negro", 4)],
    ],
    ids=["redistributed-same-total", "added-zero-stock-row", "removed-row", "renamed-row", "repeated-row"],
)
def test_inventory_changes_restart_observed_baseline(changed_items):
    previous = capture([item("Negro", 4), item("Blanco", 6)])

    current = capture(changed_items, NEXT_CAPTURE, previous)

    assert source_state(current)["stock_signature"] != source_state(previous)["stock_signature"]
    assert source_state(current)["stock_unchanged_since"] == NEXT_CAPTURE


def test_unknown_stock_and_zero_are_distinct_even_for_identical_names():
    unknown = item("Negro", None)
    zero = item("Negro", 0)
    assert stock_signature([unknown]) != stock_signature([zero])
    assert stock_signature([unknown, zero]) == stock_signature([zero, unknown])

    previous = capture([unknown])
    current = capture([zero], NEXT_CAPTURE, previous)

    assert source_state(current)["stock_unchanged_since"] == NEXT_CAPTURE


def test_source_url_change_restarts_baseline_with_same_inventory_signature():
    items = [item("Negro", 3)]
    previous = capture(items)
    new_source = replace(SOURCES["mundoinsumos"], source_url="https://example.com/new-source")

    current = capture(items, NEXT_CAPTURE, previous, sources={new_source.id: new_source})

    assert source_state(current)["stock_signature"] == source_state(previous)["stock_signature"]
    assert source_state(current)["stock_unchanged_since"] == NEXT_CAPTURE


def test_each_source_tracks_its_own_inventory_independently():
    items = [item("Negro", 3, source_id) for source_id in SOURCES]
    previous = capture(items)
    changed = [replace(raw, stock_quantity=7) if raw.source_id == "grupo_senz" else raw for raw in items]

    current = capture(changed, NEXT_CAPTURE, previous)

    for source_id in SOURCES:
        state = source_state(current, source_id)
        assert state["stock_unchanged_since"] == (NEXT_CAPTURE if source_id == "grupo_senz" else FIRST_CAPTURE)
        assert state["last_success_at"] == NEXT_CAPTURE


@pytest.mark.parametrize("has_previous", [False, True])
def test_failed_reads_preserve_previous_observation_without_using_partial_stock(has_previous):
    previous = capture([item("Negro", 3)]) if has_previous else None
    previous_copy = deepcopy(previous)

    current = capture(
        [item("Blanco", 9)],
        NEXT_CAPTURE,
        previous,
        source_errors={"mundoinsumos": "CSV export failed"},
    )

    state = source_state(current)
    expected = source_state(previous) if previous else {}
    for field in ("stock_signature", "stock_unchanged_since", "last_success_at"):
        assert state[field] == expected.get(field, "")
    assert state["status"] == "error"
    assert state["last_attempt_at"] == NEXT_CAPTURE
    assert previous == previous_copy


@pytest.mark.parametrize("invalid_time", ["not-a-date", "2026-11-01T12:00:00-03:00", "2026-10-20T12:00:00"])
def test_invalid_future_or_timezone_unknown_previous_dates_do_not_claim_known_age(invalid_time):
    items = [item("Negro", 3)]
    previous = capture(items)
    source_state(previous)["stock_unchanged_since"] = invalid_time
    source_state(previous)["last_success_at"] = invalid_time

    successful = capture(items, NEXT_CAPTURE, previous)
    failed = capture([], NEXT_CAPTURE, previous, source_errors={"mundoinsumos": "CSV export failed"})

    assert source_state(successful)["stock_unchanged_since"] == NEXT_CAPTURE
    assert source_state(successful)["last_success_at"] == NEXT_CAPTURE
    assert source_state(failed)["stock_unchanged_since"] == ""
    assert source_state(failed)["last_success_at"] == ""


def test_equivalent_timezones_preserve_an_existing_valid_baseline():
    items = [item("Negro", 3)]
    previous = capture(items)
    source_state(previous)["stock_unchanged_since"] = "2026-10-20T15:00:00Z"

    current = capture(items, NEXT_CAPTURE, previous)

    assert source_state(current)["stock_unchanged_since"] == "2026-10-20T15:00:00Z"
