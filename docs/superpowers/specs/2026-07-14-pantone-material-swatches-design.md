# Pantone Material Swatches Design

## Objective

Improve the catalog's color references by using Pantone-derived sRGB approximations when available and by representing the filament's surface finish, not only its flat color.

The public site will display a prerendered material swatch next to the spool photo. The swatch is an orientation aid, not a promise that a user's monitor matches the physical filament. Product photos remain the primary visual reference, and availability and final appearance must still be confirmed with the provider.

## Product Decisions

- Pantone values already published by the manufacturer remain the only Pantone source for a product. The system never invents a missing Pantone.
- Pantone values without a `C` or `U` suffix are interpreted as Solid Coated (`C`) because the current Grilon3 data omits the substrate suffix and the selected free conversion table covers Solid Coated colors.
- Pantone-to-sRGB values are approximate screen representations. They are not licensed Pantone production standards and are not suitable for print matching.
- Surface finish is modeled separately from base color.
- Swatches are prerendered as static WebP assets. No WebGL renderer or Three.js bundle is shipped to the public site.
- A single deterministic camera and lighting setup is used for every swatch so products remain comparable.

## Visual Standard

The standard geometry is a circular cone viewed exactly from above. It is intentionally larger than its square output frame:

- top-down camera with the cone apex centered;
- cone rendered at 150% of the output frame;
- rounded-square mask clips the cone's outer area;
- primary light enters from the upper-left of the image;
- highlights concentrate in the upper-left quadrant;
- shadows fall toward the lower-right quadrant;
- the same camera, geometry, crop, mask and light direction apply to every product;
- only base color and finish parameters vary.

The output is a 160 by 160 RGBA WebP. The rounded-square mask is baked into its alpha channel so the same file scales consistently in the catalog, summary and quote list.

## Pantone Conversion Data

The repository will contain a curated subset of Solid Coated sRGB approximations sourced from the Apache-2.0 `github.com/pborman/colors/pantone` dataset. The data artifact records:

- source URL;
- source version or commit;
- source license;
- color key;
- hexadecimal sRGB approximation.

Only Pantone values present in StockCentral are copied into the repository. The application does not call Pantone Connect, a third-party API or a network service at runtime or build time.

Pantone normalization supports numeric codes and known named entries such as Yellow, Black, Violet, Reflex Blue, Orange 021 and Cool Gray variants. Manufacturer-specific strings are handled only through explicit aliases. For example, `Pantone Piel 162` may alias to `162 C` after review; the parser must not generically discard arbitrary words to guess a code. Values such as `Pantone Perla` remain unresolved unless an explicit reviewed mapping exists.

An unresolved Pantone produces an audit entry and uses the existing name-based CSS swatch fallback.

## Material Finish Model

Each product resolves to one of these finish profiles:

| Finish | Intended appearance |
| --- | --- |
| `matte` | Broad diffuse shading and very soft highlights. |
| `satin` | Default filament appearance with balanced diffuse and specular response. |
| `gloss` | Compact, stronger highlights for polished plastic. |
| `silk` | Strong directional-looking highlight and smooth color transitions. |
| `metallic` | Colored specular response and subtle particulate variation; not modeled as a pure conductor. |
| `pearl` | Soft secondary hue shift in the baked lighting direction. |
| `glitter` | Sparse high-intensity particles over a colored base. |
| `translucent` | Brighter transmitted center and denser-looking edges. |
| `fluorescent` | High saturation and controlled apparent luminance without claiming physical fluorescence on screen. |
| `wood` | High roughness with low-contrast fibrous variation. |

Finish resolution uses this priority:

1. explicit override keyed by `product_id`;
2. known product line or variant rules, including Astra, Silk, Wood, Boutique and Clear;
3. reviewed keywords from normalized color or provider names, including metallic, pearl, transparent and fluorescent terms;
4. `satin` fallback.

The resolver records the selected finish and the rule that selected it. A generated audit report lists explicit, inferred and fallback classifications so incorrect assumptions can be reviewed.

## Rendering Architecture

The renderer is implemented in Python and reuses Pillow, which is already a production dependency. Because the geometry is fixed, it does not require a general-purpose 3D engine.

The renderer computes a deterministic, physically inspired material response for each output pixel:

- convert the base color from sRGB to linear RGB;
- derive the cone surface normal from its projected position;
- apply diffuse lighting for non-metallic color;
- apply roughness-controlled specular highlights;
- apply Fresnel response and finish-specific clearcoat behavior;
- apply finish layers for pearl, glitter, translucency, fluorescence and wood;
- convert the final image back to sRGB;
- apply the rounded-square alpha mask;
- encode WebP with fixed quality and encoder settings.

