from centraldefilamentos.material_appearance import (
    load_pantone_table,
    normalize_pantone_key,
    resolve_material_appearance,
    resolve_material_finish,
)


def test_missing_suffix_defaults_to_solid_coated() -> None:
    table = load_pantone_table()

    assert normalize_pantone_key("179", table.aliases) == "179 C"
    assert normalize_pantone_key("Pantone 179C", table.aliases) == "179 C"
    assert normalize_pantone_key("179 U", table.aliases) == "179 U"


def test_named_pantones_are_normalized_but_unknown_material_names_are_not() -> None:
    table = load_pantone_table()

    assert normalize_pantone_key("Pantone Cool Gray 9", table.aliases) == "COOL GRAY 9 C"
    assert normalize_pantone_key("Pantone Orange 021", table.aliases) == "ORANGE 021 C"
    assert normalize_pantone_key("Pantone Perla", table.aliases) == ""


def test_finish_resolution_priority() -> None:
    assert resolve_material_finish(
        product_id="pla-cobre",
        variant="Silk",
        color="Cobre",
        original_names=["PLA metalizado cobre"],
        overrides={"pla-cobre": "matte"},
    ) == ("matte", "override")
    assert resolve_material_finish(
        product_id="pla-silk",
        variant="Silk",
        color="Oro",
        original_names=[],
        overrides={},
    ) == ("silk", "variant")
    assert resolve_material_finish(
        product_id="pla-translucido",
        variant="",
        color="Azul",
        original_names=["PLA azul translúcido"],
        overrides={},
    ) == ("translucent", "keyword")
    assert resolve_material_finish(
        product_id="pla-basic",
        variant="",
        color="Azul",
        original_names=[],
        overrides={},
    ) == ("satin", "default")


def test_material_appearance_combines_color_and_finish_provenance() -> None:
    appearance = resolve_material_appearance(
        product_id="pla-rojo",
        pantone="Pantone 179",
        variant="",
        color="Rojo",
        original_names=[],
        overrides={},
    )

    assert appearance.pantone_key == "179 C"
    assert appearance.pantone_hex == "#E03C31"
    assert appearance.finish == "satin"
    assert appearance.pantone_source == "pborman/colors pantone v1.1.0"
    assert appearance.finish_source == "default"
