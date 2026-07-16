import json
from collections import Counter
from pathlib import Path


PUBLIC = Path("public")
SRC = Path("src")


def test_material_swatches_are_generated_and_published_by_workflows():
    data_capture = Path(".github/workflows/data-capture.yml").read_text(encoding="utf-8")
    thumbnails_workflow = Path(".github/workflows/thumbnails.yml").read_text(encoding="utf-8")

    assert "python -m centraldefilamentos.generate_material_swatches" in data_capture
    assert "public/assets/material-swatches" in data_capture
    assert 'cp -a public/assets/material-swatches/. "$pages_dir/assets/material-swatches/"' in data_capture
    assert "python -m centraldefilamentos.generate_material_swatches" in thumbnails_workflow
    assert "public/assets/material-swatches" in thumbnails_workflow


def test_prerendered_material_swatches_are_used_across_product_views():
    summary_source = (SRC / "SummaryApp.svelte").read_text(encoding="utf-8")
    quote_item_source = (SRC / "components" / "QuoteListItem.svelte").read_text(encoding="utf-8")
    quote_list_source = (SRC / "lib" / "quoteList.js").read_text(encoding="utf-8")
    shared_source = (SRC / "lib" / "shared.js").read_text(encoding="utf-8")
    css = (SRC / "styles" / "global.css").read_text(encoding="utf-8")

    assert "materialSwatchPath" in shared_source
    assert "materialSwatchAlt" in shared_source
    assert "material_swatch_url" in summary_source
    assert "summary-material-swatch" in summary_source
    assert "materialSwatchUrl" in quote_list_source
    assert "materialFinish" in quote_list_source
    assert "quote-list-material-swatch" in quote_item_source
    assert ".quote-list-material-swatch" in css


def test_static_frontend_files_exist_and_are_linked():
    index = Path("index.html").read_text(encoding="utf-8")
    resumen = Path("resumen.html").read_text(encoding="utf-8")
    internal = Path("estadisticas.html").read_text(encoding="utf-8")
    flags = json.loads((PUBLIC / "data" / "feature_flags.json").read_text(encoding="utf-8"))
    summary_view = (SRC / "SummaryApp.svelte").read_text(encoding="utf-8")
    site_header = (SRC / "components" / "SiteHeader.svelte").read_text(encoding="utf-8")

    assert 'type="module" src="/src/summary.js"' in index
    assert 'type="module" src="/src/summary.js"' in resumen
    assert not (SRC / "CatalogApp.svelte").exists()
    assert not (SRC / "catalog.js").exists()
    assert '{ id: "summary", label: "Resumen", href: "index.html" }' in site_header
    assert 'label: "Catálogo"' not in site_header
    assert 'href: "index.html#site-footer"' in site_header
    assert 'href: "estadisticas.html"' not in site_header
    assert "provider-status" not in site_header
    assert "brand-mark" in site_header
    assert "SiteHeader" in summary_view
    assert 'id="merge-brands-toggle"' not in resumen
    assert "Fusionar Grilon3 + 3N3" not in resumen
    assert "estadisticas.html" not in index
    assert "estadisticas.html" not in resumen
    assert "vendedores-interno.html" not in index
    assert "vendedores-interno.html" not in resumen
    assert 'type="module" src="/src/vendor-stats.js"' in internal
    assert 'noindex,nofollow' in internal
    assert flags["vendorStatsEnabled"] is True
    for entry in ["summary.js", "vendor-stats.js"]:
        js = (SRC / entry).read_text(encoding="utf-8")
        assert 'import { mount } from "svelte"' in js
        assert "mount(" in js
        assert "new " not in js


