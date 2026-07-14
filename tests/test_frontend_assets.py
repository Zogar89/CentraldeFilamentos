import json
import subprocess
from collections import Counter
from pathlib import Path


PUBLIC = Path("public")
SRC = Path("src")


def test_static_frontend_files_exist_and_are_linked():
    index = Path("index.html").read_text(encoding="utf-8")
    resumen = Path("resumen.html").read_text(encoding="utf-8")
    internal = Path("estadisticas.html").read_text(encoding="utf-8")
    flags = json.loads((PUBLIC / "data" / "feature_flags.json").read_text(encoding="utf-8"))
    catalog_view = (SRC / "CatalogApp.svelte").read_text(encoding="utf-8")
    site_header = (SRC / "components" / "SiteHeader.svelte").read_text(encoding="utf-8")

    assert 'type="module" src="/src/catalog.js"' in index
    assert 'href: "resumen.html"' in site_header
    assert 'href: "index.html#site-footer"' in site_header
    assert 'href: "estadisticas.html"' not in site_header
    assert "provider-status" not in site_header
    assert "brand-mark" in site_header
    assert "SiteHeader" in catalog_view
    assert 'type="module" src="/src/summary.js"' in resumen
    assert 'id="merge-brands-toggle"' not in resumen
    assert "Fusionar Grilon3 + 3N3" not in resumen
    assert "estadisticas.html" not in index
    assert "estadisticas.html" not in resumen
    assert "vendedores-interno.html" not in index
    assert "vendedores-interno.html" not in resumen
    assert 'type="module" src="/src/vendor-stats.js"' in internal
    assert 'noindex,nofollow' in internal
    assert flags["vendorStatsEnabled"] is True
    for entry in ["catalog.js", "summary.js", "vendor-stats.js"]:
        js = (SRC / entry).read_text(encoding="utf-8")
        assert 'import { mount } from "svelte"' in js
        assert "mount(" in js
        assert "new " not in js


