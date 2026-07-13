# Grilon3 Master Data and Actionable Summary Design

**Date:** 2026-07-13
**Status:** Approved design

## Summary

Central de Filamentos will make the compact Summary view the default product experience and move the complete quote-planning and stock-watch workflow into it. The previous Catalog view will remain temporarily available at `catalogo.html`, outside the primary navigation.

In parallel, Grilon3 enrichment will become a complete, auditable master-data process. It will crawl every active product page, capture official SKU, EAN and Pantone values when published, preserve the official product taxonomy, and use only human-reviewed official images. The preferred image is the spool at approximately 45 degrees without its box; if that image does not exist, the reviewer chooses the best official spool-only image and then the official primary image as the final fallback.

## Product Decisions

- `index.html` becomes the Summary experience.
- `resumen.html` redirects to the root while preserving query parameters and fragments.
- The former Catalog remains at `catalogo.html` during a temporary compatibility period and is removed from primary navigation.
- Summary uses the approved "actionable table" layout: product thumbnail and metadata in the product row, `+1` at row level, and a provider-specific stock-watch bell inside each provider cell.
- All current quote and watch behavior moves to Summary: alerts, quantities, local persistence, import/export, provider coverage and WhatsApp message generation.
- Existing `localStorage` keys, schema versions and product IDs remain stable.
- PLA is organized by commercial subrange. Branded lines remain distinct; generic finishes are descriptive metadata and never merge products from different commercial lines.
- All active official Grilon3 pages are scanned, including products that are not currently offered by a tracked provider.
- Missing official fields remain empty and appear in an audit report. No SKU, EAN, Pantone or product property is inferred.

## Grilon3 Catalog Discovery

The active catalog is defined by the paginated `/productos/` listing, not by a blind union with the product sitemap.

1. Read the first products page and discover every pagination URL.
2. Parse all listing pages and deduplicate products by canonical product URL.
3. Fetch every active detail page.
4. Parse the sitemap separately as an audit source.
5. Classify sitemap-only URLs as `historical`, `hidden` or `duplicate`; do not add them to the active master catalog automatically.

The scan must reconcile the official listing count with the number of canonical active URLs. A count mismatch or an unclassified sitemap-only URL is reported and prevents the scan from being considered complete, but it does not modify the last approved metadata cache.

## Detail Extraction Contract

Each active product detail produces a draft record with:

- canonical official product URL;
- official title and category breadcrumb;
- gallery image URLs in source DOM order, using the original or largest available asset;
- SKU from WooCommerce `.sku`, with structured-data and visible-text fallbacks;
- EAN from WooCommerce `.ean`, `gtin` structured data, then visible-text fallback;
- Pantone from the product summary or description, normalized to the existing `Pantone ...` display format;
- normalized material, variant, color, diameter, weight, brand and stable product ID;
- extraction warnings and source-field provenance.

The parser keeps gallery order. It does not rank candidates before presenting them for review. Repeated responsive sizes of the same original image are deduplicated.

The scan writes a draft under ignored `.image-curation/` state. It never replaces the versioned cache or production assets directly.

## Image Review and Persistence

The existing local image curator remains the human review surface but changes in four ways:

1. It loads all active Grilon3 master records from the draft scan, not only products present in `stock.json`.
2. It displays the current production image and every official gallery image in DOM order.
3. It records one of three explicit reasons: `preferred_angle`, `best_spool` or `official_primary`.
4. It flags products whose gallery fingerprint changed after their last review.

Scratch review decisions remain in `.image-curation/`. Approved durable decisions are exported to the versioned file `centraldefilamentos/data/grilon3_image_selections.json`, keyed by canonical product URL. Each value has this shape:

```json
{
  "selected_image_remote_url": "https://grilon3.com.ar/wp-content/uploads/...jpg",
  "selection_reason": "preferred_angle",
  "reviewed_at": "2026-07-13T00:00:00Z",
  "gallery_fingerprint": "sha256:..."
}
```