def test_quote_list_source_contract_covers_foundation():
    def read_source(path):
        return path.read_text(encoding="utf-8") if path.exists() else ""

    quote_list = read_source(SRC / "lib" / "quoteList.js")
    quote_panel = read_source(SRC / "components" / "QuoteListPanel.svelte")
    quote_item = read_source(SRC / "components" / "QuoteListItem.svelte")
    quote_quantity = read_source(SRC / "components" / "QuoteQuantityControl.svelte")
    summary_view = read_source(SRC / "SummaryApp.svelte")
    quote_sources = quote_list + quote_panel + quote_item + quote_quantity
    js = quote_sources

    for path in [
        SRC / "lib" / "quoteList.js",
        SRC / "components" / "QuoteListPanel.svelte",
        SRC / "components" / "QuoteListItem.svelte",
        SRC / "components" / "QuoteQuantityControl.svelte",
    ]:
        assert path.exists(), f"Missing quote-list artifact: {path}"

    for identifier in [
        "quoteListStorageKey",
        "centraldefilamentos.quoteList.v1",
        "quoteListSchemaVersion",
        "loadQuoteList",
        "saveQuoteList",
        "normalizeQuoteList",
        "snapshotQuoteItem",
        "reconcileQuoteList",
        "clampQuoteQuantity",
        "quoteQuantityLabel",
        "productId",
        "sku",
        "ean",
        "originalName",
        "material",
        "color",
        "brand",
        "diameterMm",
        "presentation",
        "quantity",
    ]:
        assert identifier in js

    for copy in [
        "Caja x12",
        "Lista de cotizacion",
        "Guardada en este dispositivo",
        "StockCentral no vende ni procesa pedidos.",
        "Controles rapidos",
        "Ocultar controles rapidos",
        "sin codigo",
        "sin diametro",
        "sin presentacion",
        "confirmar dato",
        "confirmar stock",
        "Limpiar lista",
    ]:
        assert copy in js

    assert "¿Vaciar la lista de cotizacion? Se quitaran todos los filamentos guardados en este navegador." in summary_view

    for control_token in [
        'aria-label="Restar 1 unidad"',
        'type="number"',
        'aria-label="Cantidad de unidades"',
        'aria-label="Sumar 1 unidad"',
        'aria-label="Completar siguiente caja de 12 unidades"',
    ]:
        assert control_token in quote_quantity

    assert "unidad" in quote_sources
    assert "unidades" in quote_sources
    assert "kg" not in quote_sources.lower()

    quote_class_source = "\n".join(
        line
        for line in js.splitlines()
        if "class=" in line and "quote" in line.lower()
    ).lower()
    for banned in ["cart", "carrito", "checkout", "orden", "pedido", "comprar ahora"]:
        assert banned not in quote_class_source


def test_quote_list_styles_contract_covers_panel_and_controls():
    def read_source(path):
        return path.read_text(encoding="utf-8") if path.exists() else ""

    quote_list = read_source(SRC / "lib" / "quoteList.js")
    quote_panel = read_source(SRC / "components" / "QuoteListPanel.svelte")
    quote_drawer = read_source(SRC / "components" / "QuoteListDrawer.svelte")
    summary_view = read_source(SRC / "SummaryApp.svelte")
    css = read_source(SRC / "styles" / "global.css")
    quote_sources = summary_view + quote_list + quote_panel + quote_drawer

    assert (SRC / "components" / "QuoteListDrawer.svelte").exists()
    for identifier in [
        "quote-list-drawer",
        "quote-list-backdrop",
        "quote-list-panel",
        "reconcileQuoteList",
        "removedCount",
        "resetReason",
        "storageAvailable",
        "saveError",
    ]:
        assert identifier in quote_sources + css

    for copy in [
        "No pudimos guardar la lista en este navegador. La podes usar durante esta sesion, pero se puede perder al cerrar la pagina.",
        "No se sincroniza con otra PC.",
        "StockCentral no vende ni procesa pedidos.",
        "Quitamos {count} item(s) que ya no aparecen en el catalogo publicado.",
    ]:
        assert copy in quote_sources

    assert "@media (max-width: 860px)" in css
    assert "@media (max-width: 520px)" in css
    assert "position: fixed" in css
    assert "bottom:" in css
    assert "width: min(460px" in css