The implementation is calibrated visually against the approved Three.js exploration. It is a deterministic catalog renderer, not a general photorealistic renderer.

## Data Contract

`ProductGroup` and `public/data/stock.json` gain these fields:

- `pantone_hex`: normalized hexadecimal sRGB approximation or an empty string;
- `material_finish`: resolved finish enum;
- `material_swatch_url`: local generated asset URL or an empty string.

Audit-only resolution details remain in build logs rather than the public product payload.

Generated assets use a stable renderer version in their names, for example:

```text
assets/material-swatches/pantone-179-c-satin-v1.webp
assets/material-swatches/pantone-160-c-metallic-v1.webp
```

The unique asset key is based on normalized Pantone, finish and renderer version. Products sharing the same combination share the same WebP.

## Generation and Publication Flow

1. The normal data build publishes product Pantone and finish fields.
2. The material swatch generator reads `public/data/stock.json`.
3. It resolves the normalized color and generates only missing or stale Pantone-plus-finish assets.
4. It writes `material_swatch_url` only after a valid non-empty WebP exists.
5. It rewrites JSON using the repository's existing stable formatting convention.
6. The existing thumbnail publication workflow commits and publishes material swatches together with other assets and the updated stock payload.

Generation is idempotent. Renderer-version changes deliberately create new asset names. Old assets are not deleted automatically during normal generation; cleanup is a separate reviewed operation.

## Frontend Behavior

### Catalog

- With a spool photo, display the prerendered swatch beside the photo with the Pantone label and finish name.
- Without a spool photo, use the swatch as the primary visual.
- Keep the photo visually dominant when both exist.

### Summary

- Replace the current flat color swatch with the prerendered material swatch.
- Show Pantone and finish as secondary text.

### Quote List

- When a photo exists, show the compact swatch beside or overlapping the photo without covering important spool details.
- Without a photo, use the swatch as the primary thumbnail.

### Accessibility and Motion

- Accessible text combines normalized color, Pantone and finish, for example `Azul, Pantone 286, acabado satinado`.
- Color meaning is never available only through the image.
- Images use lazy loading where they are not immediately visible.
- An optional subtle CSS sheen may appear on hover, but it must be disabled by `prefers-reduced-motion`.
- Image-load failure falls back to the current CSS swatch.

## Failure Handling and Auditability

- Unknown Pantone: record an audit warning and use the existing CSS fallback.
- Missing finish: resolve to `satin` and record fallback provenance.
- Invalid override: fail the generator with an actionable product id and invalid value.
- Render failure: do not write `material_swatch_url`; preserve the existing frontend fallback.
- Empty or corrupt WebP: treat as render failure.
- Partial generation: never publish a URL for an asset that was not successfully written.
- The stock data build remains usable when optional swatches are unavailable.

The UI describes swatches as an orientative representation and continues to tell users to confirm final appearance and availability with the provider.

## Testing

### Unit Tests

- normalize numeric, named and explicitly aliased Pantone strings;
- reject unknown and ambiguous Pantone strings without guessing;
- enforce finish-resolution priority;
- verify stable asset keys and renderer-version behavior;
- verify shared combinations generate one asset;
- verify idempotent repeated generation;
- verify output size, RGBA mask, non-empty WebP and stable JSON updates.

### Visual Invariants

- the upper-left quadrant is brighter than the lower-right under the standard light;
- the cone apex is centered;
- the cone extends beyond the nominal frame before masking;
- rounded corners are transparent;
- matte has a broader, weaker highlight than satin;
- gloss and silk have more concentrated highlights than satin;
- metallic, pearl, glitter, translucent, fluorescent and wood profiles produce measurably distinct outputs.

Tests should prefer numerical invariants and bounded pixel comparisons over whole-file hashes, which can change with Pillow or WebP encoder versions.

### Integration Verification

- run `python -m pytest -v --basetemp C:\tmp\pytest-centraldefilamentos` on Windows;
- generate material swatches twice and confirm the second run makes no changes;
- run `npm run build`;
- inspect representative dark, light, saturated, metallic, translucent and glitter swatches at catalog, summary and quote-list sizes;
- verify the frontend fallback by removing one generated URL in a test fixture;
- verify the publication workflow includes `public/assets/material-swatches/` and the updated `public/data/stock.json`.

## Scope Boundaries

This feature does not:

- provide licensed Pantone production data;
- guarantee physical color matching across monitors;
- infer Pantone values that manufacturers do not publish;
- replace spool photography or physical samples;
- add server-side rendering, sessions or runtime APIs;
- ship Three.js or WebGL code to the public site;
- automatically delete old generated assets.
