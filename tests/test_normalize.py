import pytest

from centraldefilamentos.models import RawStockItem
from centraldefilamentos.normalize import build_display_name, build_product_id, normalize_record


def raw(name: str, source_id: str = "filamentos3d", brand_hint: str = "") -> RawStockItem:
    return RawStockItem(
        source_id=source_id,
        provider_name="Proveedor",
        provider_zone="Zona Sur",
        provider_url="https://example.com",
        original_name=name,
        stock_quantity=1,
        source_url="https://example.com/source",
        brand_hint=brand_hint,
        updated_at="2026-05-12T12:00:00-03:00",
    )


def test_normalizes_grilon3_pla_negro():
    fields = normalize_record(raw("GRILON3 PLA Negro 1.75mm 1kg", brand_hint="Grilon3"))

    assert fields.material == "PLA"
    assert fields.variant == ""
    assert fields.color == "Negro"
    assert fields.diameter_mm == 1.75
    assert fields.weight_g == 1000
    assert fields.brand == "Grilon3"
    assert fields.manufacturer_name == "Grilon3"


def test_normalizes_grilon3_pla_magenta_as_distinct_canonical_color():
    magenta = normalize_record(
        raw("GRILON3 PLA MAGENTA 1.75 MM X 1 KG", brand_hint="Grilon3")
    )
    fucsia = normalize_record(
        raw("GRILON3 PLA FUCSIA 1.75 MM X 1 KG", brand_hint="Grilon3")
    )
    rosa = normalize_record(
        raw("GRILON3 PLA ROSA 1.75 MM X 1 KG", brand_hint="Grilon3")
    )

    assert (
        magenta.material,
        magenta.variant,
        magenta.color,
        magenta.diameter_mm,
        magenta.weight_g,
        magenta.brand,
        magenta.subrange,
        magenta.finish,
    ) == ("PLA", "", "Magenta", 1.75, 1000, "Grilon3", "Standard", "")
    assert build_product_id(magenta) == "pla-magenta-175-1000-grilon3"
    assert {magenta.color, fucsia.color, rosa.color} == {"Magenta", "Fucsia", "Rosa"}


def test_normalizes_official_colorless_pva_without_inventing_a_color():
    fields = normalize_record(
        raw("GRILON3 PVA SOLUBLE 1.75 MM X 500 GR", brand_hint="Grilon3")
    )

    assert (
        fields.material,
        fields.variant,
        fields.color,
        fields.diameter_mm,
        fields.weight_g,
        fields.brand,
    ) == ("PVA", "PVA Soluble", "Sin color", 1.75, 500, "Grilon3")
    assert build_product_id(fields) == (
        "pva-pva-soluble-sin-color-175-500-grilon3"
    )


def test_normalizes_3n3_pla_plus_rojo():
    fields = normalize_record(raw("3N3 PLA+ Rojo 1 kg 1.75 mm", source_id="grupo_senz"))

    assert fields.material == "PLA"
    assert fields.variant == "PLA+"
    assert fields.color == "Rojo"
    assert fields.diameter_mm == 1.75
    assert fields.weight_g == 1000
    assert fields.brand == "3N3"
    assert fields.manufacturer_name == "3N3"


def test_keeps_other_weights_separate():
    fields = normalize_record(raw("PETG Transparente 750 GR 1.75mm"))

    assert fields.material == "PETG"
    assert fields.color == "Transparente"
    assert fields.weight_g == 750


def test_keeps_special_colors_separate():
    natural = normalize_record(raw("PLA Natural 1kg 1.75mm"))
    transparent = normalize_record(raw("PLA Transparente 1kg 1.75mm"))
    crystal = normalize_record(raw("PLA Cristal 1kg 1.75mm"))

    assert natural.color == "Natural"
    assert transparent.color == "Transparente"
    assert crystal.color == "Cristal"


def test_product_id_includes_brand_and_format():
    fields = normalize_record(raw("PLA Silk Azul 1kg 1.75mm Grilon3"))

    assert build_product_id(fields) == "pla-pla-silk-azul-175-1000-grilon3"