def test_summary_svelte_uses_carretes_totals_and_provider_order():
    view = (SRC / "SummaryApp.svelte").read_text(encoding="utf-8")
    shared = (SRC / "lib" / "shared.js").read_text(encoding="utf-8")
    footer = (SRC / "components" / "SiteFooter.svelte").read_text(encoding="utf-8")
    quick_lines = (SRC / "components" / "QuickLines.svelte").read_text(encoding="utf-8")
    css = (SRC / "styles" / "global.css").read_text(encoding="utf-8")
    js = view + shared + footer + quick_lines

    assert "data/stock.json" in js
    assert "Zona Norte" in js
    assert "Zona Oeste" in js
    assert "Zona Sur" in js
    assert "Carretes por proveedor" in js
    assert "summary-presentation" in js
    assert "formatWeightLabel" in js
    assert "formatPresentation" in js
    assert "samplerLengthLabel" in js
    assert "isSamplerProduct" in js
    assert "productSummaryName" in js
    assert "summary-product" in js
    assert "summary-color-swatch" in js
    assert "colorSwatchStyle" in js
    assert "row.product.pantone" in js
    assert "mergeBrands" not in js
    assert "mergeCompatibleBrands" not in js
    assert "mergeRowKey" not in js
    assert "mergedBrandKey" not in js
    assert "brandsLabel" not in js
    assert "Grilon3 + 3N3" not in js
    assert "matchesSearchTerms" in js
    assert "products.filter(matchesFilters)" in js
    for filter_id in [
        "search-input",
        "material-filter",
        "color-filter",
        "provider-filter",
        "variant-filter",
        "diameter-filter",
        "weight-filter",
        "brand-filter",
        "stock-filter",
    ]:
        assert filter_id in view
    assert "showCatalogHelp" in view
    assert "addQuoteItem(row.product)" in view
    assert "toggleStockSubscription(row.product, offer)" in view
    assert "QuoteListDrawer" in view
    assert "summary-product-photo" in view
    assert "summary-product-photo-placeholder" in view
    assert "summary-material-swatch" in view
    assert "groupPresentationRows" in view
    assert "summary-photo-column" in view
    assert "summary-color-column" in view
    assert "summary-add-column" in view
    assert "presentation-grouped" in view
    assert "presentation-group-marker" in view
    assert "quote-list-trigger" in view
    assert "quote-list-side-panel" not in view
    assert "showAssetPreview" in view
    assert "openAssetPreview" in view
    assert "matchesSearchToken" in js
    assert "searchTokens" in js
    assert 'term === "pla"' in js
    assert 'token === "pla+"' in js
    assert "token.startsWith(term)" in js
    assert "summary-group-row" in js
    assert "quickLineValues" in js
    assert '"ABS"' in js
    assert '"PLA Boutique"' in js
    assert '"Nylon 6"' in js
    assert "summaryGroupTargetId" in js
    assert "updateStickyGroupRows" not in js
    assert "summaryStickyTop" not in js
    assert "is-stuck" not in js
    assert "footer-grid" in js
    assert "sourceWhatsappUrl" in js
    assert "contactContext" in js
    assert "Creado por Gabriel" in js
    assert "Reportar error" in js
    assert "Sumar proveedor" in js
    assert "https://github.com/Zogar89/CentraldeFilamentos/issues/new" in js
    assert "slugText" in js
    assert "groupSummaryRows" in js
    assert "0*" not in js
    assert "El proveedor seguramente no maneja esta variante" not in js
    assert "A revisar" not in js
    assert "Rev." not in js
    assert "total_stock_units" in js
    assert "stockDelta" in js
    assert "stock_delta_units" in js
    assert "vs ayer" in js
    assert "const stockDelta = stockDeltaTemplate(source.stats || {});" not in js
    assert "total_stock_kg" not in js

    assert ".quote-list-drawer" in css
    assert "justify-items: end" in css
    assert "width: min(460px" in css
    assert "@media (max-width: 1100px)" in css
    assert ".summary-total" in css
    assert ".summary-photo-cell" in css
    assert ".summary-product-photo-placeholder" in css
    assert ".summary-color-cell" in css
    assert ".summary-add-cell" in css
    assert ".presentation-group-marker" in css


def test_internal_vendor_svelte_uses_feature_flag_and_30_day_history():
    js = (SRC / "VendorStatsApp.svelte").read_text(encoding="utf-8") + (SRC / "lib" / "shared.js").read_text(encoding="utf-8")

    assert "data/feature_flags.json" in js
    assert "data/provider_stock_history.json" in js
    assert "data/build_business_log.json" in js
    assert "noCache" in js
    assert "cache: options.noCache ? \"no-store\" : \"default\"" in js
    assert "url.searchParams.set(\"v\"" in js
    assert "vendorStatsEnabled" in js
    assert "build-health" in js
    assert "last_good_sources" in js
    assert "slice(-30)" in js
    assert "stockSeriesForProvider" in js
    assert "stockChartForProvider" in js
    assert "vendor-stock-chart" in js
    assert "Evolucion 30d" in js
    assert "chart-line" in js
    assert "chart-point" in js
    assert "deltaForProvider" in js
    assert "vs dia anterior" in js
    assert "checksForDay" in js
    assert "details" in js
    assert "Chequeos del dia" in js
    assert "vs 09:00" in js
    assert "intraday-list" in js
    assert "intraday-row" in js
    assert "America/Argentina/Buenos_Aires" in js
    assert "vendor-dashboard" in js
    assert "vendor-disabled" in js
    assert "Cantidad por dia" in js
    assert "Variacion" in js