def test_catalog_svelte_fetches_json_and_supports_required_filters():
    view = (SRC / "CatalogApp.svelte").read_text(encoding="utf-8")
    shared = (SRC / "lib" / "shared.js").read_text(encoding="utf-8")
    footer = (SRC / "components" / "SiteFooter.svelte").read_text(encoding="utf-8")
    site_header = (SRC / "components" / "SiteHeader.svelte").read_text(encoding="utf-8")
    quick_lines = (SRC / "components" / "QuickLines.svelte").read_text(encoding="utf-8")
    subscriptions = (SRC / "lib" / "stockSubscriptions.js").read_text(encoding="utf-8")
    stock_workspace = (SRC / "lib" / "stockWatchWorkspace.js").read_text(encoding="utf-8")
    js = view + shared + footer + site_header + quick_lines + subscriptions + stock_workspace

    assert "data/stock.json" in js
    for filter_id in [
        "material-filter",
        "variant-filter",
        "color-filter",
        "diameter-filter",
        "weight-filter",
        "brand-filter",
        "provider-filter",
        "stock-filter",
    ]:
        assert filter_id in js
    assert "contact_whatsapp_url" in js
    assert "groupProducts" in js
    assert "group-section" in js
    assert "product.pantone" in js
    assert "product.sku" in js
    assert "product.ean" in js
    assert "PLA Standard" in js
    assert "PLA Flexible" in js
    assert "brillo tipo glitter" in js
    assert "E-PET - PET reciclado" in js
    assert "PP-T - polipropileno" in js
    assert "Sampler / lápiz 3D" in js
    assert "isSamplerProduct" in js
    assert "formatPresentation" in js
    assert "samplerLengthLabel" in js
    assert "groupBaseProducts" in js
    assert "official-product-link" in js
    assert "Abrir página oficial" in js
    assert "data-preview-src" in js
    assert "thumbnail_url" in js
    assert 'loading="lazy"' in js
    assert 'decoding="async"' in js
    assert "image-preview" in js
    assert "openImagePreview" in js
    assert "image-preview-modal" in js
    assert "media-pantone" in js
    assert "compareImagePresentations" in js
    assert "imagePresentationRank" in js
    assert ".filter((item) => item.image_url)" in js
    assert "Number(product.weight_g) === 1000" in js
    assert "Number(product.weight_g) === 2500" in js
    assert "pantoneSwatchLabel" in js
    assert "colorSwatchStyle" in js
    assert "baseColorFor" in js
    assert "foldText" in js
    assert "matchesSearchTerms" in js
    assert "setFilter" in js
    assert "filters, categoryOrder, products.filter" in js
    assert "materialOptions = (products, valuesFor" in js
    assert "providerOptions = (products, providerValues" in js
    assert "matchesSearchToken" in js
    assert "searchTokens" in js
    assert 'term === "pla"' in js
    assert 'token === "pla+"' in js
    assert "token.startsWith(term)" in js
    assert "queryText.includes" not in js
    assert "presentation-row" in js
    assert "productBaseName" in js
    assert "quickLineValues" in js
    assert "visibleLines" in js
    assert "products, lineValues()" in js
    assert "quickLabel" in js
    assert "quickTone" in js
    assert '"ABS"' in js
    assert '"PLA Boutique"' in js
    assert '"Nylon 6"' in js
    assert "PLA Wood" in js
    assert "categoryOrder" in js
    assert "compareGroups" in js
    assert "compareProductGroups" in js
    assert "scrollIntoView" in js
    assert "quick-target" in js
    assert "updateScrollCue" in js
    assert "showScrollCue" in js
    assert "groupTargetId" in js
    assert "slugText" in js
    assert "state.filters.variant = button.dataset.line" not in js
    assert "sin stock online registrado" in js
    assert "offer-main" in js
    assert "providerTitle" in js
    assert "Sin cantidad" in js
    assert "stockSubscriptionsStorageKey" in js
    assert "centraldefilamentos.stockSubscriptions.v1" in js
    assert "loadStockSubscriptions" in js
    assert "saveStockSubscriptions" in js
    assert "subscriptionKey" in js
    assert "stockSignature" in js
    assert "stockAlerts" in js
    assert "confirmedQuantityIncrease" in js
    assert "currentQuantity > previousQuantity" in js
    assert "previousQuantity" in js
    assert "stockAlertLabel" in js
    assert "Tus filamentos esperados volvieron" in site_header
    assert "stock-alert-banner" in site_header
    assert "stock-watch-button" in js
    assert "Avisarme si sube o vuelve el stock" in js
    assert "Seguir cambios de stock" in js
    assert "Dejar de seguir cambios de stock" in js
    assert "createStockWatchWorkspace" in js
    assert "dismissStockAlerts" in js
    assert "stockWatchTargetId" in js
    assert "0*" not in js
    assert "El proveedor seguramente no maneja esta variante." not in js
    assert "providerAnchorId" in js
    assert "proveedor-" in js
    assert "sourceWhatsappUrl" in js
    assert "mapsHref" in js
    assert "www.google.com/maps/search" in js
    assert "footer-detail-link" in js
    assert "contactContext" in js
    assert "stockDelta" in js
    assert "stock_delta_units" in js
    assert "vs ayer" in js
    assert "Creado por Gabriel" in js
    assert "Reportar error" in js
    assert "Sumar proveedor" in js
    assert "https://github.com/Zogar89/CentraldeFilamentos/issues/new" in js
    assert "encodeURIComponent" in js
    assert "Rev." not in js
    assert "whatsappLink" not in js
    assert 'class="chips"' not in js
    assert "function chip" not in js
    assert "<span>${escapeHtml(offer.provider_zone)}</span>" not in js
    assert "product.pantone ? chip(product.pantone)" not in js


def test_quote_list_source_contract_covers_foundation():
    def read_source(path):
        return path.read_text(encoding="utf-8") if path.exists() else ""

    catalog = read_source(SRC / "CatalogApp.svelte")
    quote_list = read_source(SRC / "lib" / "quoteList.js")
    quote_panel = read_source(SRC / "components" / "QuoteListPanel.svelte")
    quote_item = read_source(SRC / "components" / "QuoteListItem.svelte")
    quote_quantity = read_source(SRC / "components" / "QuoteQuantityControl.svelte")
    quote_sources = quote_list + quote_panel + quote_item + quote_quantity
    js = catalog + quote_sources

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
        "QuoteListPanel",
        "QuoteListItem",
        "QuoteQuantityControl",
        "addQuoteItem",
        "createQuoteWorkspace",
        "setQuoteItemQuantity",
        "removeQuoteItem",
        "clearQuoteList",
        "toggleQuoteControls",
        "presentation-row",
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
        "Agregar 1 unidad a la lista de cotizacion",
        "+1",
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
        "¿Vaciar la lista de cotizacion? Se quitaran todos los filamentos guardados en este navegador.",
    ]:
        assert copy in js

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


