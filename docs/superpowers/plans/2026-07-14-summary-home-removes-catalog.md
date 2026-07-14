# Summary Home and Catalog Removal Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Servir `SummaryApp` en la raiz, conservar `/resumen.html` como alias, eliminar la pantalla de Catalogo y mostrar foto de carrete mas render material en cada fila.

**Architecture:** `index.html` y `resumen.html` comparten `src/summary.js`; no hay redireccion ni segundo componente raiz. `SummaryApp` compone dos visuales estaticos desde el contrato existente y conserva fallbacks. Las pruebas dejan de exigir integraciones del Catalogo eliminado, pero mantienen contratos de los modulos de cotizacion que siguen en el repositorio.

**Tech Stack:** Svelte 5, Vite 8, CSS, pytest.

## Global Constraints

- La raiz publica es `/CentraldeFilamentos/`.
- `/resumen.html` debe continuar funcionando como alias.
- Eliminar `src/CatalogApp.svelte` y `src/catalog.js`.
- No eliminar componentes de cotizacion ni su persistencia.
- Preservar cambios locales no relacionados, especialmente `src/lib/quoteList.js`.
- Foto y render miden 28 x 28 px y no deben partirse en mobile.
- Verificar con `python -m pytest -v --basetemp C:\tmp\pytest-centraldefilamentos` y `npm run build`.

---

### Task 1: Replace Catalog Entry Point with Summary

**Files:**
- Modify: `tests/test_frontend_assets.py`
- Modify: `index.html`
- Modify: `vite.config.js`
- Modify: `src/components/SiteHeader.svelte`
- Delete: `src/CatalogApp.svelte`
- Delete: `src/catalog.js`

**Interfaces:**
- Consumes: `src/summary.js`, which mounts `SummaryApp` into `#app`.
- Produces: both `index.html` and `resumen.html` mount the same Summary application.

- [ ] **Step 1: Write the failing route/removal contract**

Replace the static entrypoint assertions with:

```python
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
    assert "SiteHeader" in summary_view
    assert 'type="module" src="/src/vendor-stats.js"' in internal
    assert 'noindex,nofollow' in internal
    assert flags["vendorStatsEnabled"] is True
    for entry in ["summary.js", "vendor-stats.js"]:
        js = (SRC / entry).read_text(encoding="utf-8")
        assert 'import { mount } from "svelte"' in js
        assert "mount(" in js
        assert "new " not in js
```

Delete `test_catalog_svelte_fetches_json_and_supports_required_filters`. In material-swatch and quote-list tests, remove reads/assertions that require `CatalogApp`; retain checks over `SummaryApp`, quote modules and quote components.

- [ ] **Step 2: Run the route test to verify RED**

Run:

```powershell
python -m pytest tests/test_frontend_assets.py::test_static_frontend_files_exist_and_are_linked -v --basetemp C:\tmp\pytest-centraldefilamentos
```

Expected: FAIL because `index.html` still loads `catalog.js` and the Catalog files exist.

- [ ] **Step 3: Switch the root and navigation**

In `index.html`:

```html
<title>Central de Filamentos · Resumen</title>
<meta name="description" content="Tabla compacta de stock de filamentos por proveedor.">
<script type="module" src="/src/summary.js"></script>
```

In `vite.config.js`:

```javascript
input: {
  principal: resolve(__dirname, "index.html"),
  resumen: resolve(__dirname, "resumen.html"),
  estadisticas: resolve(__dirname, "estadisticas.html"),
},
```

In `SiteHeader.svelte`:

```javascript
const navItems = [
  { id: "summary", label: "Resumen", href: "index.html" },
  { id: "providers", label: "Proveedores", href: "index.html#site-footer" },
];
```

Change the brand label to `aria-label="Ir al resumen"`.

- [ ] **Step 4: Delete the obsolete screen and entrypoint**

Delete exactly:

```text
src/CatalogApp.svelte
src/catalog.js
```

Do not delete quote-list modules/components or stock-subscription modules.

- [ ] **Step 5: Run focused frontend tests**

Run:

```powershell
python -m pytest tests/test_frontend_assets.py -v --basetemp C:\tmp\pytest-centraldefilamentos
```

Expected: all frontend asset tests pass after catalog-only expectations are removed.

- [ ] **Step 6: Commit only files without unrelated dirty changes**

```powershell
git add index.html vite.config.js src/components/SiteHeader.svelte src/CatalogApp.svelte src/catalog.js
git diff --cached --check
git commit -m "feat: make summary the primary view"
```