def test_styles_are_compact_and_responsive():
    css = (SRC / "styles" / "global.css").read_text(encoding="utf-8")

    assert "@media" in css
    assert "position: sticky" in css
    assert "grid-template-columns" in css
    assert "border-radius: 8px" in css
    assert ".group-section" in css
    assert ".group-section.quick-target" in css
    assert ".group-heading" in css
    assert ".quick-line::before" in css
    assert ".quick-lines-shell" in css
    assert ".quick-lines-cue" in css
    assert "quick-lines-cue-nudge" in css
    assert ".quick-line-abs" in css
    assert ".quick-line-boutique" in css
    assert ".quick-line-wood" in css
    assert ".quick-line-nylon" in css
    assert "flex-wrap: nowrap" in css
    assert "scroll-snap-type: x proximity" in css
    assert "-webkit-overflow-scrolling: touch" in css
    assert "scrollbar-width: none" in css
    assert "top: var(--quick-lines-height)" in css
    assert "scroll-margin-top" in css
    assert "repeat(auto-fit, minmax(320px, 1fr))" in css
    assert ".offer-main" in css
    assert ".stock-alert-banner" in css
    assert ".stock-watch-button" in css
    assert ".offer:target" in css
    assert ".presentation-list" in css
    assert ".presentation-row" in css
    assert ".chips" not in css
    assert ".chip" not in css
    assert ".product-visuals" in css
    assert ".media-presentation" in css
    assert ".color-swatch" in css
    assert ".swatch-pantone" in css
    assert ".product-media" in css
    assert ".official-product-link" in css
    assert ".image-preview" in css
    assert ".image-preview.visible" in css
    assert ".image-preview-backdrop" in css
    assert ".image-preview-modal" in css
    assert ".media-pantone" in css
    assert "cursor: zoom-in" in css
    assert "scroll-behavior: smooth" in css
    assert ".footer-provider:target" in css
    assert ".stock-delta" in css
    assert ".footer-provider-stock" in css
    assert ".stock-delta-up" in css
    assert ".stock-delta-down" in css
    assert ".footer-meta" in css
    assert ".summary-presentation" in css
    assert ".summary-product" in css
    assert ".summary-color-swatch" in css
    assert ".summary-product-name" in css
    assert ".category-sort" in css
    assert ".soft-button.active" in css
    assert ".summary-group-row" in css
    assert ".summary-group-row.quick-target" in css
    assert ".summary-group-row.is-stuck td" not in css
    assert "color: transparent" not in css
    assert "top: calc(var(--quick-lines-height) + var(--summary-head-height))" in css
    assert ".summary-table tbody .summary-group-row th" in css
    assert ".internal-shell" in css
    assert ".build-health" in css
    assert ".build-health-events" in css
    assert ".vendor-stat-grid" in css
    assert ".vendor-stock-chart" in css
    assert ".chart-line" in css
    assert ".chart-area" in css
    assert ".chart-point" in css
    assert ".vendor-history-table" in css
    assert ".intraday-checks" in css
    assert ".intraday-panel" in css
    assert ".intraday-list" in css
    assert ".intraday-row" in css
    assert ".delta-positive" in css
    assert ".delta-negative" in css


def test_generated_stock_data_has_one_offer_per_provider_per_card():
    payload = json.loads((PUBLIC / "data" / "stock.json").read_text(encoding="utf-8"))

    for product in payload["products"]:
        provider_counts = Counter(offer["provider_name"] for offer in product["offers"])
        repeated_providers = [provider for provider, count in provider_counts.items() if count > 1]

        assert repeated_providers == [], product["display_name"]


def test_generated_stock_data_has_no_stocked_products_without_color():
    payload = json.loads((PUBLIC / "data" / "stock.json").read_text(encoding="utf-8"))
    stocked_without_color = [
        product["display_name"]
        for product in payload["products"]
        if product["color"] == "Sin color" and product["offers"]
    ]

    assert stocked_without_color == []