An explicit apply command reads the draft scan and scratch review file. Its default mode is a dry run. With `--apply`, it:

- validates that every selected image belongs to the corresponding official gallery;
- writes the versioned selection manifest;
- updates official SKU, EAN, Pantone and product URLs in `grilon3_metadata.json`;
- downloads only newly approved or changed official images;
- regenerates only affected thumbnails;
- emits a complete coverage and change report.

The apply command refuses image changes for unreviewed products. Existing reviewed images remain active if a later scan changes the gallery; the product is marked stale for review, but production is not silently changed. Daily stock capture continues to read local versioned metadata and never crawls Grilon3 detail pages.

Whenever an approved official Grilon3 image exists, it takes precedence over provider imagery. Samplers and 3D-pen products retain their existing no-spool-image exception unless an exact matching official product page is reviewed.

## Metadata and Audit Outputs

`centraldefilamentos/data/grilon3_metadata.json` remains the versioned canonical enrichment cache consumed by stock builds. It contains only official published values and the selected local image path plus remote source URL.

The scan/apply report records:

- active listing count and canonical URL count;
- detail pages attempted, succeeded and failed;
- counts and URLs missing SKU, EAN, Pantone or gallery images;
- sitemap-only and duplicate URLs with classification;
- reviewed, stale and pending image selections;
- files downloaded and metadata fields changed.

Missing data is expected when the official page omits it. Completeness means every active page was attempted and every published field was captured, not that every field is non-empty.

## PLA Subrange Model

Two additive strings are added to normalized and public products:

- `subrange`: commercial subrange label;
- `finish`: short user-facing finish descriptor.

Existing `variant` values and `build_product_id()` inputs do not change. This preserves product IDs and all stored quote/watch references.

Initial PLA mappings are:

| Existing variant | `subrange` | `finish` |
| --- | --- | --- |
| empty PLA variant | `Standard` | empty |
| `PLA Astra` | `Astra` | `Glitter` |
| `PLA Silk` | `Silk` | `Brillo metálico` |
| `PLA Wood` | `Wood` | `Madera` |
| `PLA Boutique` | `Boutique` | empty |
| `PLA 850` | `PLA 850` | empty |
| `PLA 870` | `PLA 870` | empty |
| `PLA Zeta` | `Zeta` | empty |
| other PLA variant | existing variant label | empty unless explicitly mapped |

Non-PLA products receive empty `subrange` and `finish` values unless a future explicit mapping is added. The UI must not derive or guess finishes from color names.

Summary displays a visible hierarchy of material, commercial subrange, then products. Group identity still includes brand, diameter and existing variant so that separate brands or presentations are not collapsed into one product.

## Shared Interaction Architecture

Quote-list and stock-watch orchestration currently embedded in `CatalogApp.svelte` moves into two shared instance-based controllers backed by Svelte writable stores:

- a quote workspace controller that initializes, reconciles and saves the existing quote schema and exposes add, quantity, remove, clear, import and export actions;
- a stock-watch controller that loads and reconciles existing product-provider subscriptions, exposes toggle/dismiss actions and produces alert state.

Both Summary and the legacy Catalog instantiate these controllers after `stock.json` loads. Existing pure helpers and quote UI components remain the contract source. The controllers do not introduce new storage keys or schema versions.

Summary receives controller state and renders:

- a thumbnail and official metadata in each product row;
- one `+1` action per product/presentation row;
- one bell per product-provider cell, preserving current product-provider semantics;
- the stock alert banner through `SiteHeader`;
- the existing side panel at desktop widths and drawer/floating trigger on mobile;
- import/export, provider comparison and WhatsApp preparation through the existing quote components.

Rows with no offer for a provider show no actionable bell for that provider. Unknown stock remains visually distinct from confirmed zero stock. Adding to a quote never assigns a provider; provider coverage is calculated later from the complete list as it is today.

## Routes and Navigation