@pytest.mark.parametrize(
    ("name", "expected_subrange", "expected_finish"),
    [
        ("GRILON3 PLA NEGRO 1.75 MM X 1 KG", "Standard", ""),
        ("GRILON3 ASTRA DARK 1.75 MM X 1 KG", "Astra", "Glitter"),
        ("GRILON3 PLA SILK AZUL 1.75 MM X 1 KG", "Silk", "Brillo metálico"),
        ("GRILON3 PLA WOOD NOGAL 1.75 MM X 1 KG", "Wood", "Madera"),
        ("GRILON3 BOUTIQUE PERLA 1.75 MM X 1 KG", "Boutique", ""),
        ("GRILON3 PLA 850 NARANJA 1.75 MM X 1 KG", "PLA 850", ""),
        ("GRILON3 PLA 870 VERDE 1.75 MM X 1 KG", "PLA 870", ""),
        ("GRILON3 PLA ZETA ROBY 1.75 MM X 1 KG", "Zeta", ""),
        ("GRILON3 PETG CLEAR AZUL 1.75 MM X 1 KG", "", ""),
    ],
)
def test_classifies_explicit_pla_commercial_subranges(
    name, expected_subrange, expected_finish
):
    fields = normalize_record(raw(name, brand_hint="Grilon3"))

    assert (fields.subrange, fields.finish) == (expected_subrange, expected_finish)


def test_keeps_unmapped_pla_variant_as_subrange_without_inferred_finish():
    fields = normalize_record(raw("3N3 PLA+ ROJO 1.75 MM X 1 KG"))

    assert (fields.subrange, fields.finish) == ("PLA+", "")


@pytest.mark.parametrize(
    ("name", "expected_id"),
    [
        ("GRILON3 PLA NEGRO 1.75 MM X 1 KG", "pla-negro-175-1000-grilon3"),
        (
            "GRILON3 ASTRA DARK 1.75 MM X 1 KG",
            "pla-pla-astra-dark-175-1000-grilon3",
        ),
        (
            "GRILON3 PLA SILK AZUL 1.75 MM X 1 KG",
            "pla-pla-silk-azul-175-1000-grilon3",
        ),
        (
            "GRILON3 PLA WOOD NOGAL 1.75 MM X 1 KG",
            "pla-pla-wood-nogal-175-1000-grilon3",
        ),
        (
            "GRILON3 BOUTIQUE PERLA 1.75 MM X 1 KG",
            "pla-pla-boutique-perla-175-1000-grilon3",
        ),
        (
            "GRILON3 PLA 850 NARANJA 1.75 MM X 1 KG",
            "pla-pla-850-naranja-175-1000-grilon3",
        ),
        (
            "GRILON3 PLA 870 VERDE 1.75 MM X 1 KG",
            "pla-pla-870-verde-175-1000-grilon3",
        ),
        (
            "GRILON3 PLA ZETA ROBY 1.75 MM X 1 KG",
            "pla-pla-zeta-roby-175-1000-grilon3",
        ),
    ],
)
def test_pla_subrange_fields_do_not_change_historical_product_ids(name, expected_id):
    fields = normalize_record(raw(name, brand_hint="Grilon3"))

    assert build_product_id(fields) == expected_id


def test_normalizes_grilon3_official_lines():
    astra = normalize_record(raw("GRILON3 ASTRA DARK 1.75 MM X 1 KG", brand_hint="Grilon3"))
    boutique = normalize_record(raw("MEGAFILL GRILON3 BOUTIQUE PERLA 1.75 MM X 4 KG", brand_hint="Grilon3"))
    pp = normalize_record(raw("GRILON3 PP-T 06_AMARILLO 1.75 MM X 1 KG", brand_hint="Grilon3"))
    nylon = normalize_record(raw("GRILON3 NYLON12 AZUL 1.75 MM X 1 KG", brand_hint="Grilon3"))
    pva = normalize_record(raw("GRILON3 PVA NATURAL 1.75 MM X 500 GR", brand_hint="Grilon3"))

    assert (astra.material, astra.variant, astra.color) == ("PLA", "PLA Astra", "Dark")
    assert (boutique.material, boutique.variant, boutique.weight_g) == ("PLA", "PLA Boutique", 4000)
    assert (pp.material, pp.variant) == ("PP", "PP-T")
    assert (nylon.material, nylon.variant) == ("Nylon", "Nylon 12")
    assert (pva.material, pva.variant, pva.weight_g) == ("PVA", "PVA Soluble", 500)