def test_generated_stock_data_keeps_presentation_specific_images():
    payload = json.loads((PUBLIC / "data" / "stock.json").read_text(encoding="utf-8"))
    groups = {}
    for product in payload["products"]:
        if product["brand"] != "Grilon3" or not product["image_url"]:
            continue
        key = (
            product["material"],
            product["variant"],
            product["color"],
            product["brand"],
            product["diameter_mm"],
        )
        groups.setdefault(key, []).append(product)

    presentation_groups = [
        products
        for products in groups.values()
        if len({product["weight_g"] for product in products}) > 1
        and len({product["image_url"] for product in products}) > 1
    ]

    checked_groups = 0
    assert presentation_groups
    for products in presentation_groups:
        one_kg = [product for product in products if product["weight_g"] == 1000]
        larger = [product for product in products if product["weight_g"] and product["weight_g"] > 1000]
        if not one_kg or not larger:
            continue

        one_kg_image = one_kg[0]["image_url"]
        larger_images = {product["image_url"] for product in larger}
        checked_groups += 1
        assert one_kg_image not in larger_images
    assert checked_groups > 0


def test_generated_stock_data_does_not_use_large_spool_images_for_1kg_products():
    payload = json.loads((PUBLIC / "data" / "stock.json").read_text(encoding="utf-8"))
    large_markers = ("megafill", "maxicarrete")
    mismatches = [
        (product["id"], product["image_url"])
        for product in payload["products"]
        if product.get("weight_g") == 1000
        and any(marker in product.get("image_url", "").lower() for marker in large_markers)
    ]

    assert mismatches == []


def test_generated_stock_data_keeps_sampler_products_without_roll_images():
    payload = json.loads((PUBLIC / "data" / "stock.json").read_text(encoding="utf-8"))
    sampler_products = [
        product
        for product in payload["products"]
        if any(
            "SAMPLER" in offer["original_name"].upper()
            or "LAPIZ 3D" in offer["original_name"].upper()
            or "LÁPIZ 3D" in offer["original_name"].upper()
            for offer in product["offers"]
        )
    ]

    assert sampler_products
    assert [product["image_url"] for product in sampler_products if product["image_url"]] == []
    assert [product["manufacturer_product_url"] for product in sampler_products if product["manufacturer_product_url"]] == []


def test_generated_stock_data_has_official_metadata_for_technical_grilon3_lines():
    payload = json.loads((PUBLIC / "data" / "stock.json").read_text(encoding="utf-8"))
    technical_products = [
        product
        for product in payload["products"]
        if product["brand"] == "Grilon3"
        and product["variant"] in {"PP-T", "Acetal-POM"}
        and product["weight_g"] == 1000
    ]
    urls = [product["manufacturer_product_url"] for product in technical_products if product["manufacturer_product_url"]]
    non_manufacturer_images = [
        product["id"]
        for product in technical_products
        if product["image_url"] and product["image_source"] != "manufacturer"
    ]

    assert technical_products
    assert all(url.startswith("https://grilon3.com.ar/") for url in urls)
    assert any("/producto/" in url for url in urls)
    assert any("/categoria-producto/tecnicos/" in url for url in urls)
    assert non_manufacturer_images == []


def test_generated_stock_data_uses_local_thumbnails_for_local_images():
    payload = json.loads((PUBLIC / "data" / "stock.json").read_text(encoding="utf-8"))
    products_with_images = [
        product
        for product in payload["products"]
        if product.get("image_url", "").startswith("assets/")
    ]
    missing_or_broken = []

    assert products_with_images
    for product in products_with_images:
        thumbnail_url = product.get("thumbnail_url", "")
        thumbnail_path = PUBLIC / thumbnail_url
        if (
            not thumbnail_url.startswith("assets/thumbs/")
            or thumbnail_url == product["image_url"]
            or not thumbnail_path.exists()
            or thumbnail_path.suffix != ".webp"
        ):
            missing_or_broken.append((product["id"], product["image_url"], thumbnail_url))

    assert missing_or_broken == []


