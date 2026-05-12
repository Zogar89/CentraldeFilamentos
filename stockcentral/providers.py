from __future__ import annotations

from dataclasses import dataclass

from stockcentral.models import ManufacturerInfo


@dataclass(frozen=True)
class SourceConfig:
    id: str
    name: str
    zone: str
    homepage_url: str
    source_url: str
    connector: str
    sheet_id: str = ""
    gid: str = "0"
    brand_hint: str = ""
    contact_whatsapp_url: str = ""
    contact_email: str = ""
    address: str = ""
    contact_url: str = ""


SOURCES: dict[str, SourceConfig] = {
    "filamentos3d": SourceConfig(
        id="filamentos3d",
        name="Filamentos3D",
        zone="Zona Sur",
        homepage_url="https://filamentos3d.com.ar/",
        source_url="https://filamentos3d.com.ar/grilon3.php",
        connector="filamentos3d",
        brand_hint="Grilon3",
        contact_url="https://filamentos3d.com.ar/",
    ),
    "grupo_senz": SourceConfig(
        id="grupo_senz",
        name="Grupo Senz",
        zone="Zona Oeste",
        homepage_url="https://docs.google.com/spreadsheets/d/14nblAeXZfx_TEeHj4xnK90hSmUp3hk6KSO4nUTrb9zM",
        source_url="https://docs.google.com/spreadsheets/d/14nblAeXZfx_TEeHj4xnK90hSmUp3hk6KSO4nUTrb9zM",
        connector="google_sheet",
        sheet_id="14nblAeXZfx_TEeHj4xnK90hSmUp3hk6KSO4nUTrb9zM",
        gid="0",
    ),
    "mundoinsumos": SourceConfig(
        id="mundoinsumos",
        name="MundoInsumos",
        zone="Zona Norte",
        homepage_url="https://www.mundoinsumos.com.ar/",
        source_url="https://docs.google.com/spreadsheets/d/1r-nKy4tRRtZ-5xwgxAcia8REDVW0Dv0h/edit?gid=1981641819#gid=1981641819",
        connector="google_sheet",
        sheet_id="1r-nKy4tRRtZ-5xwgxAcia8REDVW0Dv0h",
        gid="1981641819",
        contact_url="https://www.mundoinsumos.com.ar/",
    ),
}

MANUFACTURERS: dict[str, ManufacturerInfo] = {
    "grilon3": ManufacturerInfo(
        id="grilon3",
        name="Grilon3",
        official_site_url="https://grilon3.com.ar/",
        products_url="https://grilon3.com.ar/productos/",
        has_official_product_pages=True,
    ),
    "3n3": ManufacturerInfo(
        id="3n3",
        name="3N3",
        official_site_url="",
        products_url="",
        has_official_product_pages=False,
    ),
}