`src/lib/quoteList.js` and `tests/test_frontend_assets.py` must remain unstaged because they already contain unrelated or mixed local work.

### Task 2: Show Spool Photo and Material Render Side by Side

**Files:**
- Modify: `tests/test_frontend_assets.py`
- Modify: `src/SummaryApp.svelte`
- Modify: `src/styles/global.css`

**Interfaces:**
- Consumes: `thumbnail_url`, `image_url`, `material_swatch_url`, `dataUrl()`, `materialSwatchAlt()`, `colorSwatchStyle()`.
- Produces: `.summary-product-visuals`, `.summary-product-photo`, and `.summary-material-swatch` markup/classes.

- [ ] **Step 1: Add a failing summary composition test**

Extend `test_summary_svelte_uses_carretes_totals_and_provider_order`:

```python
assert "summary-product-visuals" in view
assert "summary-product-photo" in view
assert "row.product.thumbnail_url || row.product.image_url" in view
assert "row.product.material_swatch_url" in view
assert "summary-material-swatch" in view
assert "colorSwatchStyle" in view
```

Extend the responsive CSS test:

```python
assert ".summary-product-visuals" in css
assert ".summary-product-photo" in css
assert "width: 28px" in css
assert "height: 28px" in css
```

- [ ] **Step 2: Run the focused tests to verify RED**

Run:

```powershell
python -m pytest tests/test_frontend_assets.py::test_summary_svelte_uses_carretes_totals_and_provider_order tests/test_frontend_assets.py::test_styles_are_compact_and_responsive -v --basetemp C:\tmp\pytest-centraldefilamentos
```

Expected: FAIL because the photo/group classes do not exist.

- [ ] **Step 3: Implement the two-image group**

Replace the current single swatch block inside `.summary-product` with:

```svelte
<span class="summary-product-visuals">
  {#if row.product.thumbnail_url || row.product.image_url}
    <img
      class="summary-product-photo"
      src={dataUrl(row.product.thumbnail_url || row.product.image_url)}
      alt=""
      loading="lazy"
      decoding="async"
    >
  {/if}
  {#if row.product.material_swatch_url}
    <img
      class="summary-color-swatch summary-material-swatch"
      src={dataUrl(row.product.material_swatch_url)}
      alt={materialSwatchAlt(row.product)}
      loading="lazy"
      decoding="async"
    >
  {:else}
    <span
      class="summary-color-swatch"
      style={colorSwatchStyle(row.product)}
      title={[row.product.color || "Sin color", row.product.pantone].filter(Boolean).join(" · ")}
      aria-label={[row.product.color || "Sin color", row.product.pantone].filter(Boolean).join(" · ")}
    ></span>
  {/if}
</span>
```

- [ ] **Step 4: Add compact responsive styles**

```css
.summary-product-visuals {
  display: inline-flex;
  flex: 0 0 auto;
  align-items: center;
  gap: 4px;
  white-space: nowrap;
}

.summary-product-photo,
.summary-color-swatch {
  width: 28px;
  height: 28px;
  border: 1px solid color-mix(in srgb, var(--line) 82%, black);
  border-radius: 6px;
}

.summary-product-photo {
  display: block;
  object-fit: cover;
  background: var(--surface-soft);
}
```

Keep `.summary-material-swatch { object-fit: cover; }`.

- [ ] **Step 5: Verify focused tests and build**

```powershell
python -m pytest tests/test_frontend_assets.py -v --basetemp C:\tmp\pytest-centraldefilamentos
npm run build
```

Expected: frontend tests pass; Vite outputs `index.html`, `resumen.html`, and `estadisticas.html`.

- [ ] **Step 6: Preserve mixed local changes**

`SummaryApp.svelte`, `global.css`, and `tests/test_frontend_assets.py` already contain uncommitted material-swatch work. Do not stage or commit them unless the user explicitly authorizes consolidating that local slice. Leave them working and verified.

### Task 3: Final Verification

**Files:**
- Verify only; no new production files.

- [ ] **Step 1: Search for obsolete runtime references**

```powershell
rg -n "CatalogApp|src/catalog.js|label: \"Catálogo\"" index.html resumen.html src vite.config.js tests
```

Expected: no runtime or test reference.

- [ ] **Step 2: Run full verification**

```powershell
python -m pytest -v --basetemp C:\tmp\pytest-centraldefilamentos
npm run build
git diff --check
git status --short
```

Expected: all tests pass; build succeeds; only intended mixed UI changes and pre-existing unrelated untracked files remain.