def test_color_picker_page_is_linked_and_built():
    html = Path("color-picker.html").read_text(encoding="utf-8")
    entry = (SRC / "color-picker.js").read_text(encoding="utf-8")
    app = (SRC / "ColorPickerApp.svelte").read_text(encoding="utf-8")
    header = (SRC / "components" / "SiteHeader.svelte").read_text(encoding="utf-8")
    vite = Path("vite.config.js").read_text(encoding="utf-8")

    assert 'src="/src/color-picker.js"' in html
    assert "mount(ColorPickerApp" in entry
    assert 'fetchJson("data/stock.json", null)' in app
    assert 'active="color-picker"' in app
    assert 'href: "color-picker.html"' in header
    assert 'colorPicker: resolve(__dirname, "color-picker.html")' in vite
    palette = (SRC / "components" / "ColorPalette.svelte").read_text(encoding="utf-8")
    assert 'aria-pressed={selectedIds.includes(group.id)}' in palette
    assert 'title={tooltip(group)}' in palette
    assert 'view === "continuous"' in palette
    assert 'view === "families"' in palette
    assert 'view === "map"' in palette
    assert "groupContinuousBands" in palette
    assert "color-picker-continuous-band" in palette
    assert "Rueda cromática intensa" in palette
    assert "Claros y apagados" in palette
    assert "Tierras y marrones" in palette
    assert "Neutros" in palette
    assert "Ocultar sin stock" in app
    assert "let hideOutOfStock = true;" in app
    assert "let hideSamplers = true;" in app
    assert "Ocultar samplers" in app
    assert "!group.isSampler" in app

    similar = (SRC / "components" / "SimilarColorSearch.svelte").read_text(encoding="utf-8")
    assert "Buscar colores similares" in similar
    assert "result.distance.toFixed(1)" in similar
    assert "onCompare(result.group)" in similar
    assert 'role="status"' in similar
    assert "Se encontraron" in similar
    assert "findSimilarColors(visibleGroups, normalizedSimilarHex, referenceGroupId, 3)" in app
    assert "if (searchActive && isValidHex(normalizedSimilarHex))" in app

    comparator = (SRC / "components" / "ColorComparator.svelte").read_text(encoding="utf-8")
    assert "group.materialSwatchUrl" in comparator
    assert "rgbFromHex(group.hex)" in comparator
    assert "onAddPresentation(presentation.product)" in comparator
    assert "incrementQuoteListItem(quoteItems, product)" in app
    assert "saveQuoteList({" in app

    styles = (SRC / "styles" / "global.css").read_text(encoding="utf-8")
    assert "data-tooltip" in palette
    assert 'aria-live="polite"' in app
    assert "@media (max-width: 760px)" in styles
    assert ".color-picker-tile:focus-visible::after" in styles
    assert "grid-template-columns: repeat(2, minmax(0, 1fr))" in styles
    assert "grid-template-columns: minmax(0, 1fr)" in styles
    assert ".color-picker-continuous-band" in styles


def test_all_public_pages_declare_the_shared_favicon_and_are_publishable():
    html_pages = [
        "index.html",
        "catalogo.html",
        "resumen.html",
        "color-picker.html",
        "estadisticas.html",
    ]
    for page_path in html_pages:
        html = Path(page_path).read_text(encoding="utf-8")
        assert '<link rel="icon" href="%BASE_URL%favicon.svg" type="image/svg+xml">' in html

    assert (PUBLIC / "favicon.svg").exists()

    vite = Path("vite.config.js").read_text(encoding="utf-8")
    assert 'catalogo: resolve(__dirname, "catalogo.html")' in vite

    workflow = Path(".github/workflows/pages.yml").read_text(encoding="utf-8")
    for watched_path in ["catalogo.html", "color-picker.html", "public/favicon.svg"]:
        assert f'- "{watched_path}"' in workflow


def test_color_picker_map_uses_dynamic_point_coordinates() -> None:
    source = Path("src/components/ColorPalette.svelte").read_text(encoding="utf-8")
    css = Path("src/styles/global.css").read_text(encoding="utf-8")

    assert "left: ${group.mapX}%" in source
    assert "top: ${group.mapY}%" in source
    assert "--map-size: ${group.mapSize}px" in source
    assert ".color-picker-map-point" in css


def test_color_picker_selected_tile_uses_internal_selection_indicator() -> None:
    css = Path("src/styles/global.css").read_text(encoding="utf-8")

    assert '.color-picker-tile[aria-pressed="true"] { box-shadow: inset' in css
    assert '.color-picker-tile[aria-pressed="true"] { outline:' not in css


def test_color_picker_map_focus_indicator_stays_inside_tiles() -> None:
    css = Path("src/styles/global.css").read_text(encoding="utf-8")

    assert '.color-picker-map-point .color-picker-tile:focus-visible::before { box-shadow: inset' in css
    assert '.color-picker-map-point .color-picker-tile[aria-pressed="true"]:focus-visible::before { box-shadow: inset' in css
