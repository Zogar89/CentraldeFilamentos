from stockcentral.providers import MANUFACTURERS, SOURCES


def test_sources_cover_initial_amba_providers():
    assert set(SOURCES) == {"filamentos3d", "grupo_senz", "mundoinsumos"}
    assert SOURCES["filamentos3d"].zone == "Zona Sur"
    assert SOURCES["grupo_senz"].zone == "Zona Oeste"
    assert SOURCES["mundoinsumos"].zone == "Zona Norte"


def test_google_sheet_sources_include_sheet_ids_and_gids():
    assert SOURCES["grupo_senz"].sheet_id == "14nblAeXZfx_TEeHj4xnK90hSmUp3hk6KSO4nUTrb9zM"
    assert SOURCES["grupo_senz"].gid == "0"
    assert SOURCES["mundoinsumos"].sheet_id == "1r-nKy4tRRtZ-5xwgxAcia8REDVW0Dv0h"
    assert SOURCES["mundoinsumos"].gid == "1981641819"


def test_provider_contacts_are_optional_and_not_invented():
    assert SOURCES["filamentos3d"].contact_url == "https://filamentos3d.com.ar/"
    assert SOURCES["grupo_senz"].contact_whatsapp_url == ""
    assert SOURCES["grupo_senz"].contact_email == ""
    assert SOURCES["grupo_senz"].address == ""


def test_manufacturer_configuration_keeps_3n3_without_official_site():
    assert MANUFACTURERS["grilon3"].products_url == "https://grilon3.com.ar/productos/"
    assert MANUFACTURERS["grilon3"].has_official_product_pages is True
    assert MANUFACTURERS["3n3"].official_site_url == ""
    assert MANUFACTURERS["3n3"].has_official_product_pages is False