def test_catalog_delegates_interaction_state_to_shared_workspaces():
    catalog = (SRC / "CatalogApp.svelte").read_text(encoding="utf-8")

    for required in [
        'import { createQuoteWorkspace } from "./lib/quoteWorkspace.js";',
        'import { createStockWatchWorkspace } from "./lib/stockWatchWorkspace.js";',
        "createQuoteWorkspace({",
        "createStockWatchWorkspace({",
        "unsubscribeQuoteWorkspace",
        "unsubscribeStockWatchWorkspace",
        "showQuickControls: true",
        "QuoteListPanel",
        "QuoteListDrawer",
        "quote-add-button",
        "stock-watch-button",
        "quote-import-dialog",
        "dismissStockAlerts",
        "stockWatchTargetId",
        "exportCleanupTimers",
        "exportObjectUrls",
    ]:
        assert required in catalog

    destroy_block = catalog.split("onDestroy(() => {", 1)[1].split("});", 1)[0]
    for cleanup in [
        "unsubscribeQuoteWorkspace();",
        "unsubscribeStockWatchWorkspace();",
        "quoteFeedbackTimers",
        "stockWatchFeedbackTimers",
        "exportCleanupTimers",
        "exportObjectUrls",
    ]:
        assert cleanup in destroy_block

    for duplicated_or_low_level in [
        "loadQuoteList",
        "saveQuoteList",
        "initializeQuoteList",
        "snapshotQuoteItem",
        "combineQuoteListItems",
        "previewQuoteListImport",
        "serializeQuoteListExport",
        "loadStockSubscriptions",
        "saveStockSubscriptions",
        "stockSignature",
        "saveQuoteListState",
        "reconcileStockSubscriptions",
        "findSubscribedOffer",
    ]:
        assert duplicated_or_low_level not in catalog

    assert catalog.count("readOnly={quoteListReadOnly}") == 2


def test_catalog_import_reads_only_publish_the_latest_live_request():
    catalog = (SRC / "CatalogApp.svelte").read_text(encoding="utf-8")
    destroy_block = catalog.split("onDestroy(() => {", 1)[1].split("});", 1)[0]
    picker_block = catalog.split("function openQuoteImportPicker() {", 1)[1].split("\n  async function handleQuoteImportFile", 1)[0]
    import_block = catalog.split("async function handleQuoteImportFile(event) {", 1)[1].split("\n  function applyQuoteImport", 1)[0]
    close_block = catalog.split("function closeQuoteImport() {", 1)[1].split("\n  }", 1)[0]

    assert "let quoteImportRequestId = 0;" in catalog
    assert "function beginQuoteImportRequest()" in catalog
    assert "function invalidateQuoteImportRequest()" in catalog
    assert "function isCurrentQuoteImportRequest(requestId)" in catalog

    assert "if (!quoteWorkspace)" in picker_block
    assert picker_block.index("if (!quoteWorkspace)") < picker_block.index("quoteImportInput?.click()")

    for required in [
        "const requestId = beginQuoteImportRequest();",
        "if (!quoteWorkspace)",
        "await file.text()",
        "isCurrentQuoteImportRequest(requestId)",
        "catch",
    ]:
        assert required in import_block
    assert import_block.index("if (!quoteWorkspace)") < import_block.index("await file.text()")
    assert import_block.index('quoteImportError = "";') < import_block.index("await file.text()")
    assert import_block.count("isCurrentQuoteImportRequest(requestId)") >= 2

    assert "invalidateQuoteImportRequest();" in close_block
    assert "invalidateQuoteImportRequest();" in destroy_block