def test_normalizes_epet_as_recycled_pet_and_3n_subbrands_as_3n3():
    fields = normalize_record(raw("3nEPET AZUL TRAFUL 1KG", brand_hint=""))
    flex = normalize_record(raw("3nFLEX BLANCO 500G", brand_hint="Grilon3"))
    pla_flex = normalize_record(raw("3NFLEX PLA+ 06_AMARILLO 1.75 MM X 1 KG", brand_hint=""))

    assert (fields.material, fields.variant, fields.color, fields.brand) == ("PET", "E-PET", "Azul Traful", "3N3")
    assert (flex.material, flex.variant, flex.brand) == ("TPU", "Flex", "3N3")
    assert (pla_flex.material, pla_flex.variant, pla_flex.color, pla_flex.brand) == ("PLA", "PLA Flexible", "Amarillo", "3N3")


def test_detects_compact_color_and_wide_diameters():
    compact = normalize_record(raw("3nFLEX AZUL500G", brand_hint=""))
    wide = normalize_record(raw("GRILON3 PLA NEGRO 2.85 MM X 1 KG", brand_hint="Grilon3"))
    carbon = normalize_record(raw("GRILON3 BOUTIQUE 02_CARBON.75 MM X 1 KG", brand_hint="Grilon3"))

    assert compact.color == "Azul"
    assert wide.diameter_mm == 2.85
    assert carbon.diameter_mm == 1.75


@pytest.mark.parametrize(
    ("left_name", "right_name"),
    [
        (
            "GRILON3 PLA 08_AZUL 1.75 MM X 1 KG",
            "GRILON3 PLA 23_AZUL DE PRUSIA 1.75 MM X 1 KG",
        ),
        (
            "GRILON3 PLA 91_PIEL-162 1.75 MM X 1 KG",
            "GRILON3 PLA 92_PIEL-720 1.75 MM X 1 KG",
        ),
        (
            "GRILON3 ASTRA CALIPSO 1.75 MM X 1 KG",
            "GRILON3 ASTRA JADE 1.75 MM X 1 KG",
        ),
        (
            "GRILON3 PLA 07_VERDE 1.75 MM X 1 KG",
            "GRILON3 PLA 19_VERDE MANZANA 1.75 MM X 1 KG",
        ),
        (
            "KIT LAPIZ 3D GRILON3 PLA 20 COLORES 10M POR COLOR (200M)",
            "KIT LAPIZ 3D GRILON3 PLA 10 COLORES 10M POR COLOR (100M)",
        ),
        (
            "GRILON3 PLA 850 09_NARANJA UV GLOW 1.75 MM X 1 KG",
            "GRILON3 PETG NARANJA PRAGA 1.75 MM X 1 KG",
        ),
    ],
)
def test_keeps_provider_organized_color_variants_separate(left_name, right_name):
    left = normalize_record(raw(left_name, brand_hint="Grilon3"))
    right = normalize_record(raw(right_name, brand_hint="Grilon3"))

    assert left.color != "Sin color"
    assert right.color != "Sin color"
    assert left.color != right.color
    assert build_product_id(left) != build_product_id(right)


def test_build_display_name_avoids_repeating_material_and_variant():
    fields = normalize_record(raw("3N3 PLA+ Rojo 1kg 1.75mm"))

    assert build_display_name(fields) == "PLA+ Rojo 3N3 1 kg 1.75 mm"