- Root `index.html` mounts `SummaryApp` and uses Summary metadata/title.
- `catalogo.html` mounts `CatalogApp` and is included as a Vite build entry.
- `resumen.html` performs a same-origin replacement to the root, preserving search and hash.
- Primary navigation contains `Resumen` and `Proveedores`; the deprecated Catalog is not a primary tab.
- A secondary "Catálogo anterior" link remains available in the footer during the compatibility period.
- Brand links and provider anchors point to the new root.

No removal date or automatic redirect is assigned to `catalogo.html` in this change.

## Failure Behavior

- A failed Grilon3 scan leaves the last approved metadata and images untouched.
- Partial field extraction is included in the draft and audit but does not fabricate values.
- A selected image missing from the current gallery blocks that image change and marks the record stale.
- Image download or thumbnail failure leaves the previous approved local image in place and reports the failure.
- A failed `stock.json` load preserves the local quote list without reconciliation or writes, matching the current resilience contract.
- Unsupported future quote schemas remain read-only and are not overwritten.
- `localStorage` failures keep the in-session workflow usable and display the existing warning.

## Implementation Sequence and Release Gates

The work is delivered as ordered milestones rather than one production cutover:

1. **Safe master scan:** implement paginated discovery, detail extraction and audit output to ignored draft state. Gate: the active catalog reconciles and no approved cache or asset changes.
2. **Official image curation:** extend the curator, add the durable selection manifest and implement dry-run/selective apply. Gate: every active product with an official gallery has an explicit durable image decision before the initial master refresh.
3. **Additive PLA taxonomy:** add `subrange` and `finish`, regenerate data and prove representative product IDs are unchanged. Gate: normalization and generated-data tests pass.
4. **Summary feature migration:** introduce shared controllers and add the actionable-table interactions without changing routes. Gate: functional parity passes on the existing `resumen.html` entry.
5. **Route cutover:** make Summary the root, move Catalog to `catalogo.html`, add the compatibility redirect and update navigation. Gate: desktop/mobile acceptance and the complete verification suite pass.

No milestone may publish partial generated data from a failed later milestone. The root-route cutover is the final step.

## Testing and Acceptance Criteria

### Grilon3 pipeline

- Parser fixtures cover multipage discovery, canonical URL deduplication, ordered galleries, responsive image deduplication, WooCommerce and fallback SKU/EAN extraction, Pantone extraction and absent fields.
- Tests cover active-listing versus sitemap-only classification and count mismatches.
- Image-selection tests cover each selection reason, changed gallery fingerprints, invalid external image URLs, dry-run behavior and selective apply behavior.
- Generated-data tests assert that approved official Grilon3 images take precedence and that 1 kg products never inherit Maxicarrete or Megafill metadata.
- A live audit run must report every active product URL as attempted before the initial master refresh is accepted.

### Taxonomy

- Normalization tests cover every initial PLA mapping.
- Existing product IDs remain byte-for-byte stable for representative Standard, Astra, Silk, Wood, Boutique, 850, 870 and Zeta products.
- Public products serialize `subrange` and `finish` without changing existing fields.

### Summary migration

- Source tests verify root/legacy route ownership and navigation.
- Node tests cover shared quote and watch controller behavior with existing storage payloads.
- UI contract tests cover row-level `+1`, provider-cell bells, alerts, import/export, coverage and WhatsApp actions in Summary.
- Desktop acceptance verifies the table plus side-panel layout.
- Mobile acceptance verifies readable stock cells, tap targets, the quote drawer and no horizontal action overlap.
- Accessibility checks cover button labels, pressed states, focus restoration and alert announcements.

### Verification commands

```powershell
python -m pytest -v --basetemp C:\tmp\pytest-centraldefilamentos
npm run test:quote-list
npm run build
```

The implementation is complete only when all commands pass, the active Grilon3 audit has no unclassified URLs, every active official product with a gallery has a durable review decision, and the legacy localStorage payloads work from the new root experience.