def test_quote_list_styles_contract_covers_panel_and_controls():
    def read_source(path):
        return path.read_text(encoding="utf-8") if path.exists() else ""

    catalog = read_source(SRC / "CatalogApp.svelte")
    quote_list = read_source(SRC / "lib" / "quoteList.js")
    quote_workspace = read_source(SRC / "lib" / "quoteWorkspace.js")
    quote_panel = read_source(SRC / "components" / "QuoteListPanel.svelte")
    quote_drawer = read_source(SRC / "components" / "QuoteListDrawer.svelte")
    css = read_source(SRC / "styles" / "global.css")
    quote_sources = catalog + quote_list + quote_workspace + quote_panel + quote_drawer

    assert (SRC / "components" / "QuoteListDrawer.svelte").exists()
    for identifier in [
        "QuoteListDrawer",
        "quote-floating-button",
        "quote-list-drawer",
        "quote-list-backdrop",
        "quote-list-panel",
        "quote-list-layout-active",
        "openQuoteDrawer",
        "closeQuoteDrawer",
        "handleQuoteDrawerKeydown",
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
        "Quitamos ${initialized.removedCount} item(s) que ya no aparecen en el catálogo publicado.",
    ]:
        assert copy in quote_sources

    assert "@media (max-width: 820px)" in css
    assert "@media (max-width: 520px)" in css
    assert "position: fixed" in css
    assert "bottom:" in css
    assert "minmax(320px, 360px)" in css


def test_summary_svelte_uses_carretes_totals_and_provider_order():
    view = (SRC / "SummaryApp.svelte").read_text(encoding="utf-8")
    shared = (SRC / "lib" / "shared.js").read_text(encoding="utf-8")
    footer = (SRC / "components" / "SiteFooter.svelte").read_text(encoding="utf-8")
    quick_lines = (SRC / "components" / "QuickLines.svelte").read_text(encoding="utf-8")
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
    assert "query, rows.filter" in js
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
    assert "groupRows" in js
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


def test_summary_organizes_materials_and_preserves_pla_subrange_detail():
    view = (SRC / "SummaryApp.svelte").read_text(encoding="utf-8")
    shared = (SRC / "lib" / "shared.js").read_text(encoding="utf-8")

    assert "export function subrangeLabel(product)" in shared
    assert "if (product?.subrange) return product.subrange;" in shared
    assert 'if (product?.material !== "PLA") return "";' in shared
    assert 'lineLabel(product).replace(/^PLA\\s+/, "") || "Standard"' in shared
    assert "export function finishLabel(product)" in shared
    assert 'return product?.finish || "";' in shared

    assert "materialSections" in view
    assert "groupMaterialSections" in view
    assert "summary-material-row" in view
    assert "section.material" in view
    assert "subrange: subrangeLabel(row.product)" in view
    assert "finish: finishLabel(row.product)" in view
    assert "group.finish" in view
    assert "summary-group-finish" in view

    group_key = view[view.index("function groupKey(product)"):view.index("function groupTitle(product)")]
    assert "subrangeLabel(product)" in group_key
    assert "finishLabel(product)" in group_key
    assert "product.brand" in group_key
    assert "product.diameter_mm" in group_key
    assert "lineLabel(product)" in group_key
    assert "product.variant" in group_key

    assert 'data-line={group.line}' in view
    assert 'targetSelector=".summary-group-row"' in view


def test_summary_reuses_action_workspaces_and_preserves_cell_offer_contract():
    view = (SRC / "SummaryApp.svelte").read_text(encoding="utf-8")
    panel = (SRC / "components" / "QuoteListPanel.svelte").read_text(encoding="utf-8")
    drawer = (SRC / "components" / "QuoteListDrawer.svelte").read_text(encoding="utf-8")
    item = (SRC / "components" / "QuoteListItem.svelte").read_text(encoding="utf-8")
    css = (SRC / "styles" / "global.css").read_text(encoding="utf-8")
    quote_sources = view + panel

    for token in [
        "createQuoteWorkspace",
        "createStockWatchWorkspace",
        "QuoteListPanel",
        "QuoteListDrawer",
        "QuoteProviderCoverage",
        "quote-summary-add",
        "summary-stock-watch",
        "stockAlerts",
        "quoteImportPreview",
        "applyQuoteImport",
        "quoteImportRequestId",
        "beginQuoteImportRequest",
        "isCurrentQuoteImportRequest",
        "quote-list-layout-active",
        "quote-floating-button",
    ]:
        assert token in quote_sources + css

    assert 'import { buildSummaryRows, summaryProductImage } from "./lib/summaryRows.js";' in view
    assert "buildSummaryRows(products, sources)" in view
    assert "cell.offer = offer;" not in view
    assert "{#if cell?.offer}" in view
    assert "stockWatchWorkspace.toggle(product, offer)" in view
    assert "quoteWorkspace.addProduct(product)" in view
    assert "aria-pressed={isSubscribed(row.product, cell.offer)}" in view
    assert "stockWatchTargetId(row.product, cell.offer)" in view
    assert "cell.offer.provider_name || source.name" in view
    assert "summaryProductImage(row.product)" in view
    assert "row.product.sku" in view
    assert "row.product.ean" in view
    assert "row.product.pantone" in view
    assert "quoteListReadOnly" in view
    assert "readOnly={quoteListReadOnly}" in view
    assert "disabled={readOnly}" in panel
    assert "disabled={readOnly}" in item
    assert "{readOnly}" in drawer
    assert "componentActive" in view
    assert "invalidateQuoteImportRequest();" in view
    assert "min-width: 44px" in css
    assert "min-height: 44px" in css
    assert ".summary-table-region" in css


def test_summary_sticky_headers_are_explicit_across_scroll_modes():
    css = (SRC / "styles" / "global.css").read_text(encoding="utf-8")
    base_region = css.split(".summary-table-region {", 1)[1].split("}", 1)[0]
    quote_scroller = css.split(
        ".summary-action-layout.quote-list-layout-active .summary-table-region {", 1
    )[1].split("}", 1)[0]
    desktop_head = css.split(".summary-table thead th {", 1)[1].split("}", 1)[0]
    quote_head = css.split(
        ".summary-action-layout.quote-list-layout-active .summary-table thead th {", 1
    )[1].split("}", 1)[0]
    quote_groups = css.split(
        ".summary-action-layout.quote-list-layout-active .summary-table tbody .summary-group-row th,", 1
    )[1].split("}", 1)[0]
    mobile = css.split("@media (max-width: 820px)", 1)[1]

    assert "overflow-x" not in base_region
    assert "overflow-x: auto" in quote_scroller
    assert "position: sticky" in desktop_head
    assert "position: static" in quote_head
    assert "position: static" in quote_groups
    assert ".summary-action-layout.quote-list-layout-active .summary-table-region" in mobile
    assert "overflow-x: visible" in mobile


def test_summary_labels_support_current_and_legacy_stock_payloads():
    script = """
      import { finishLabel, lineVariantDisambiguator, subrangeLabel } from "./src/lib/shared.js";
      const sampler = (material, variant) => ({
        material,
        variant,
        offers: [{ original_name: `SAMPLER ${variant} X 10 M` }],
      });
      const labels = [
        subrangeLabel({ material: "PLA", subrange: "Astra", variant: "PLA Astra" }),
        subrangeLabel({ material: "PLA", variant: "PLA Astra" }),
        subrangeLabel({ material: "PLA", variant: null }),
        subrangeLabel({ material: "PETG", variant: "PETG Clear" }),
        finishLabel({ finish: "Glitter" }),
        finishLabel({}),
        lineVariantDisambiguator(sampler("PLA", "PLA Silk")),
        lineVariantDisambiguator(sampler("PLA", "PLA Astra")),
        lineVariantDisambiguator(sampler("PLA", "PLA Wood")),
        lineVariantDisambiguator(sampler("Nylon", "Nylon 6")),
        lineVariantDisambiguator(sampler("Nylon", "Nylon 12")),
        lineVariantDisambiguator({ material: "PLA", variant: "PLA Silk", offers: [] }),
      ];
      process.stdout.write(JSON.stringify(labels));
    """
    result = subprocess.run(
        ["node", "--input-type=module", "--eval", script],
        check=True,
        capture_output=True,
        text=True,
    )

    assert json.loads(result.stdout) == [
        "Astra", "Astra", "Standard", "", "Glitter", "",
        "Silk", "Astra", "Wood", "Nylon 6", "Nylon 12", "",
    ]


def test_summary_sampler_headings_show_collapsed_legacy_variants():
    view = (SRC / "SummaryApp.svelte").read_text(encoding="utf-8")

    assert "lineVariantDisambiguator" in view
    group_title = view[view.index("function groupTitle(product)"):view.index("function groupMaterialSections(groups)")]
    assert "const variantDisambiguator = lineVariantDisambiguator(product);" in group_title
    assert "const compactLine = lineLabel(product);" in group_title
    assert "variantDisambiguator || subrangeLabel(product)" in group_title
    assert "variantDisambiguator ? compactLine" in group_title
    assert "compactLine, variantDisambiguator" in group_title


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
    assert ".summary-material-row" in css
    assert ".summary-material-row h2" in css
    assert ".summary-group-heading h3" in css
    assert ".summary-group-finish" in css
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
